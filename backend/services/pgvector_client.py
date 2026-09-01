import os
import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector
import uuid

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
            CREATE INDEX IF NOT EXISTS assets_domain_idx
            ON knowledge_assets(domain)
        """)

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
):
    conn = await get_conn()

    try:
        vector_id = str(uuid.uuid4())

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
                embedding
            )
            VALUES (
                $1,$2,$3,$4,$5,$6,$7,$8,$9,$10
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
        )

        return dict(row)

    finally:
        await conn.close()
async def semantic_search(
    query_vec: list,
    top_k: int = 20,
    domain: str = None,
    max_price: int = None,
) -> list:

    conn = await get_conn()

    try:
        vec = np.array(query_vec, dtype=np.float32)

        where_clauses = ["quality >= 0.4"]
        params = [vec]

        if domain:
            where_clauses.append(f"domain = ${len(params) + 1}")
            params.append(domain)

        if max_price:
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

