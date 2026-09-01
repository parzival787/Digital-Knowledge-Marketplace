# backend/main.py - COMPLETE FINAL VERSION FOR PHASE 1
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os, json, httpx
from dotenv import load_dotenv

load_dotenv()

from services.text_extractor import extract_text
from services.llm_enrichment import enrich_document
from services.embedding import generate_embedding
from services.pgvector_client import (
    setup_tables,
    insert_embedding,
    get_asset_by_token_id,
    update_token_id,
)
from services.quantum_hash import quantum_hash
from services.quantum_search import quantum_enhanced_search
from services.fraud_detector import fraud_detector

from services.blockchain import (
    has_purchased,
    get_purchase_count,
    get_knowledge_asset,
)


app = FastAPI(title="DKM API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await setup_tables()
    print("DKM API started - pgvector tables ready")


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
        checks["ollama_error"] = str(e)

    checks["nft_storage"] = bool(
        os.environ.get("NFT_STORAGE_TOKEN")
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
async def analyze(file: UploadFile = File(...)):
    data = await file.read()
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
    metadata_json: str = "{}"
):
    data = await file.read()

    meta = json.loads(metadata_json)

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

    vid = quantum_hash(
        file_cid.encode()
    )[:16]

    # ---------------------------------------------------------
    # Save to PostgreSQL + pgvector
    # ---------------------------------------------------------

    await insert_embedding(
    title=meta.get("title", ""),
    domain=meta.get("domain", "other"),
    tags=meta.get("tags", []),
    quality=meta.get("quality_score", 0.5),
    price_usdc=meta.get("recommended_price_usdc", 5),
    blake3_hash=meta["blake3_hash"],
    embedding=embedding,
    file_cid=file_cid,
    metadata_cid=metadata_cid,
)

    # ---------------------------------------------------------
    # Return existing API response format
    # ---------------------------------------------------------

    return {
        "file_cid": file_cid,
        "metadata_cid": metadata_cid,
        "vector_id": vid,
    }


@app.post("/api/search")
async def search(body: dict):
    query = body.get("query", "").strip()
    if not query:
        raise HTTPException(400, "query field is required")

    results = await quantum_enhanced_search(
        query, domain=body.get("domain"), max_price=body.get("max_price")
    )
    return {"query": query, "results": results, "count": len(results)}


@app.get("/api/assets/{token_id}/access")
async def check_asset_access(
    token_id: int,
    wallet_address: str
):
    if token_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid token ID"
        )

    asset = await get_asset_by_token_id(token_id)

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Knowledge asset not found"
        )

    try:
        purchased = has_purchased(
            token_id,
            wallet_address
        )

        purchase_count = get_purchase_count(
            token_id,
            wallet_address
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address"
        )

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Blockchain verification failed: {str(e)}"
        )

    return {
        "token_id": token_id,
        "wallet_address": wallet_address,
        "has_purchased": purchased,
        "purchase_count": purchase_count,
        "access_granted": purchased,
        "asset": {
            "title": asset["title"],
            "domain": asset["domain"],
            "quality": asset["quality"],
            "price_usdc": asset["price_usdc"],
        },
    }


@app.post("/api/assets/{vector_id}/link-token")
async def link_token(
    vector_id: str,
    body: dict
):
    token_id = body.get("token_id")
    creator_address = body.get("creator_address")

    if token_id is None:
        raise HTTPException(
            status_code=400,
            detail="token_id is required"
        )

    if not creator_address:
        raise HTTPException(
            status_code=400,
            detail="creator_address is required"
        )

    try:
        token_id = int(token_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="token_id must be an integer"
        )

    try:
        onchain_asset = get_knowledge_asset(token_id)

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Token {token_id} does not exist on-chain"
        )

    if (
        onchain_asset["creator"].lower()
        != creator_address.lower()
    ):
        raise HTTPException(
            status_code=403,
            detail="Creator address does not match NFT creator"
        )

    await update_token_id(
        vector_id,
        token_id
    )

    return {
        "success": True,
        "vector_id": vector_id,
        "token_id": token_id,
        "creator": onchain_asset["creator"],
        "message": "Blockchain token linked to knowledge asset"
    }

