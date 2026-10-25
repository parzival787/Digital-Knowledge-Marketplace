# QAOA pricing benchmark

Measured local simulation; no marketplace prices or payments changed.
Synthetic logistic demand is an experimental assumption, not observed revenue.

| Metric | Result |
| --- | --- |
| assets | 64 |
| mean_qaoa_relative_gap | 0.176013 |
| mean_qaoa_feasible_probability | 0.975540 |
| qaoa_exact_price_matches | 1 |
| classical_exact_price_matches | 64 |
| mean_qaoa_revenue | 8868.365307 |
| mean_classical_revenue | 10946.111479 |
| mean_reference_revenue | 6555.652042 |
| mean_uniform_revenue | 5145.606211 |
| mean_qaoa_seconds | 0.456721 |
| mean_classical_seconds | 0.000505 |
| mean_exact_seconds | 0.000051 |

## Method and limitations

64 assets; 100 integer price choices; 7 qubits; QAOA depth 2; COBYLA up to 80 objective evaluations; 2048 seeded samples per asset.
The cost Hamiltonian is diagonal negative normalized expected seller revenue, with invalid binary-state penalty 2. RX mixers alternate with cost unitaries. Selection is the most frequent feasible sampled state (ties choose the lower price).
Classical baseline uses bounded scalar optimization and adjacent integer prices; exhaustive search supplies the exact oracle. The uniform baseline has the same sample count. Random reference prices are not the project's LLM recommendations.
This small smooth independent-price problem favors classical optimization. Full diagonal construction and simulator costs are exponential; no scalable quantum oracle, hardware speedup or quantum advantage is claimed.
Parameters, probabilities, counts, traces, per-asset results and runtime are in qaoa_pricing.json. Budget exhaustion is recorded rather than mislabelled convergence.

References: https://arxiv.org/abs/1411.4028 and https://docs.pennylane.ai/en/stable/code/api/pennylane.DiagonalQubitUnitary.html
