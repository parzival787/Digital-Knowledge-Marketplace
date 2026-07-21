import asyncio

from services.embedding import generate_embedding
from services.pgvector_client import insert_embedding
from services.quantum_hash import hash_string


async def main():
    text = "Maharashtra agriculture dataset"

    embedding = generate_embedding(text)

    result = await insert_embedding(
        title="Agriculture Dataset",
        domain="agriculture",
        tags=["agriculture", "climate"],
        quality=0.9,
        price_usdc=10,
        blake3_hash=hash_string(text),
        embedding=embedding,
    )

    print(result)


asyncio.run(main())