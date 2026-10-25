from sentence_transformers import SentenceTransformer

_model = None


def get_model() -> SentenceTransformer:
    global _model

    if _model is None:
        print("Loading embedding model all-MiniLM-L6-v2...")
        # Search requests must not stall on remote model metadata/downloads.
        _model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        print("Embedding model ready.")

    return _model


def generate_embedding(text: str) -> list[float]:
    model = get_model()

    vector = model.encode(
        text,
        normalize_embeddings=True
    )

    return vector.tolist()


def embed_query(query: str) -> list[float]:
    return generate_embedding(query)
