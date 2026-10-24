from services.quantum_hash import quantum_hash
from services import pgvector_client as db


class QuantumFraudDetector:
    async def check_upload(self, file_bytes: bytes, embedding: list = None) -> dict:
        content_hash = quantum_hash(file_bytes)

        # Check 1: Exact duplicate (same file, byte for byte)
        conn = await db.get_conn()
        try:
            exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM knowledge_assets WHERE blake3_hash=$1)", content_hash)
        finally:
            await conn.close()
        if exists:
            return {
                "is_fraud": True,
                "reason": "Exact duplicate file detected. This file has already been uploaded.",
                "content_hash": content_hash,
            }

        # Check 2: File is suspiciously tiny
        if len(file_bytes) < 100:
            return {
                "is_fraud": True,
                "reason": "File is too small to be a meaningful dataset.",
                "content_hash": content_hash,
            }

        return {
            "is_fraud": False,
            "content_hash": content_hash,
        }


# Reads persisted uploads; failed storage attempts do not reserve a hash.
fraud_detector = QuantumFraudDetector()
