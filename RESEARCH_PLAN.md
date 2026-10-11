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

Status: required engineering; experiment implementation and measured results are
still pending. These references guide the method, not evidence of DKM results.
