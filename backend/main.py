# backend/main.py - COMPLETE FINAL VERSION FOR PHASE 1
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import os, json, httpx, asyncio
from dotenv import load_dotenv

load_dotenv()

from services.text_extractor import extract_text
from services.llm_enrichment import enrich_document
from services.embedding import generate_embedding
from services.pgvector_client import (
    setup_tables,
    insert_embedding,
    get_asset_by_token_id,
    DuplicateUploadError,
)
from services.quantum_hash import quantum_hash
from services.quantum_search import quantum_enhanced_search
from services.fraud_detector import fraud_detector

from services.blockchain import (
    has_purchased,
    get_purchase_count,
    get_knowledge_asset,
)
from services.payments.models import CreatePaymentRequest, ConfirmPaymentRequest
from services.payments.service import payment_service
from services.auth import router as auth_router, setup_auth, current_user, wallet_user, ORIGIN
from services.pgvector_client import get_conn
from services.reviews import router as reviews_router
from services.content_security import seal, unseal, master_key
from services.payments.transak import router as transak_router, setup_transak
from services.payments.quotes import router as quotes_router, setup_quotes
from services.research_results import router as research_router




app = FastAPI(title="DKM API", version="1.0.0")
app.include_router(auth_router)
app.include_router(reviews_router)
app.include_router(transak_router)
app.include_router(quotes_router)
app.include_router(research_router)


@app.exception_handler(DuplicateUploadError)
async def duplicate_upload(request, exc):
    return JSONResponse(status_code=409, content={"detail": "This file has already been uploaded. Check your dashboard to continue an existing upload."})


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Never echo submitted passwords, signatures or uploaded metadata in errors.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "msg": error["msg"]} for error in exc.errors()
    ]})


@app.middleware("http")
async def private_response_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/api/auth", "/api/account", "/api/payments", "/api/purchase-quotes", "/api/research", "/api/assets")):
        response.headers["Cache-Control"] = "no-store"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.on_event("startup")
async def startup():
    await setup_tables()
    await setup_auth()
    await setup_transak()
    await setup_quotes()
    if os.getenv("TRANSAK_RECONCILIATION_ENABLED", "true") == "true":
        from services.payments.transak import configuration, reconciliation_worker
        try:
            configuration()
        except ValueError:
            pass
        else:
            app.state.transak_task = asyncio.create_task(reconciliation_worker())
    if os.getenv("SETTLEMENT_ENABLED") == "true":
        from services.payments.settlement import settlement_worker
        app.state.settlement_task = asyncio.create_task(settlement_worker())
    print("DKM API started - pgvector tables ready")


@app.on_event("shutdown")
async def shutdown():
    for name in ("settlement_task", "transak_task"):
        task = getattr(app.state, name, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


@app.get("/")
async def root():
    return {"message": "DKM API running", "stack": "100% free"}


@app.get("/health")
async def health():
    checks = {}
    try:
        r = httpx.get(
            "http://localhost:11434/api/tags",
            timeout=3.0
        )

        models = [
            m["name"]
            for m in r.json().get("models", [])
        ]

        checks["ollama_running"] = True
        checks["llama3_2_ready"] = any(
            "llama3.2" in m for m in models
        )
        checks["llama3_2_3b_ready"] = any(
            "llama3.2:3b" in m for m in models
        )
    except Exception as e:
        checks["ollama_running"] = False
        checks["ollama_error"] = "Ollama is unavailable"

    checks["pinata"] = bool(
        os.environ.get("PINATA_JWT")
    )

    checks["blockchain"] = bool(
        os.environ.get("BLOCKCHAIN_RPC_URL")
    )

    checks["blockchain_chain_id"] = (
        os.environ.get("BLOCKCHAIN_CHAIN_ID") == "80002"
    )

    checks["database_url"] = bool(
        os.environ.get("DATABASE_URL")
    )
    try:
        master_key()
        checks["protected_storage_key"] = True
    except ValueError:
        checks["protected_storage_key"] = False

    all_ok = all(
        v for k, v in checks.items()
        if not k.endswith("_error")
    )

    return {
        "status": "ok" if all_ok else "degraded",
        "checks": checks
    }

@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...), user=Depends(current_user)):
    data = await read_upload(file)
    if len(data) < 100:
        raise HTTPException(422, "File too small or empty")

    text = extract_text(data, file.filename)
    if len(text.strip()) < 50:
        raise HTTPException(422, "Could not extract readable text from file")

    metadata = await enrich_document(text)
    if metadata["quality_score"] < 0.4:
        raise HTTPException(
            422,
            f"Quality score {metadata['quality_score']:.2f} below threshold 0.4. "
            "Improve document content before uploading.",
        )

    return {"success": True, "metadata": metadata, "file_size": len(data)}

@app.post("/api/upload-ipfs")
async def upload_ipfs(
    file: UploadFile = File(...),
    metadata_json: str = Form("{}"),
    user=Depends(wallet_user),
):
    data = await read_upload(file)
    try:
        meta = json.loads(metadata_json)
        if not isinstance(meta, dict) or not isinstance(meta.get("title"), str) or not meta["title"].strip():
            raise ValueError()
        price = meta.get("recommended_price_usdc")
        quality = meta.get("quality_score")
        if type(price) is not int or not 1 <= price <= 100 or type(quality) not in (int, float) or not 0.4 <= quality <= 1:
            raise ValueError()
        if not isinstance(meta.get("summary"), str) or len(meta["summary"]) > 20000:
            raise ValueError()
        if not isinstance(meta.get("domain"), str) or not isinstance(meta.get("tags"), list) or any(not isinstance(t, str) for t in meta["tags"]):
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(422, "Supply valid analyzed metadata, quality 0.4–1 and a whole USDC price from 1–100") from None

    # ---------------------------------------------------------
    # Generate embedding
    # ---------------------------------------------------------

    embedding = generate_embedding(
        meta.get("summary", "")
    )

    # ---------------------------------------------------------
    # Fraud detection
    # ---------------------------------------------------------

    fraud = await fraud_detector.check_upload(
        data,
        embedding
    )

    if fraud["is_fraud"]:
        raise HTTPException(
            422,
            f"Upload rejected: {fraud['reason']}"
        )

    content_hash = quantum_hash(data)
    try:
        protected_data, encrypted_key = seal(data, content_hash)
    except ValueError:
        raise HTTPException(503, "Protected storage needs configuration before uploading") from None

    # ---------------------------------------------------------
    # Upload FILE to Pinata
    # ---------------------------------------------------------

    pinata_jwt = os.environ.get("PINATA_JWT")

    if not pinata_jwt:
        raise HTTPException(
            500,
            "PINATA_JWT is not configured"
        )

    async with httpx.AsyncClient(timeout=120) as client:

        files = {
            "file": (
                "knowledge-asset.enc",
                protected_data,
                "application/octet-stream",
            )
        }

        form_data = {
            "network": "public"
        }

        r = await client.post(
            "https://uploads.pinata.cloud/v3/files",
            headers={
                "Authorization": f"Bearer {pinata_jwt}",
            },
            files=files,
            data=form_data,
        )

        r.raise_for_status()

        pinata_response = r.json()


        file_cid = pinata_response["data"]["cid"]

    # ---------------------------------------------------------
    # Add file CID + BLAKE3 hash to metadata
    # ---------------------------------------------------------

    meta["file_cid"] = file_cid

    meta["blake3_hash"] = quantum_hash(data)
    meta["storage"] = "encrypted-v1"

    meta_bytes = json.dumps(meta).encode()

    # ---------------------------------------------------------
    # Upload METADATA JSON to Pinata
    # ---------------------------------------------------------

    async with httpx.AsyncClient(timeout=60) as client:

        metadata_files = {
            "file": (
                "metadata.json",
                meta_bytes,
                "application/json",
            )
        }

        metadata_form_data = {
            "network": "public"
        }

        r = await client.post(
            "https://uploads.pinata.cloud/v3/files",
            headers={
                "Authorization": f"Bearer {pinata_jwt}",
            },
            files=metadata_files,
            data=metadata_form_data,
        )

        r.raise_for_status()

        metadata_response = r.json()


        metadata_cid = metadata_response["data"]["cid"]

    # ---------------------------------------------------------
    # Generate vector ID
    # ---------------------------------------------------------


    # ---------------------------------------------------------
    # Save to PostgreSQL + pgvector
    # ---------------------------------------------------------

    stored = await insert_embedding(
    title=meta.get("title", ""),
    domain=meta.get("domain", "other"),
    tags=meta.get("tags", []),
    quality=meta.get("quality_score", 0.5),
    price_usdc=meta.get("recommended_price_usdc", 5),
    blake3_hash=meta["blake3_hash"],
    embedding=embedding,
    file_cid=file_cid,
    metadata_cid=metadata_cid,
    user_id=user["id"],
    summary=meta.get("summary", ""),
    encrypted_key=encrypted_key,
    original_filename=(file.filename or "knowledge-asset.bin").replace("\\", "/").rsplit("/", 1)[-1][:200],
)

    # ---------------------------------------------------------
    # Return existing API response format
    # ---------------------------------------------------------

    return {
        "file_cid": file_cid,
        "metadata_cid": metadata_cid,
        "vector_id": stored["vector_id"],
    }


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    domain: str | None = Field(default=None, max_length=100)
    max_price: int | None = Field(default=None, ge=0, le=1000000)
    min_quality: float = Field(default=0.4, ge=0.4, le=1)


async def read_upload(file):
    data = await file.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "Files must be 20 MB or smaller")
    if len(data) < 100:
        raise HTTPException(422, "File too small or empty")
    return data


@app.post("/api/search")
async def search(body: SearchRequest):
    if not body.query.strip():
        raise HTTPException(400, "Enter a search query")
    results = await quantum_enhanced_search(body.query.strip(), domain=body.domain, max_price=body.max_price, min_quality=body.min_quality)
    return {"query": body.query, "results": results, "count": len(results)}


@app.get("/api/assets/{token_id}/access")
async def check_asset_access(token_id: int, user=Depends(wallet_user)):
    if token_id <= 0:
        raise HTTPException(400, "Invalid token ID")
    try:
        onchain = await asyncio.to_thread(get_knowledge_asset, token_id)
        purchased = await asyncio.to_thread(has_purchased, token_id, user["wallet_address"])
        count = await asyncio.to_thread(get_purchase_count, token_id, user["wallet_address"])
    except Exception:
        raise HTTPException(503, "Could not verify this asset on-chain. Retry shortly.") from None
    creator = onchain["creator"].lower() == user["wallet_address"].lower()
    granted = bool(onchain["active"] and (purchased or creator))
    conn = await get_conn()
    try:
        protected = bool(await conn.fetchval("SELECT encrypted_key IS NOT NULL FROM knowledge_assets WHERE file_cid=$1 AND metadata_cid=$2 ORDER BY created_at DESC LIMIT 1", onchain["ipfs_cid"], onchain["metadata_cid"]))
    finally:
        await conn.close()
    return {"token_id": token_id, "wallet_address": user["wallet_address"],
            "has_purchased": purchased, "purchase_count": count, "access_granted": granted,
            "file_url": "https://ipfs.io/ipfs/" + onchain["ipfs_cid"] if granted and not protected else None,
            "download_path": f"/api/assets/{token_id}/download" if granted and protected else None,
            "storage_notice": "Encrypted file; downloading requires an active on-chain entitlement or creator access." if protected else "Legacy public file: anyone with its IPFS address can retrieve it."}


@app.get("/api/assets/{token_id}/download")
async def download_asset(token_id: int, user=Depends(wallet_user)):
    import re
    from urllib.parse import quote
    from cryptography.exceptions import InvalidTag
    access = await check_asset_access(token_id, user)
    if not access["access_granted"]:
        raise HTTPException(403, "Purchase this asset before downloading")
    if not access["download_path"]:
        raise HTTPException(409, "This legacy asset uses its public file link")
    try:
        asset = await asyncio.to_thread(get_knowledge_asset, token_id)
    except Exception:
        raise HTTPException(503, "Could not verify asset content") from None
    conn = await get_conn()
    try:
        row = await conn.fetchrow("SELECT encrypted_key,blake3_hash,original_filename FROM knowledge_assets WHERE file_cid=$1 AND metadata_cid=$2 AND encrypted_key IS NOT NULL ORDER BY created_at DESC LIMIT 1", asset["ipfs_cid"], asset["metadata_cid"])
    finally:
        await conn.close()
    if not row or not re.fullmatch(r"[A-Za-z0-9]{20,100}", asset["ipfs_cid"]):
        raise HTTPException(503, "Protected file is unavailable")
    async with httpx.AsyncClient(timeout=30) as client:
        for gateway in ("https://ipfs.io/ipfs/", "https://gateway.pinata.cloud/ipfs/"):
            try:
                async with client.stream("GET", gateway + asset["ipfs_cid"]) as response:
                    response.raise_for_status()
                    ciphertext = bytearray()
                    async for chunk in response.aiter_bytes():
                        ciphertext.extend(chunk)
                        if len(ciphertext) > 20 * 1024 * 1024 + 28:
                            raise ValueError("File too large")
                data = unseal(bytes(ciphertext), row["encrypted_key"], row["blake3_hash"])
                if quantum_hash(data) != row["blake3_hash"]:
                    raise ValueError("Integrity mismatch")
                filename = quote(row["original_filename"] or f"knowledge-asset-{token_id}.bin", safe="")
                return Response(data, media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
            except (httpx.HTTPError, ValueError, InvalidTag):
                continue
    raise HTTPException(503, "Could not retrieve and verify this file. Retry shortly.")


def asset_description(metadata):
    # Explicit public catalog fields, never a dump of file IDs, hashes or JSON.
    title = metadata.get("title")
    summary = metadata.get("summary") or metadata.get("description")
    domain = metadata.get("domain")
    return {
        "title": title[:200] if isinstance(title, str) and title.strip() else "Knowledge asset",
        "summary": summary[:5000] if isinstance(summary, str) and summary.strip() else "The creator has not provided a description yet.",
        "domain": domain[:100] if isinstance(domain, str) else "other",
        "tags": [tag[:80] for tag in metadata.get("tags", []) if isinstance(tag, str)][:12]
            if isinstance(metadata.get("tags"), list) else [],
    }


@app.get("/api/assets/{token_id}/details")
async def asset_details(token_id: int):
    import re
    if token_id <= 0:
        raise HTTPException(400, "Invalid asset")
    try:
        asset = await asyncio.to_thread(get_knowledge_asset, token_id)
    except Exception:
        raise HTTPException(503, "Asset information is temporarily unavailable") from None
    cid = asset["metadata_cid"]
    conn = await get_conn()
    try:
        row = await conn.fetchrow("SELECT title,summary,domain,tags FROM knowledge_assets WHERE metadata_cid=$1 ORDER BY created_at DESC LIMIT 1", cid)
    finally:
        await conn.close()
    if row and row["title"] and row["summary"]:
        return asset_description(dict(row))
    if re.fullmatch(r"[A-Za-z0-9]{20,100}", cid):
        async with httpx.AsyncClient(timeout=8) as client:
            for gateway in ("https://ipfs.io/ipfs/", "https://gateway.pinata.cloud/ipfs/"):
                try:
                    async with client.stream("GET", gateway + cid) as response:
                        response.raise_for_status()
                        content = bytearray()
                        async for chunk in response.aiter_bytes():
                            content.extend(chunk)
                            if len(content) > 256000:
                                raise ValueError("Metadata too large")
                    metadata = json.loads(content)
                    if isinstance(metadata, dict):
                        return asset_description(metadata)
                except (httpx.HTTPError, ValueError, TypeError):
                    continue
    if row:
        return asset_description({**dict(row), "summary": row["summary"] or "Description is currently unavailable."})
    raise HTTPException(503, "The creator's description is temporarily unavailable. Please retry.")


class LinkTokenRequest(BaseModel):
    token_id: int = Field(gt=0)


@app.post("/api/assets/{vector_id}/link-token")
async def link_token(vector_id: str, body: LinkTokenRequest, user=Depends(wallet_user)):
    conn = await get_conn()
    try:
        async with conn.transaction():
            row = await conn.fetchrow("SELECT * FROM knowledge_assets WHERE vector_id=$1 AND user_id=$2 FOR UPDATE", vector_id, user["id"])
            if not row:
                raise HTTPException(404, "Upload not found in your account")
            if row["token_id"] and row["token_id"] != body.token_id:
                raise HTTPException(409, "Upload is already linked to a different token")
            try:
                asset = await asyncio.to_thread(get_knowledge_asset, body.token_id)
            except Exception:
                raise HTTPException(503, "Could not verify the minted token. Retry shortly.") from None
            if (asset["creator"].lower() != user["wallet_address"].lower()
                    or asset["ipfs_cid"] != row["file_cid"] or asset["metadata_cid"] != row["metadata_cid"]):
                raise HTTPException(403, "Token creator and content must match your verified wallet and upload")
            if asset["price_usdc"] != row["price_usdc"] * 1000000:
                raise HTTPException(409, "Minted price must match the uploaded price")
            await conn.execute("UPDATE knowledge_assets SET token_id=$2 WHERE vector_id=$1", vector_id, body.token_id)
        return {"success": True, "vector_id": vector_id, "token_id": body.token_id}
    finally:
        await conn.close()


@app.get("/api/account/dashboard")
async def dashboard(user=Depends(current_user)):
    conn = await get_conn()
    try:
        assets = await conn.fetch("SELECT vector_id,title,token_id,file_cid,metadata_cid,price_usdc,quality,created_at FROM knowledge_assets WHERE user_id=$1 ORDER BY created_at DESC LIMIT 100", user["id"])
        rows = await conn.fetch("SELECT * FROM payment_orders WHERE user_id=$1 ORDER BY created_at DESC LIMIT 100", user["id"])
        from services.payments.models import PaymentOrder
        return {"assets": [dict(a) for a in assets], "orders": [PaymentOrder.model_validate(dict(r)).model_dump() for r in rows]}
    finally:
        await conn.close()


@app.get("/api/capabilities")
async def capabilities(response: Response):
    from services.payments.capabilities import payment_capabilities
    response.headers["Cache-Control"] = "no-store"
    return await asyncio.to_thread(payment_capabilities)


@app.get("/api/assets/{token_id}/payment")
async def latest_payment(token_id: int, user=Depends(current_user)):
    conn = await get_conn()
    try:
        row = await conn.fetchrow("SELECT * FROM payment_orders WHERE user_id=$1 AND token_id=$2 AND payment_method IN ('upi','card') ORDER BY created_at DESC LIMIT 1", user["id"], token_id)
        from services.payments.models import PaymentOrder
        return {"order": PaymentOrder.model_validate(dict(row)).model_dump() if row else None}
    finally:
        await conn.close()


@app.get("/api/account/activity")
async def activity(before_block: int | None = None, user=Depends(wallet_user)):
    if before_block is not None and before_block < 0:
        raise HTTPException(400, "Invalid block number")
    from services.activity import account_activity
    try:
        result = await asyncio.to_thread(account_activity, user["wallet_address"], before_block)
    except Exception:
        raise HTTPException(503, "Blockchain history is unavailable. Retry or choose an earlier block.") from None
    conn = await get_conn()
    try:
        for item in result["activity"]:
            method = await conn.fetchval("SELECT payment_method FROM payment_orders WHERE lower(settlement_tx_hash)=$1", item["transaction_hash"].lower())
            item["payment_route"] = method if method in ("upi", "card") else "on-chain"
    finally:
        await conn.close()
    return result


async def require_order_owner(order_id, user):
    conn = await get_conn()
    try:
        found = await conn.fetchval("SELECT 1 FROM payment_orders WHERE order_id=$1 AND user_id=$2", order_id, user["id"])
    finally:
        await conn.close()
    if not found:
        raise HTTPException(404, "Payment order not found in your account")


# =========================================================
# PAYMENT API
# =========================================================

@app.post("/api/payments/webhook/razorpay")
async def razorpay_webhook(request: Request):
    import hashlib
    import hmac
    from services.pgvector_client import get_conn
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(503, "Payment webhooks are not configured")
    body = await request.body()
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected.encode(), request.headers.get("x-razorpay-signature", "").encode()):
        raise HTTPException(400, "Invalid webhook signature")
    try:
        payload = json.loads(body)
        if payload.get("event") != "payment.captured":
            return {"received": True}
        payment = payload["payload"]["payment"]["entity"]
        provider_order_id, payment_id = payment["order_id"], payment["id"]
    except (ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(400, "Malformed webhook") from None
    conn = await get_conn()
    try:
        order_id = await conn.fetchval("SELECT order_id FROM payment_orders WHERE provider_order_id=$1", provider_order_id)
    finally:
        await conn.close()
    if not order_id:
        raise HTTPException(404, "Payment order not found")
    # The raw-body webhook signature authenticates this callback. Reuse the
    # checkout verifier, which also fetches and checks captured amount/currency.
    signature = hmac.new(os.environ["RAZORPAY_KEY_SECRET"].encode(), f"{provider_order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
    try:
        order = await payment_service.confirm_order(order_id, {
            "razorpay_order_id": provider_order_id, "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"received": True, "status": order.status}

@app.post("/api/payments/{order_id}/settle")
async def settle_payment(order_id: str, user=Depends(wallet_user)):
    await require_order_owner(order_id, user)
    from services.payments.settlement import settle_order
    try:
        order = await settle_order(order_id)
        return {"success": True, "order": order.model_dump()}
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

@app.post("/api/payments/create")
async def create_payment(
    request: CreatePaymentRequest, user=Depends(wallet_user),
):
    if request.buyer_address.lower() != user["wallet_address"].lower():
        raise HTTPException(403, "Buyer must be your verified wallet")
    try:
        order = await payment_service.create_order(
            request, user_id=user["id"]
        )

        return {
            "success": True,
            "order": order.model_dump(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@app.get("/api/payments/{order_id}")
async def get_payment(
    order_id: str, user=Depends(current_user),
):
    await require_order_owner(order_id, user)
    order = await payment_service.get_order(order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Payment order not found"
        )

    return {
        "success": True,
        "order": order.model_dump(),
    }


@app.post("/api/payments/{order_id}/confirm")
async def confirm_payment(
    order_id: str,
    confirmation: ConfirmPaymentRequest | None = None,
    user=Depends(wallet_user),
):
    await require_order_owner(order_id, user)
    try:
        order = await payment_service.confirm_order(
            order_id,
            confirmation.model_dump() if confirmation else None,
        )

        return {
            "success": True,
            "order": order.model_dump(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
