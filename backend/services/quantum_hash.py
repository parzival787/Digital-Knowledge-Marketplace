import blake3


def quantum_hash(data: bytes) -> str:
    """
    Generate a BLAKE3 hash of binary data.
    """
    return blake3.blake3(data).hexdigest()


def verify_integrity(data: bytes, expected_hash: str) -> bool:
    """
    Verify that the supplied data matches the expected hash.
    """
    return quantum_hash(data) == expected_hash


def hash_string(text: str) -> str:
    """
    Convenience function for hashing strings.
    """
    return quantum_hash(text.encode("utf-8"))


if __name__ == "__main__":
    data1 = b"test data for hashing"
    data2 = b"different data"

    h1 = quantum_hash(data1)
    h2 = quantum_hash(data1)
    h3 = quantum_hash(data2)

    print(f"Hash: {h1}")
    print(f"Same input = same hash: {h1 == h2}")
    print(f"Different input = different hash: {h1 != h3}")
    print(f"Integrity check: {verify_integrity(data1, h1)}")