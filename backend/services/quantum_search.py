"""Legacy graph experiments plus deterministic production semantic retrieval."""
import asyncio
import networkx as nx
import numpy as np
import dimod

    
def build_asset_graph(assets: list) -> nx.Graph:
    G = nx.Graph()
    for a in assets:
        node_id = a.get("token_id") or a.get("vector_id")
        G.add_node(node_id, **a)

    nodes = list(G.nodes(data=True))
    for i, (node_i, data_i) in enumerate(nodes):
        for node_j, data_j in nodes[i + 1:]:
            shared_tags = set(data_i.get("tags", [])) & set(data_j.get("tags", []))
            same_domain = data_i.get("domain") == data_j.get("domain")
            weight = len(shared_tags) + (1 if same_domain else 0)
            if weight > 0:
                G.add_edge(node_i, node_j, weight=weight)

    return G


def quantum_walk_discover(G: nx.Graph, start_node, steps: int = 3) -> dict:
    nodes = list(G.nodes())
    n = len(nodes)
    if n < 2:
        return {nodes[0]: 1.0} if nodes else {}

    idx_map = {node: i for i, node in enumerate(nodes)}
    start_i = idx_map.get(start_node, 0)

    # Build adjacency matrix weighted by shared tags + domain
    A = nx.to_numpy_array(G, nodelist=nodes, weight="weight")
    row_sums = A.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    A = A / row_sums  # Row-normalize so each row sums to 1

    # Legacy classical propagation, not unitary quantum evolution.
    psi = np.zeros(n, dtype=complex)
    psi[start_i] = 1.0 + 0j

    for _ in range(steps):
        psi = A @ psi  # Spread amplitude through graph
        norm = np.linalg.norm(psi)
        if norm > 0:
            psi = psi / norm  # Keep normalized (unit length)

    # Squared normalized magnitudes are heuristic graph scores.
    probs = {nodes[i]: float(np.abs(psi[i]) ** 2) for i in range(n)}
    return probs


def qubo_rerank(assets: list, scores: dict, top_k: int = 10) -> list:
    n = len(assets)
    if n <= top_k:
        return assets

    ids = [a.get("token_id") or a.get("vector_id") for a in assets]

    # Legacy QUBO rewards relevance and penalizes the number of selected pairs.
    Q = {}
    for i in range(n):
        # Diagonal: reward for selecting this item (negative = we want to select it)
        Q[(i, i)] = -scores.get(ids[i], 0)
        for j in range(i + 1, n):
            # Off-diagonal: penalty for selecting two items together
            # Constant penalties do not measure semantic diversity.
            Q[(i, j)] = 0.3

    # Solve with simulated annealing (classical algorithm, available now on CPU)
    sampler = dimod.SimulatedAnnealingSampler()
    response = sampler.sample_qubo(Q, num_reads=100, num_sweeps=500)
    best = response.first.sample

    # Collect selected assets
    selected = [assets[i] for i in range(n) if best.get(i, 0) == 1]
    remaining = [assets[i] for i in range(n) if best.get(i, 0) != 1]

    # Return selected first, then fill up to top_k with remaining
    return (selected + remaining)[:top_k]


async def quantum_enhanced_search(query: str, domain: str = None, max_price: float | None = None, min_quality: float = 0.4) -> list:
    from services.embedding import embed_query
    from services.pgvector_client import semantic_search

    # Keep the existing entry point; production retrieval is classical, not QAOA/VQC.
    query_vec = await asyncio.to_thread(embed_query, query)
    candidates = await semantic_search(query_vec, top_k=60, domain=domain, max_price=max_price,
                                       min_quality=min_quality, published_only=True)
    return rank_results(candidates)


def rank_results(candidates: list, top_k: int = 10) -> list:
    """Deduplicate identities, then use deterministic maximum marginal relevance."""
    unique, tokens, hashes = [], set(), set()
    for asset in sorted(candidates, key=lambda a: (-a["score"], a["vector_id"])):
        token, content_hash = asset.get("token_id"), asset.get("blake3_hash")
        if not token or asset["score"] <= 0 or token in tokens or (content_hash and content_hash in hashes):
            continue
        tokens.add(token)
        if content_hash:
            hashes.add(content_hash)
        unique.append(asset)
    selected = []
    while unique and len(selected) < top_k:
        def marginal(asset):
            vector = np.asarray(asset["embedding"], dtype=float)
            redundancy = 0.0
            for previous in selected:
                other = np.asarray(previous["embedding"], dtype=float)
                denominator = np.linalg.norm(vector) * np.linalg.norm(other)
                similarity = float(vector @ other / denominator) if denominator else 0.0
                redundancy = max(redundancy, similarity)
            return 0.85 * asset["score"] - 0.15 * redundancy
        best = max(range(len(unique)), key=lambda i: marginal(unique[i]))
        selected.append(unique.pop(best))
    # Catalog output only: embeddings, storage references and fingerprints stay internal.
    fields = ("vector_id", "token_id", "title", "summary", "domain", "tags", "quality", "price_usdc", "score")
    return [{key: asset.get(key) for key in fields} for asset in selected]
