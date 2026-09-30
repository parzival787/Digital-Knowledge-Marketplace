import os
import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector
import uuid


class DuplicateUploadError(ValueError):
    pass

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:devpassword@localhost:5432/dkm"
)


async def get_conn():
    conn = await asyncpg.connect(DB_URL)
    await register_vector(conn)
    return conn

async def setup_tables():
    conn = await get_conn()

    try:
        create_assets = """
        CREATE TABLE IF NOT EXISTS knowledge_assets (
            id SERIAL PRIMARY KEY,

            vector_id TEXT UNIQUE NOT NULL,

            file_cid TEXT DEFAULT '',
            metadata_cid TEXT DEFAULT '',

            title TEXT DEFAULT '',
            domain TEXT DEFAULT 'other',

            tags TEXT[] DEFAULT '{}',

            quality FLOAT DEFAULT 0.5,
            price_usdc INT DEFAULT 5,

            token_id INT,

            blake3_hash TEXT,

            embedding VECTOR(384),

            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """

        create_index = """
        CREATE INDEX IF NOT EXISTS assets_embedding_idx
        ON knowledge_assets
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        """

        create_reviews = """
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,

            token_id INT NOT NULL,

            buyer_address TEXT NOT NULL,

            rating INT DEFAULT 5,

            review_text TEXT DEFAULT '',

            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """

        await conn.execute(create_assets)
        await conn.execute(create_index)
        await conn.execute(create_reviews)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payment_orders (
                order_id TEXT PRIMARY KEY,
                token_id INT NOT NULL CHECK (token_id > 0),
                buyer_address TEXT NOT NULL,
                amount_usdc BIGINT NOT NULL CHECK (amount_usdc > 0),
                payment_method TEXT NOT NULL CHECK (payment_method IN ('mock', 'upi', 'card', 'web3')),
                status TEXT NOT NULL CHECK (status IN (
                    'CREATED', 'PENDING', 'PROVIDER_CONFIRMED', 'SETTLEMENT_PENDING',
                    'SETTLED', 'ENTITLEMENT_GRANTED', 'FAILED'
                )),
                provider_order_id TEXT UNIQUE,
                provider_payment_id TEXT UNIQUE,
                settlement_tx_hash TEXT UNIQUE,
                error TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS assets_domain_idx
            ON knowledge_assets(domain)
        """)

        await conn.execute("""
            ALTER TABLE payment_orders
                ADD COLUMN IF NOT EXISTS fiat_currency TEXT,
                ADD COLUMN IF NOT EXISTS fiat_amount BIGINT,
                ADD COLUMN IF NOT EXISTS exchange_rate TEXT,
                ADD COLUMN IF NOT EXISTS checkout_key TEXT,
                ADD COLUMN IF NOT EXISTS listing_id BIGINT,
                ADD COLUMN IF NOT EXISTS marketplace_address TEXT,
                ADD COLUMN IF NOT EXISTS chain_id BIGINT,
                ADD COLUMN IF NOT EXISTS settlement_raw_tx TEXT
        """)
        await conn.execute("ALTER TABLE payment_orders ADD COLUMN IF NOT EXISTS user_id BIGINT")
        await conn.execute("""
            ALTER TABLE payment_orders
                ADD COLUMN IF NOT EXISTS recovery_status TEXT CHECK (recovery_status IN ('REVIEW_REQUIRED', 'REFUNDED')),
                ADD COLUMN IF NOT EXISTS settlement_attempts INT NOT NULL DEFAULT 0,
                ADD COLUMN IF NOT EXISTS settlement_started_at TIMESTAMPTZ,
                ADD COLUMN IF NOT EXISTS settlement_last_attempt_at TIMESTAMPTZ,
                ADD COLUMN IF NOT EXISTS refund_id TEXT UNIQUE
        """)
        await conn.execute("ALTER TABLE knowledge_assets ADD COLUMN IF NOT EXISTS user_id BIGINT")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payment_recovery_events (
                id BIGSERIAL PRIMARY KEY, order_id TEXT NOT NULL REFERENCES payment_orders(order_id),
                action TEXT NOT NULL, reason TEXT NOT NULL,
                actor TEXT NOT NULL DEFAULT CURRENT_USER, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("ALTER TABLE knowledge_assets ADD COLUMN IF NOT EXISTS summary TEXT DEFAULT ''")
        await conn.execute("CREATE INDEX IF NOT EXISTS assets_hash_idx ON knowledge_assets(blake3_hash)")
        await conn.execute("CREATE INDEX IF NOT EXISTS reviews_token_idx ON reviews(token_id)")
        await conn.execute("ALTER TABLE knowledge_assets ADD COLUMN IF NOT EXISTS encrypted_key TEXT")
        await conn.execute("ALTER TABLE knowledge_assets ADD COLUMN IF NOT EXISTS original_filename TEXT")

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS assets_quality_idx
            ON knowledge_assets(quality)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS assets_token_id_idx
            ON knowledge_assets(token_id)
        """)

        print("pgvector tables created successfully")

    finally:
        await conn.close()

 


async def insert_embedding(
    title: str,
    domain: str,
    tags: list[str],
    quality: float,
    price_usdc: int,
    blake3_hash: str,
    embedding: list[float],
    file_cid: str = "",
    metadata_cid: str = "",
    user_id: int | None = None,
    summary: str = "",
    encrypted_key: str | None = None,
    original_filename: str | None = None,
):
    conn = await get_conn()

    try:
        vector_id = str(uuid.uuid4())

        # Serialize identical content across workers without deleting legacy duplicates.
        await conn.execute("SELECT pg_advisory_lock(hashtextextended($1,0))", "upload:" + blake3_hash)
        if blake3_hash and await conn.fetchval("SELECT 1 FROM knowledge_assets WHERE blake3_hash=$1 LIMIT 1", blake3_hash):
            raise DuplicateUploadError("This file has already been uploaded")

        row = await conn.fetchrow(
            """
            INSERT INTO knowledge_assets (
                vector_id,
                file_cid,
                metadata_cid,
                title,
                domain,
                tags,
                quality,
                price_usdc,
                blake3_hash,
                embedding, user_id, summary, encrypted_key, original_filename
            )
            VALUES (
                $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14
            )
            RETURNING id, vector_id;
            """,
            vector_id,
            file_cid,
            metadata_cid,
            title,
            domain,
            tags,
            quality,
            price_usdc,
            blake3_hash,
            np.array(embedding),
            user_id,
            summary,
            encrypted_key,
            original_filename,
        )

        return dict(row)

    finally:
        await conn.close()
async def semantic_search(
    query_vec: list,
    top_k: int = 20,
    domain: str = None,
    max_price: int = None,
    min_quality: float = 0.4,
) -> list:

    conn = await get_conn()

    try:
        vec = np.array(query_vec, dtype=np.float32)

        where_clauses = ["quality >= $2"]
        params = [vec, max(0.4, min_quality)]

        if domain:
            where_clauses.append(f"domain = ${len(params) + 1}")
            params.append(domain)

        if max_price is not None:
            where_clauses.append(f"price_usdc <= ${len(params) + 1}")
            params.append(max_price)

        where_sql = " AND ".join(where_clauses)

        top_k = max(1, int(top_k))

        sql = f"""
        SELECT
            vector_id,
            file_cid,
            metadata_cid,
            title,
            domain,
            tags,
            quality,
            price_usdc,
            token_id,
            embedding <=> $1 AS distance
        FROM knowledge_assets
        WHERE {where_sql}
        ORDER BY embedding <=> $1
        LIMIT {top_k}
        """

        rows = await conn.fetch(sql, *params)

        return [
            {
                "score": 1 - float(r["distance"]),
                "distance": float(r["distance"]),
                "vector_id": r["vector_id"],
                "file_cid": r["file_cid"],
                "metadata_cid": r["metadata_cid"],
                "title": r["title"],
                "domain": r["domain"],
                "tags": list(r["tags"] or []),
                "quality": float(r["quality"]),
                "price_usdc": r["price_usdc"],
                "token_id": r["token_id"],
            }
            for r in rows
        ]

    finally:
        await conn.close()


async def update_token_id(vector_id: str, token_id: int):
    conn = await get_conn()
    try:
        await conn.execute(
            "UPDATE knowledge_assets SET token_id = $1 WHERE vector_id = $2",
            token_id,
            vector_id,
        )
    finally:
        await conn.close()


async def get_asset_by_token_id(token_id: int):
    conn = await get_conn()

    try:
        row = await conn.fetchrow(
            """
            SELECT
                id,
                vector_id,
                file_cid,
                metadata_cid,
                title,
                domain,
                tags,
                quality,
                price_usdc,
                token_id,
                blake3_hash,
                created_at
            FROM knowledge_assets
            WHERE token_id = $1
            LIMIT 1
            """,
            token_id,
        )

        if not row:
            return None

        return {
            "id": row["id"],
            "vector_id": row["vector_id"],
            "file_cid": row["file_cid"],
            "metadata_cid": row["metadata_cid"],
            "title": row["title"],
            "domain": row["domain"],
            "tags": list(row["tags"] or []),
            "quality": float(row["quality"]),
            "price_usdc": row["price_usdc"],
            "token_id": row["token_id"],
            "blake3_hash": row["blake3_hash"],
            "created_at": row["created_at"].isoformat()
                if row["created_at"]
                else None,
        }

    finally:
        await conn.close()

