import asyncio

from services.embedding import generate_embedding
from services.pgvector_client import get_conn


async def main():
    conn = await get_conn()

    embedding = generate_embedding("crop production and agriculture")

    row = await conn.fetchrow(
        """
        SELECT
            id,
            title,
            embedding <=> CAST($1 AS vector) AS distance
        FROM knowledge_assets
        LIMIT 1;
        """,
        embedding,
    )

    print(row)

    await conn.close()


asyncio.run(main())