# Required QAOA / VQC work

Owner confirmed on 2026-10-11 that both are core handout requirements, not optional.
Do not substitute existing classical graph propagation or simulated annealing.
The supplied roadmap specifies 50-100 pricing assets and a
384D -> compression -> VQC -> expansion retrieval comparison using NDCG@10.

## QAOA pricing

- Implement a bounded local statevector simulation of genuine alternating cost
  and mixer unitaries, with classical parameter optimization and seeded sampling.
- Define and publish the price/demand objective and feasible price grid. Existing
  listings and seller choices remain unchanged; recommendations are advisory.
- Evaluate 50-100 assets against exhaustive optimum (small-grid oracle), current
  reference prices and a classical optimization baseline under the same objective.
- Save seeds, parameters, circuit size/depth, expectation, selected-price utility,
  revenue estimate, optimality gap, runtime and sampling budget. Synthetic demand
  assumptions must be labelled, never described as observed market revenue.

## VQC embeddings

- Preserve production 384D embeddings. Fit compression only on training data.
- Implement a small trainable angle-encoded entangling circuit, measured features
  and a fitted classical expansion back to the existing dimensionality.
- Train on an explicit training split. Hold out evaluation queries/relevance labels;
  avoid tuning on test NDCG. Compare original MiniLM and equal-compression classical
  baselines, plus untrained-circuit ablation, using the same candidates and labels.
- Save dataset provenance, split, seed, model parameters, training trace, per-query
  NDCG@10 and runtime. A small authored demo corpus is a controlled benchmark, not
  an external real-world relevance dataset. Report limits and any worse results.
- Expose clearly labelled experiment results/demo controls without silently
  replacing the working search pipeline or claiming quantum hardware execution.

## Verification and report

Test normalization, unitary behavior, known small optimization cases, deterministic
seeds, dimension/finite-value validation, no train/test leakage and ranking metrics.
Run actual experiments and retain machine-readable outputs and a report. Never
claim quantum advantage from classical simulation or this small benchmark.

Primary method references consulted 2026-10-11:
- Farhi, Goldstone, Gutmann, *A Quantum Approximate Optimization Algorithm*:
  https://arxiv.org/abs/1411.4028
- Lloyd et al., *Quantum embeddings for machine learning*:
  https://arxiv.org/abs/2001.03622

Status: implemented and locally tested with measured simulator results. The
authenticated /research page presents the evidence; production search and seller
prices are unchanged. This does not establish quantum advantage or independent
academic acceptance.

## Reproduce and inspect

From backend, install the separate requirements-research.txt group if PennyLane
is missing, then run with the project's virtual-environment Python:

```powershell
.\venv\Scripts\python.exe -m research.run_pricing
.\venv\Scripts\python.exe -m research.run_embeddings
.\venv\Scripts\python.exe -m unittest tests.test_qaoa tests.test_vqc tests.test_research_results
```

The embedding run uses the existing cached all-MiniLM-L6-v2 model and does not
download it. Outputs, fitted arrays, seeds, assumptions and reports are retained
in research_results. No private uploaded assets enter either experiment.

- QAOA: 64 synthetic cases, 7 qubits, depth 2, 2,048 samples per case. Mean
  sampled-price revenue gap from the exact optimum: 17.60%. Classical optimization
  matched all 64 exact optimal prices; QAOA matched one. The reference-price
  baseline is synthetic, not a rerun of the existing LLM price recommender.
- VQC: 64 training documents, 96 retrieval documents and 32 held-out queries.
  Test NDCG@10: original 0.9053, PCA4 baseline 0.7027, untrained circuit 0.6050,
  trained VQC 0.6093. Query topics overlap training-document topics; labels are
  authored rules. This is an in-domain controlled benchmark.
- Neither experiment outperformed its principal classical baseline. These are
  actual measured results, not a claim of a production optimization improvement.
