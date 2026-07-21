import argparse
import asyncio
import sys

from services.embedding import generate_embedding
from services.pgvector_client import semantic_search


async def main():
    parser = argparse.ArgumentParser(description="Run a semantic search test query.")
    parser.add_argument(
        "query",
        nargs="?",
        default="crop production and agriculture",
        help="Query text to embed and search for.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Max number of results to return.",
    )
    args = parser.parse_args()

    print(f"Query: {args.query!r}")
    print("Generating embedding...")

    try:
        embedding = await asyncio.to_thread(generate_embedding, args.query)
    except Exception as e:
        print(f"Failed to generate embedding: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Embedding length: {len(embedding)}")

    try:
        results = await semantic_search(embedding, top_k=args.limit)
    except Exception as e:
        print(f"Semantic search failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Results found: {len(results)}")

    if not results:
        print("No results returned.")
        return

    for i, row in enumerate(results, start=1):
        print(f"\n[{i}]")
        print(f"Title      : {row['title']}")
        print(f"Score      : {row['score']:.6f}")
        print(f"Distance   : {row['distance']:.6f}")
        print(f"Vector ID  : {row['vector_id']}")
        print(f"Domain     : {row['domain']}")
        print(f"Quality    : {row['quality']}")
        print(f"Price(usdc): {row['price_usdc']}")


if __name__ == "__main__":
    asyncio.run(main())