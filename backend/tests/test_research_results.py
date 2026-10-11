import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
import httpx
from services import research_results as research


class ResearchResultsTests(unittest.IsolatedAsyncioTestCase):
    async def test_authentication_and_generated_evidence(self):
        app = FastAPI()
        app.include_router(research.router)

        async def denied():
            raise HTTPException(401, "Sign in required")

        app.dependency_overrides[research.current_user] = denied
        async def signed_in():
            return {"id": "test"}

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            self.assertEqual((await client.get("/api/research/results")).status_code, 401)
            app.dependency_overrides[research.current_user] = signed_in
            response = await client.get("/api/research/results")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["changes_marketplace_prices"])
        self.assertFalse(data["changes_production_search"])
        self.assertEqual(data["pricing"]["summary"]["assets"], 64)
        self.assertEqual(len(data["pricing"]["samples"]), 8)
        self.assertEqual(data["embeddings"]["output_dimensions"], 384)
        self.assertIn("test", data["embeddings"]["summary"])

    def test_missing_invalid_and_oversized_files(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(research, "RESULTS", Path(directory)):
            self.assertIsNone(research.load_result("missing.json"))
            path = Path(directory) / "result.json"
            path.write_text("broken", encoding="utf-8")
            self.assertIsNone(research.load_result("result.json"))
            path.write_text(" " * 4_000_001, encoding="utf-8")
            self.assertIsNone(research.load_result("result.json"))
            path.write_text(json.dumps({"valid": True}), encoding="utf-8")
            self.assertEqual(research.load_result("result.json"), {"valid": True})
