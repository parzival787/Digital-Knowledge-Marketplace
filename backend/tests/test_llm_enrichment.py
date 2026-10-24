import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from services import llm_enrichment as llm
from services.text_extractor import extract_text

TEXT = "Rainfall measurements in millimeters were collected daily at ten stations. Missing readings are documented."


def metadata():
    return {"title": "Rainfall data", "summary": TEXT, "tags": [" Rain ", "rain"],
            "domain": "science", "quality_score": 0.99,
            "quality_breakdown": {name: {"score": score, "reason": "Some collection details are available.",
                "quote": "Rainfall measurements in millimeters"} for name, score in zip(llm.CRITERIA, [3, 4, 2, 1])}}


class EnrichmentTests(unittest.IsolatedAsyncioTestCase):
    def test_total_computed_from_rubric_not_model_total(self):
        result = llm.validate_metadata(metadata(), TEXT)
        self.assertEqual(result["quality_score"], 10 / 16)
        self.assertEqual(result["tags"], ["rain"])
        self.assertEqual(result["quality_rubric"], "excerpt-v1")
        no_evidence = metadata()
        no_evidence["quality_breakdown"]["clarity"]["quote"] = ""
        self.assertEqual(llm.validate_metadata(no_evidence, TEXT)["quality_breakdown"]["clarity"]["score"], 0)

    def test_reject_fabricated_evidence_invalid_scores_and_missing_criteria(self):
        for value in (True, -1, 5, float("nan"), "4"):
            data = metadata(); data["quality_breakdown"]["clarity"]["score"] = value
            with self.assertRaises(ValueError): llm.validate_metadata(data, TEXT)
        data = metadata(); data["quality_breakdown"]["clarity"]["quote"] = "Invented text absent from source"
        with self.assertRaises(ValueError): llm.validate_metadata(data, TEXT)
        data = metadata(); del data["quality_breakdown"]["evidence"]
        with self.assertRaises(ValueError): llm.validate_metadata(data, TEXT)

    async def test_ollama_options_and_no_fabricated_fallback(self):
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(metadata())))])
        with patch.object(llm.client.chat.completions, "create", new_callable=AsyncMock, return_value=response) as create:
            result = await llm.enrich_document(TEXT)
            self.assertEqual(result["quality_score"], 0.625)
            self.assertEqual(create.call_args.kwargs["temperature"], 0)
            self.assertEqual(create.call_args.kwargs["seed"], 31)
            self.assertEqual(create.call_args.kwargs["response_format"]["type"], "json_schema")
        with patch.object(llm.client.chat.completions, "create", new_callable=AsyncMock, side_effect=RuntimeError("down")), patch.object(llm.asyncio, "sleep", new_callable=AsyncMock):
            with self.assertRaises(llm.AnalysisUnavailable): await llm.enrich_document(TEXT)

    def test_bad_pdf_returns_no_content(self):
        self.assertEqual(extract_text(b"this is not a PDF", "bad.pdf"), "")
