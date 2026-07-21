# backend/main.py - COMPLETE FINAL VERSION FOR PHASE 1
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os, json, httpx
from dotenv import load_dotenv

load_dotenv()

from services.text_extractor import extract_text
from services.llm_enrichment import enrich_document
from services.embedding import generate_embedding
from services.pgvector_client import setup_tables, insert_embedding
from services.quantum_hash import quantum_hash
from services.quantum_search import quantum_enhanced_search
from services.fraud_detector import fraud_detector

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
        r = httpx.get("http://localhost:11434/api/tags", timeout=3.0)
        models = [m["name"] for m in r.json().get("models", [])]
        checks["ollama_running"] = True
        checks["llama3_2_ready"] = any("llama3.2" in m for m in models)
        checks["llama3_2_3b_ready"] = any("llama3.2:3b" in m for m in models)
    except Exception as e:
        checks["ollama_running"] = False
        checks["ollama_error"] = str(e)

    checks["nft_storage"] = bool(os.environ.get("NFT_STORAGE_TOKEN"))
    checks["alchemy"] = bool(os.environ.get("ALCHEMY_MUMBAI_URL"))
    checks["database_url"] = bool(os.environ.get("DATABASE_URL"))

    all_ok = all(v for k, v in checks.items() if not k.endswith("_error"))
    return {"status": "ok" if all_ok else "degraded", "checks": checks}


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
async def upload_ipfs(file: UploadFile = File(...), metadata_json: str = "{}"):
    data = await file.read()
    meta = json.loads(metadata_json)

    embedding = generate_embedding(meta.get("summary", ""))

    fraud = fraud_detector.check_upload(data, embedding)
    if fraud["is_fraud"]:
        raise HTTPException(422, f"Upload rejected: {fraud['reason']}")

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            "https://api.nft.storage/upload",
            headers={
                "Authorization": f"Bearer {os.environ['NFT_STORAGE_TOKEN']}",
                "Content-Type": "application/octet-stream",
            },
            content=data,
        )
        r.raise_for_status()
        file_cid = r.json()["value"]["cid"]

    meta["file_cid"] = file_cid
    meta["blake3_hash"] = quantum_hash(data)
    meta_bytes = json.dumps(meta).encode()

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.nft.storage/upload",
            headers={
                "Authorization": f"Bearer {os.environ['NFT_STORAGE_TOKEN']}",
                "Content-Type": "application/json",
            },
            content=meta_bytes,
        )
        r.raise_for_status()
        metadata_cid = r.json()["value"]["cid"]

    vid = quantum_hash(file_cid.encode())[:16]

    await upsert_vector(
        vid,
        embedding,
        {
            "file_cid": file_cid,
            "metadata_cid": metadata_cid,
            "title": meta.get("title", ""),
            "domain": meta.get("domain", "other"),
            "tags": meta.get("tags", []),
            "quality": meta.get("quality_score", 0.5),
            "price_usdc": meta.get("recommended_price_usdc", 5),
            "blake3_hash": meta["blake3_hash"],
        },
    )

    return {"file_cid": file_cid, "metadata_cid": metadata_cid, "vector_id": vid}


@app.post("/api/search")
async def search(body: dict):
    query = body.get("query", "").strip()
    if not query:
        raise HTTPException(400, "query field is required")

    results = await quantum_enhanced_search(
        query, domain=body.get("domain"), max_price=body.get("max_price")
    )
    return {"query": query, "results": results, "count": len(results)}