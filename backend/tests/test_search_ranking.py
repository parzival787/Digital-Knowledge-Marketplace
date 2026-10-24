import unittest
from unittest.mock import patch, AsyncMock

from services.quantum_search import rank_results, quantum_enhanced_search


def asset(token, score=0.9, vector=None, fingerprint=None):
    return {"token_id": token, "vector_id": str(token), "score": score,
            "embedding": vector or [1.0, 0.0], "blake3_hash": fingerprint,
            "title": "A shared title", "summary": "Document description", "tags": [],
            "file_cid": "private-reference", "metadata_cid": "internal"}


class SearchRankingTests(unittest.IsolatedAsyncioTestCase):
    def test_duplicates_drafts_and_private_fields(self):
        rows = [asset(None), asset(1, fingerprint="same"), asset(2, fingerprint="same"),
                asset(1, 0.8), asset(3, 0.7), asset(4, -0.1)]
        result = rank_results(rows)
        self.assertEqual([a["token_id"] for a in result], [1, 3])
        self.assertEqual(result[0]["summary"], "Document description")
        self.assertNotIn("embedding", result[0])
        self.assertNotIn("blake3_hash", result[0])
        self.assertNotIn("file_cid", result[0])

    def test_relevance_diversity_and_repeatability(self):
        rows = [asset(1, 0.95), asset(2, 0.94), asset(3, 0.9, [0.0, 1.0])]
        expected = rank_results(rows)
        self.assertEqual([a["token_id"] for a in expected], [1, 3, 2])
        self.assertEqual(rank_results(list(reversed(rows))), expected)
        self.assertEqual(rank_results(rows, top_k=1), expected[:1])
        self.assertEqual(rank_results([]), [])

    async def test_live_entry_point_filters_before_candidate_limit(self):
        with patch("services.embedding.embed_query", return_value=[1.0, 0.0]), patch(
            "services.pgvector_client.semantic_search", new_callable=AsyncMock, return_value=[asset(1)]
        ) as search:
            result = await quantum_enhanced_search("topic", domain="science", max_price=0.25)
        self.assertEqual(result[0]["token_id"], 1)
        self.assertTrue(search.call_args.kwargs["published_only"])
        self.assertEqual(search.call_args.kwargs["max_price"], 0.25)
