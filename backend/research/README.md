# backend/research

Offline QAOA pricing and VQC embedding simulator experiments. These do not execute during production search or change live prices. Install the separate research requirements if rerunning; retain seeds/configuration and compare baseline metrics. Result artifacts are in ../../research_results.

## Files

### [__init__.py](__init__.py)

Python package initializer; may be intentionally empty.

### [qaoa_pricing.py](qaoa_pricing.py)

Synthetic demand objective, diagonal QAOA cost/mixer circuit, sampled selection and classical/exact comparators.

Main entry points: `demand_revenue`, `circuit_for`, `optimize_prices`.

### [run_embeddings.py](run_embeddings.py)

Constructs the authored corpus/query splits, runs comparable embedding methods and saves per-query metrics/artifacts.

Main entry points: `corpus`, `main`.

### [run_pricing.py](run_pricing.py)

Executes the seeded synthetic pricing experiment and writes per-case data and report.

Main entry points: `main`.

### [vqc_embeddings.py](vqc_embeddings.py)

PCA/angle preprocessing, variational quantum feature circuit, training and ridge reconstruction for the separate VQC benchmark.

Main entry points: `normalize`, `quantum_features`, `decoder`, `expand`, `train`, `transform`, `ndcg`.
