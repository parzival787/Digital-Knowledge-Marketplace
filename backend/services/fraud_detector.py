from services.quantum_hash import quantum_hash


class QuantumFraudDetector:
    def __init__(self):
        # Track file hashes to detect exact duplicates
        self.seen_hashes: set = set()

    def check_upload(self, file_bytes: bytes, embedding: list = None) -> dict:
        content_hash = quantum_hash(file_bytes)

        # Check 1: Exact duplicate (same file, byte for byte)
        if content_hash in self.seen_hashes:
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

        # Passed all checks - record the hash
        self.seen_hashes.add(content_hash)

        return {
            "is_fraud": False,
            "content_hash": content_hash,
        }


# Single instance shared across all requests
fraud_detector = QuantumFraudDetector()