# backend/tests/test_phase1_complete.py

import pytest

from services.text_extractor import extract_text
from services.llm_enrichment import enrich_document
from services.embedding import generate_embedding, embed_query
from services.pgvector_client import (
    setup_tables,
    insert_embedding,
    semantic_search,
)
from services.quantum_hash import quantum_hash
from services.quantum_search import (
    build_asset_graph,
    quantum_walk_discover,
    qubo_rerank,
)

SAMPLE = (
    b"Maharashtra District Agriculture Production Database 2015-2023. "
    b"Monthly statistics for 36 districts: rice yield tonnes per hectare, "
    b"wheat production in metric tons, sugarcane area in hectares, "
    b"rainfall in millimeters, irrigation coverage percentage. "
    b"Useful for food security research, climate impact analysis, "
    b"and agricultural policy."
)


@pytest.mark.asyncio
async def test_complete_phase1_pipeline():

    print("\n========== PHASE 1 END-TO-END TEST ==========\n")

    # ------------------------------------------------------------------
    # STEP 1 : DATABASE
    # ------------------------------------------------------------------
    await setup_tables()
    print("✓ Step 1 : pgvector tables ready")

    # ------------------------------------------------------------------
    # STEP 2 : TEXT EXTRACTION
    # ------------------------------------------------------------------
    text = extract_text(SAMPLE, "sample.txt")

    assert len(text) > 50

    print(f"✓ Step 2 : Extracted {len(text)} characters")

    # ------------------------------------------------------------------
    # STEP 3 : LLM ENRICHMENT
    # ------------------------------------------------------------------
    metadata = await enrich_document(text)

    assert metadata["quality_score"] >= 0.4

    print("✓ Step 3 : Metadata generated")
    print("Title   :", metadata["title"])
    print("Domain  :", metadata["domain"])
    print("Quality :", metadata["quality_score"])
    print("Tags    :", metadata["tags"])

    # ------------------------------------------------------------------
    # STEP 4 : EMBEDDING
    # ------------------------------------------------------------------
    embedding = generate_embedding(metadata["summary"])

    assert len(embedding) == 384

    print("✓ Step 4 : Generated 384-dimensional embedding")

    # ------------------------------------------------------------------
    # STEP 5 : STORE IN PGVECTOR
    # ------------------------------------------------------------------
    test_hash = quantum_hash(SAMPLE)

    inserted = await insert_embedding(
        title=metadata["title"],
        domain=metadata["domain"],
        tags=metadata["tags"],
        quality=metadata["quality_score"],
        price_usdc=metadata["recommended_price_usdc"],
        blake3_hash=test_hash,
        embedding=embedding,
        file_cid="QmTestCID_Phase1",
        metadata_cid="QmMetaCID_Phase1",
    )

    assert inserted is not None

    print(f"✓ Step 5 : Stored in PostgreSQL")
    print(f"Vector ID : {inserted['vector_id']}")

    # ------------------------------------------------------------------
    # STEP 6 : SEMANTIC SEARCH
    # ------------------------------------------------------------------
    query = "crop yield data Maharashtra agriculture districts"

    query_vec = embed_query(query)

    results = await semantic_search(
        query_vec,
        top_k=5,
    )

    assert len(results) > 0

    print(f"✓ Step 6 : Semantic search returned {len(results)} results")
    print(
        f"Top Result : {results[0]['title']} | Score : {results[0]['score']:.4f}"
    )

    # ------------------------------------------------------------------
    # STEP 7 : QUANTUM GRAPH
    # ------------------------------------------------------------------
    graph = build_asset_graph(results)

    start_node = (
        results[0].get("token_id")
        or results[0].get("vector_id")
    )

    quantum_scores = quantum_walk_discover(
        graph,
        start_node,
        steps=3,
    )

    assert isinstance(quantum_scores, dict)

    print(
        f"✓ Step 7 : Quantum walk finished ({len(quantum_scores)} nodes)"
    )

    # ------------------------------------------------------------------
    # STEP 8 : HYBRID SCORE
    # ------------------------------------------------------------------
    for asset in results:

        node = (
            asset.get("token_id")
            or asset.get("vector_id")
        )

        asset["quantum_score"] = quantum_scores.get(node, 0)

        asset["final_score"] = (
            0.6 * asset["score"]
            + 0.4 * asset["quantum_score"]
        )

    score_map = {
        (
            a.get("token_id")
            or a.get("vector_id")
        ): a["final_score"]
        for a in results
    }

    final_results = qubo_rerank(
        results,
        score_map,
        top_k=5,
    )

    assert len(final_results) > 0

    print(
        f"✓ Step 8 : QUBO reranked {len(final_results)} results"
    )

    # ------------------------------------------------------------------
    # STEP 9 : HASH VERIFICATION
    # ------------------------------------------------------------------
    recalculated = quantum_hash(SAMPLE)

    assert recalculated == test_hash

    print("✓ Step 9 : BLAKE3 hash verified")

    print("\n========== PHASE 1 COMPLETED SUCCESSFULLY ==========\n")