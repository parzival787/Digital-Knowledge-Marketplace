"""Public ratings, with writes restricted to verified on-chain purchasers."""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from . import pgvector_client as db, blockchain
from .auth import wallet_user

router = APIRouter(prefix="/api/assets", tags=["Reviews"])


class Review(BaseModel):
    rating: int = Field(ge=1, le=5, strict=True)
    review_text: str = Field(default="", max_length=2000)


@router.get("/{token_id}/reviews")
async def get_reviews(token_id: int, offset: int = 0):
    if token_id <= 0 or not 0 <= offset <= 10000:
        raise HTTPException(400, "Invalid review page")
    conn = await db.get_conn()
    try:
        # Historical rows are preserved; only the latest review per wallet counts.
        query = """WITH latest AS (SELECT DISTINCT ON (lower(buyer_address)) *
            FROM reviews WHERE token_id=$1 AND rating BETWEEN 1 AND 5
            ORDER BY lower(buyer_address), created_at DESC, id DESC) """
        stats = await conn.fetchrow(query + "SELECT COUNT(*) AS count, AVG(rating)::float AS average FROM latest", token_id)
        rows = await conn.fetch(query + "SELECT id,rating,review_text,created_at FROM latest ORDER BY created_at DESC,id DESC LIMIT 20 OFFSET $2", token_id, offset)
        return {**dict(stats), "reviews": [dict(r) for r in rows], "next_offset": offset + 20 if offset + 20 < stats["count"] else None}
    finally:
        await conn.close()


@router.post("/{token_id}/reviews")
async def save_review(token_id: int, body: Review, user=Depends(wallet_user)):
    if token_id <= 0:
        raise HTTPException(400, "Invalid asset")
    try:
        asset = await asyncio.to_thread(blockchain.get_knowledge_asset, token_id)
        purchased = await asyncio.to_thread(blockchain.has_purchased, token_id, user["wallet_address"])
    except Exception:
        raise HTTPException(503, "Could not verify your purchase. Retry shortly.") from None
    if asset["creator"].lower() == user["wallet_address"].lower() or not purchased:
        raise HTTPException(403, "Only purchasers can review this asset; creators cannot review their own assets")
    conn = await db.get_conn()
    try:
        async with conn.transaction():
            address = user["wallet_address"].lower()
            await conn.execute("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", f"review:{token_id}:{address}")
            existing = await conn.fetchval("SELECT id FROM reviews WHERE token_id=$1 AND lower(buyer_address)=$2 ORDER BY created_at DESC,id DESC LIMIT 1", token_id, address)
            if existing:
                await conn.execute("UPDATE reviews SET rating=$2,review_text=$3,created_at=NOW() WHERE id=$1", existing, body.rating, body.review_text.strip())
            else:
                await conn.execute("INSERT INTO reviews(token_id,buyer_address,rating,review_text) VALUES ($1,$2,$3,$4)", token_id, address, body.rating, body.review_text.strip())
        return {"success": True}
    finally:
        await conn.close()
