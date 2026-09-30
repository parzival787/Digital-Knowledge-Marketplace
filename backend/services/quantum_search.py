# backend/services/quantum_search.py
print("LOADING QUANTUM_SEARCH")
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

    # Quantum walk: amplitude starts concentrated at the query node
    psi = np.zeros(n, dtype=complex)
    psi[start_i] = 1.0 + 0j

    for _ in range(steps):
        psi = A @ psi  # Spread amplitude through graph
        norm = np.linalg.norm(psi)
        if norm > 0:
            psi = psi / norm  # Keep normalized (unit length)

    # Probability of "finding" the walker at each node = |amplitude|^2
    probs = {nodes[i]: float(np.abs(psi[i]) ** 2) for i in range(n)}
    return probs


def qubo_rerank(assets: list, scores: dict, top_k: int = 10) -> list:
    n = len(assets)
    if n <= top_k:
        return assets

    ids = [a.get("token_id") or a.get("vector_id") for a in assets]

    # QUBO formulation: minimize negative of relevance
    # while penalizing co-selection of similar items
    Q = {}
    for i in range(n):
        # Diagonal: reward for selecting this item (negative = we want to select it)
        Q[(i, i)] = -scores.get(ids[i], 0)
        for j in range(i + 1, n):
            # Off-diagonal: penalty for selecting two items together
            # This encourages diversity in the final result set
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


async def quantum_enhanced_search(query: str, domain: str = None, max_price: int = None, min_quality: float = 0.4) -> list:
    from services.embedding import embed_query
    from services.pgvector_client import semantic_search

    # Step 1: Classical semantic search via pgvector (fast, ~20ms)
    query_vec = embed_query(query)
    candidates = await semantic_search(query_vec, top_k=20, domain=domain, max_price=max_price, min_quality=min_quality)

    if len(candidates) < 2:
        return candidates

    # Step 2: Build knowledge graph and run quantum walk
    G = build_asset_graph(candidates)
    start = candidates[0].get("token_id") or candidates[0].get("vector_id")
    qscores = quantum_walk_discover(G, start, steps=3)

    # Merge: 60% semantic similarity + 40% quantum walk score
    for c in candidates:
        k = c.get("token_id") or c.get("vector_id")
        c["quantum_score"] = qscores.get(k, 0)
        c["final_score"] = 0.6 * c.get("score", 0) + 0.4 * c["quantum_score"]

    candidates.sort(key=lambda x: x["final_score"], reverse=True)

    # Step 3: QUBO diversity optimization – pick best diverse top-10
    score_map = {(c.get("token_id") or c.get("vector_id")): c["final_score"] for c in candidates}
    return qubo_rerank(candidates, score_map, top_k=10)
