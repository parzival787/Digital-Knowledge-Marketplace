# backend/main.py - COMPLETE FINAL VERSION FOR PHASE 1
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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




app = FastAPI(title="DKM API", version="1.0.0")
app.include_router(auth_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Never echo submitted passwords, signatures or uploaded metadata in errors.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "msg": error["msg"]} for error in exc.errors()
    ]})


@app.middleware("http")
async def private_response_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/api/auth", "/api/account", "/api/payments", "/api/assets")):
        response.headers["Cache-Control"] = "no-store"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await setup_tables()
    await setup_auth()
    if os.getenv("SETTLEMENT_ENABLED") == "true":
        from services.payments.settlement import settlement_worker
        app.state.settlement_task = asyncio.create_task(settlement_worker())
    print("DKM API started - pgvector tables ready")


@app.on_event("shutdown")
async def shutdown():
    task = getattr(app.state, "settlement_task", None)
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

    fraud = fraud_detector.check_upload(
        data,
        embedding
    )

    if fraud["is_fraud"]:
        raise HTTPException(
            422,
            f"Upload rejected: {fraud['reason']}"
        )

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
                file.filename or "knowledge_asset",
                data,
                file.content_type or "application/octet-stream",
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

        print("PINATA FILE RESPONSE:", pinata_response)

        file_cid = pinata_response["data"]["cid"]

    # ---------------------------------------------------------
    # Add file CID + BLAKE3 hash to metadata
    # ---------------------------------------------------------

    meta["file_cid"] = file_cid

    meta["blake3_hash"] = quantum_hash(data)

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

        print(
            "PINATA METADATA RESPONSE:",
            metadata_response
        )

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
    results = await quantum_enhanced_search(body.query.strip(), domain=body.domain, max_price=body.max_price)
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
    return {"token_id": token_id, "wallet_address": user["wallet_address"],
            "has_purchased": purchased, "purchase_count": count, "access_granted": granted,
            "file_url": "https://ipfs.io/ipfs/" + onchain["ipfs_cid"] if granted else None,
            "storage_notice": "Files on public IPFS are publicly retrievable; entitlement is a license record, not encryption."}


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
async def capabilities():
    configured = bool(os.getenv("RAZORPAY_KEY_ID", "").startswith("rzp_test_") and os.getenv("RAZORPAY_KEY_SECRET") and os.getenv("SETTLEMENT_ENABLED") == "true" and os.getenv("SETTLEMENT_PRIVATE_KEY"))
    return {"fiat_configured": configured, "fiat_message": "Test checkout configured; availability is verified against each listing before payment." if configured else "UPI/card test checkout awaits settlement deployment and provider credentials.",
            "bridge_available": False, "bridge_message": "Combined swap/bridge checkout is not available on Polygon Amoy.", "chain_id": 80002}


@app.get("/api/assets/{token_id}/payment")
async def latest_payment(token_id: int, user=Depends(current_user)):
    conn = await get_conn()
    try:
        row = await conn.fetchrow("SELECT * FROM payment_orders WHERE user_id=$1 AND token_id=$2 AND payment_method IN ('upi','card') ORDER BY created_at DESC LIMIT 1", user["id"], token_id)
        from services.payments.models import PaymentOrder
        return {"order": PaymentOrder.model_validate(dict(row)).model_dump() if row else None}
    finally:
        await conn.close()


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
