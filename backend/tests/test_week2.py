import pytest

from services.text_extractor import extract_text
from services.llm_enrichment import enrich_document
from services.quantum_hash import quantum_hash, verify_integrity
from services.fraud_detector import QuantumFraudDetector

SAMPLE_DOC = b"""
Maharashtra Crop Production Statistics 2015-2023.
District-wise monthly data for 36 districts and 12 crop types.
Variables:
yield_tonnes_per_hectare,
rainfall_mm,
irrigation_pct,
temperature_celsius.

Useful for agricultural policy,
food security research,
and climate impact analysis.

well but sometimes these are not good enough for the farmers to get the right price for their crops. The government has been trying to address this issue by implementing various schemes and policies.
 However, there is still a long way to go in ensuring that farmers receive fair compensation for their produce.
"""


def test_text_extractor_txt():
    text = extract_text(SAMPLE_DOC, "test.txt")

    assert len(text) > 50
    assert "Maharashtra" in text

    print(f"Extracted {len(text)} characters")


def test_blake3_hashing():
    h1 = quantum_hash(b"hello")
    h2 = quantum_hash(b"hello")
    h3 = quantum_hash(b"world")

    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64
    assert verify_integrity(b"hello", h1)

    print(f"BLAKE3 hash: {h1[:16]}...")


def test_fraud_detector():
    detector = QuantumFraudDetector()

    # More than 100 bytes to pass the size check
    data = b"Some dataset content here. " * 10

    result1 = detector.check_upload(data)

    assert not result1["is_fraud"]

    result2 = detector.check_upload(data)

    assert result2["is_fraud"]
    assert "duplicate" in result2["reason"].lower()

    print("Fraud detector caught duplicate correctly")


@pytest.mark.asyncio
async def test_llm_enrichment():
    text = extract_text(SAMPLE_DOC, "test.txt")

    metadata = await enrich_document(text)

    assert "title" in metadata
    assert "summary" in metadata
    assert "tags" in metadata
    assert "domain" in metadata
    assert "quality_score" in metadata

    assert 0.0 <= metadata["quality_score"] <= 1.0

    assert metadata["domain"] in [
        "science",
        "finance",
        "healthcare",
        "technology",
        "social",
        "agriculture",
        "environment",
        "other",
    ]

    assert isinstance(metadata["tags"], list)

    print(f"Title: {metadata['title']}")
    print(f"Domain: {metadata['domain']}")
    print(f"Quality: {metadata['quality_score']:.2f}")
    print(f"Tags: {', '.join(metadata['tags'][:5])}")
    print("LLM enrichment test PASSED")