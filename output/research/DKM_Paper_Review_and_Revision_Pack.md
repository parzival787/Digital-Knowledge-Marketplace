# DKM research paper: evidence review and revision pack

Reviewed 21 October 2026. Source: `DKM_Research_Paper (4).pdf`, seven pages. This document reviews the paper against the current repository and retained experiment outputs. It does not modify the submitted PDF or introduce new experimental results. Paths below are relative to the repository root. Payment-provider research is outside this revision.

## 1. Overall assessment

The strongest defensible paper is a hybrid blockchain-backed knowledge-access prototype with transparent evaluations of two quantum algorithms. Its useful research result is that the tested quantum representations and pricing method did **not** beat the strongest classical comparators. Honest negative results are publishable evidence; adding unsupported novelty or security claims would weaken the paper.

The manuscript already acknowledges several limitations well. However, its architecture description predates changes to retrieval, quality scoring and deployed contracts. Correct these before submission. The VQC benchmark is separate from production search: its NDCG values must not be presented as measured accuracy of the application.

Suggested title: **DKM: Blockchain-Backed Knowledge Access with Semantic Retrieval and Classical–Quantum Benchmark Comparisons**. The existing title is also defensible if QAOA remains a smaller secondary study.

## 2. All ten VERIFY markers

| # | Location | Resolution and wording to use |
|---|---|---|
| 1 | Page 1, corresponding email | Unresolved author information. Replace `abc@gmail.com` with the corresponding author's real approved address. Verify names and institutional affiliation with all authors. No technical experiment can resolve this. |
| 2 | Page 3, Table II, marketplace listing | Implemented. Six active listings on the previous Amoy marketplace were observed and their cancellation calls simulated successfully. The newly deployed marketplace had no active listings at the last check. Write: “Implemented; legacy Amoy listings observed and local contract tests passed; a new-market live listing trace is not reported here.” |
| 3 | Page 3, Table II, purchase-to-decryption | No retained complete live end-to-end evidence bundle was identified. Keep “Full live purchase-to-decryption evaluation not reported.” Local purchase tests and separate access/download tests do not establish this combined result. Evidence needed: transaction receipt, entitlement result, authorized download matching the original digest, and an unauthorized account denied access. |
| 4 | Page 3, Section III-B, four addresses | Resolve against `contracts/cents-deployment.json`. Replace current addresses using Section 6 below, and label older ones as legacy. Do not equate compiled source with deployed bytecode. |
| 5 | Page 3, Section III-C, pipeline order | Replace with the actual sequence in Section 4 below. Server enrichment and quality checks precede summary embedding, encryption and Pinata storage; wallet minting happens separately after upload persistence. |
| 6 | Page 4, Table III, RoyaltySplitter | Current: `0x36CAa5b59825a378664E75b5EFB30988F71901c0`. The address printed in the paper is the legacy splitter. Both are historical facts, not conflicting versions of one deployment. |
| 7 | Page 4, Table III, Marketplace | Current: `0xc1cfA63fDA41cD1Ee76B24F1D1B2b993661a67A5`. The paper's `0xDe7b...A5d` is the previous marketplace and remains relevant to existing records. |
| 8 | Page 5, Section IV-A, domain mix | Eight domains: science, finance, healthcare, technology, social, agriculture, environment and other. Each contains four topics and three document variants per topic: 12 documents/domain, 96 total. There are four queries/domain, two validation and two test: 32 total. Fit uses 64 documents; 32 variants are held out from fitting but included in retrieval. |
| 9 | Page 5, QAOA inclusion | Keep it: QAOA and VQC are required project components according to the project brief. Present QAOA as a separate synthetic algorithm evaluation, not a deployed price-setting mechanism or evidence of actual revenue. Remove the internal “optional/VERIFY” note. |
| 10 | Page 6, Table V, environment | Versions are retained: VQC uses PennyLane 0.45.1, NumPy 2.5.1, scikit-learn 1.9.0 and sentence-transformers 5.6.0. QAOA records PennyLane 0.45.1, NumPy 2.5.1 and SciPy 1.18.0. Original-run CPU, RAM and OS remain unverified. A present-day host inspection alone would not prove the original benchmark environment. |

Seven markers can be resolved from existing records or the stated project scope; three still need author information, a live evidence bundle, or historical environment confirmation. The listing marker must retain the distinction between previous and current deployments.

## 3. What has actually been implemented, and what the evidence establishes

| Component | Supported claim | Evidence and boundary |
|---|---|---|
| Account authentication and wallet association | Implemented account/session and wallet-proof flows | Backend auth code and `backend/tests/test_auth.py`. This is not an independent security audit. |
| Document upload and metadata | Server extracts an excerpt, enriches metadata and persists uploaded assets | `backend/main.py`, `backend/services/text_extractor.py`, `backend/services/llm_enrichment.py`. A successful upload does not mean a successful NFT mint. |
| Quality assessment | Four-criterion, excerpt-grounded LLM assessment with backend score calculation | Same enrichment module; sanity-check evidence in `output/research/ui_search_scoring_checks.json`. No human calibration, factual-accuracy or originality result. |
| Semantic discovery | MiniLM summary embeddings, pgvector cosine candidates, deduplication and classical MMR reranking | `backend/services/embedding.py`, `pgvector_client.py`, `quantum_search.py`. The legacy function/file name does not make this a quantum search algorithm. |
| Encrypted off-chain content | AES-GCM envelope-encrypted content, backend-controlled decryption | Upload/download code. Backend key custody is a central trust assumption; this is not end-to-end encryption against the operator. |
| Registration and access | ERC-721 registration and entitlement-gated document access | Contract and backend checks. Buying access must not be described as transferring NFT ownership: the creator can remain the NFT owner. |
| One-cent mint minimum | Successor deployment accepts 10,000 six-decimal units, or 0.01 USDC | Deployment manifest, contract tests and a read-only live estimate. An estimate is not a completed mint receipt. |
| Legacy preservation | Fixed legacy prefix of six assets and old purchase entitlements retained | `KnowledgeAssetSuccessor.sol`, successor tests and `backend/tests/test_legacy_access.py`. This is read-through compatibility, not copying or migrating the original NFTs. |
| Mint recovery | Saved uploads can resume without a user-supplied code; matching completed mints can be recovered | `backend/tests/test_mint_recovery.py`, `frontend/tests/mintResume.test.mjs`. Automatic registry scanning is bounded to 100 tokens. No global exactly-once guarantee across concurrent devices. |
| Listing cancellation | Confirmed-receipt handling and explicit chain/gas preparation implemented | Six legacy cancellation simulations passed; estimated 51,299 gas each. No user listing was actually cancelled during those checks; current-market cancellation was not exercised live because no active listing existed. |
| Auctions and marketplace actions | Contract/frontend implementations exist | Contract suite provides local functional evidence. Do not claim every action was executed publicly merely because its interface exists. |
| VQC representation experiment | Completed controlled statevector benchmark | `research_results/vqc_embeddings.json`, `vqc_model.npz`, `VQC_EMBEDDINGS_REPORT.md`; `backend/research/run_embeddings.py`, `vqc_embeddings.py`. |
| QAOA pricing experiment | Completed synthetic statevector benchmark | `research_results/qaoa_pricing.json`, `QAOA_PRICING_REPORT.md`; `backend/research/qaoa_pricing.py`, `run_pricing.py`. |
| Database restore | A local database dump/restore drill compared table row counts and digests | `restore_drill_evidence.json`. Does not cover independent key backup or external IPFS restoration. |
| Post-quantum key release | Proposed only | Do not put it in implemented contributions. ML-KEM requires an implemented and evaluated protocol, not just a standards citation. |

Recent engineering checks recorded in PROJECT_CONTEXT include 131 contract tests, 17 frontend tests, three mint-recovery tests, and nine backend checks from their respective runs, plus a frontend production build. These runs have differing scopes and may overlap; do not sum them into one freshly executed total. A paper should archive commands, timestamps, commit identifiers and logs before presenting test counts as reproducible evidence.

## 4. Copy-ready replacement text

### Abstract

Knowledge marketplaces require searchable descriptions, auditable asset registration and controlled access to reusable content. We present DKM, a hybrid prototype combining ERC-721 registration on Polygon Amoy, encrypted off-chain document storage, wallet-linked access checks and semantic discovery. The backend assesses document excerpts using a structured four-criterion language-model rubric and indexes summary embeddings for cosine retrieval with maximum marginal relevance reranking. Because the backend controls decryption keys, the design provides blockchain-backed registration and access records rather than fully decentralized content confidentiality. We separately evaluate variational quantum embeddings and QAOA pricing using classical simulation. On a controlled corpus of 96 authored documents and 32 queries, test NDCG@10 was 0.9053 for original MiniLM embeddings, 0.7027 for a PCA-based comparator and 0.6093 for the trained quantum representation. Across 64 synthetic pricing cases, QAOA exhibited a mean relative revenue gap of 17.60% from the exact optimum, while the classical comparator matched the optimal price in every case. Neither experiment demonstrates quantum advantage. The contribution is an implemented prototype and a bounded comparative evaluation, with explicit limitations concerning centralized key custody, author-defined relevance labels, single-seed evaluation and incomplete live end-to-end evidence.

### Introduction: problem and scope

Registering an asset on a blockchain does not, by itself, make its content searchable, establish its scientific quality or provide confidential delivery. A knowledge marketplace must connect registration records with off-chain content, discovery metadata and an enforceable access path. DKM investigates this integration through a locally operated application backed by a public testnet. Its scope is registration and licensed access to knowledge assets; registration does not establish copyright ownership or independently verify authorship.

The system also provides a setting for examining whether small quantum feature models and quantum approximate optimization offer useful improvements over classical baselines. We evaluate these components separately from the operational application so that algorithmic results are not confused with deployment claims. The experiments are executed using classical simulation and are intended as comparative prototype studies, not demonstrations of hardware speedup.

Use literature citations to support the broader motivation. Do not assert that all existing marketplaces lack these features without a documented review and feature-by-feature source evidence.

### Contributions

1. An implemented hybrid architecture connecting encrypted knowledge content, blockchain registration, wallet-linked entitlement checks and semantic discovery.
2. A structured, excerpt-grounded metadata-assessment process and a classical diversity-aware retrieval pipeline, with their trust and validation limits stated explicitly.
3. A controlled comparison of original embeddings, PCA-based reconstruction and untrained/trained variational quantum representations, with retained rankings and experiment artifacts.
4. A synthetic QAOA pricing comparison against classical optimization and exhaustive search, reporting objective gaps, feasibility and runtime without claiming advantage.

These are system and evaluation contributions. MMR, MiniLM, AES-GCM, QAOA and variational circuits are existing methods; do not claim to have invented them.

### Research questions

- RQ1: Under the controlled corpus and common relevance labels, how do compressed classical and quantum representations compare with original embeddings on NDCG@10?
- RQ2: On the stated synthetic demand model and finite price grid, how closely does the QAOA implementation approach the exhaustive optimum compared with a classical optimizer?
- RQ3: Which registration, retrieval, recovery and access-control properties are implemented and supported by retained engineering evidence, and which remain unevaluated?

Do not present hypotheses formulated after seeing the results as preregistered hypotheses. Production retrieval quality and human agreement with the LLM rubric are future evaluation questions until measured.

### Actual ingestion and registration pipeline

The server bounds and validates an upload, extracts a text excerpt and independently generates structured metadata and criterion scores. It applies the quality threshold, embeds the generated summary and performs existing content/duplicate checks. A BLAKE3 digest identifies the plaintext. The content is encrypted with AES-GCM, and its content key is wrapped under backend-controlled key material. The encrypted file and public metadata are uploaded to Pinata, after which the upload record is stored in PostgreSQL. The user subsequently approves a separate wallet transaction to mint the registration token. Receipt verification and account-scoped linking associate the persisted upload with its on-chain token.

These operations are not one atomic transaction across IPFS, PostgreSQL and the blockchain. A failed mint can leave a valid saved upload requiring recovery. The plaintext digest and the encrypted object's IPFS CID identify different representations and must not be treated as interchangeable values.

### Current production retrieval

The application embeds a query and retrieves up to 60 eligible published candidates using pgvector cosine similarity. Candidates are deduplicated by content identity and token identity, and non-positive similarity candidates are excluded from ranking. Up to ten results are selected greedily using maximum marginal relevance:

`MMR(d) = 0.85 × cos(q, d) − 0.15 × max(0, max[s in S] cos(d, s))`.

Here `S` contains already selected results; its redundancy term is zero for the first selection. This classical reranker balances query relevance and redundancy. It replaces the graph/QUBO description in the current-system section. Historical graph helpers may remain in source, but their presence is not evidence that they run in the active search path. Similarity and MMR scores are ranking signals, not probabilities of relevance.

Production indexing uses generated summaries. The VQC experiment uses its authored corpus directly, so its scores do not validate the complete production summary-generation and retrieval pipeline.

### Quality-assessment method

The default Ollama configuration uses llama3.2:3b with temperature zero and seed 31, subject to deployment configuration. The model returns integer scores from zero to four for clarity, specificity, completeness and documented evidence. The backend computes `Q = (clarity + specificity + completeness + evidence) / 16` and applies a threshold of 0.4. Positive scores require supporting excerpt quotations; missing evidence removes the associated positive score and invalid quotations are rejected by validation.

Assessment is limited to an excerpt of at most 4,000 characters, with extraction additionally limited to the first five PDF pages or first 51 CSV lines where applicable. Therefore “completeness” refers to the available excerpt, not the entire scientific work. Quote matching establishes that cited text occurs in the excerpt; it does not establish factual correctness or that the score is justified. The rubric is not a plagiarism detector, originality measure or validated peer-review substitute. The model does not set the seller's price.

The retained sanity check assigned 0.5625 to a detailed example on repeated calls and 0.125 to a vague example. These two examples illustrate behavior only. They do not measure scoring accuracy, reliability across documents or agreement with expert reviewers. Temperature zero and a seed do not establish universal reproducibility across model/runtime versions.

### Security and trust model

The backend is trusted with plaintext processing, master-key custody and access decisions. Blockchain records provide an independently inspectable registration and entitlement reference, while encrypted off-chain storage protects stored content under the implemented key-management assumptions. An authorized recipient can retain or redistribute downloaded plaintext, and the system does not provide DRM. Token registration is not proof of legal ownership, scientific validity or original authorship. Post-quantum key distribution is not implemented and is excluded from current security claims.

### Results interpretation and conclusion

Original MiniLM embeddings provided the strongest retrieval performance in the controlled benchmark. Training improved the quantum representation only slightly relative to the untrained comparator, and both remained below the PCA-based and original-embedding baselines. This experiment does not establish that quantum methods are generally inferior; it establishes that this four-qubit representation, training objective and corpus did not produce an improvement. Similarly, QAOA did not outperform the classical comparator on the tested small independent pricing problems. DKM demonstrates a functioning architectural integration and retains evidence for these bounded algorithmic comparisons, while further work is required for independent relevance judgments, repeated-run uncertainty, production retrieval evaluation and complete live access-flow validation.

## 5. Verified numerical results and reporting details

### VQC

| Split | Original MiniLM | PCA4 + ridge expansion | Untrained VQC + ridge | Trained VQC + ridge |
|---|---:|---:|---:|---:|
| Validation | 0.915266 | 0.654188 | 0.534822 | 0.611822 |
| Test | 0.905296 | 0.702724 | 0.605030 | 0.609317 |

Report NDCG@10, not “90.53% accuracy.” Test improvement over the untrained VQC is approximately 0.004287 absolute NDCG. No confidence interval or significance result has been established by the retained single-run comparison.

Method details: seed 31; PCA with four components fitted to 64 document vectors; arctan-scaled angle encoding; four qubits; two RY/RZ layers with ring CNOT connections; 16 trainable rotation parameters; four Z and four adjacent ZZ expectations; Adam step size 0.04 for 40 epochs; cosine-Gram alignment loss; ridge expansion with alpha 0.01 to 384 dimensions. Expansion restores dimensionality, not information discarded by compression. Simulation uses exact statevector expectations, not noisy hardware measurements.

Training time: 1.026658 seconds. Initial/best loss: 0.485185/0.098681. Recorded transform times cover all 96 documents and 32 queries, not one query. Fit excludes 32 document variants, but query topics occur in fitting documents. Therefore this is in-domain evaluation, not unseen-topic generalization. Relevance labels 3/1/0 are authored rules, not independent assessor judgments.

### QAOA

| Metric | Retained result |
|---|---:|
| Synthetic cases | 64 |
| Mean relative gap from exact revenue | 17.6013% |
| Mean feasible probability | 97.5540% |
| QAOA exact-price matches | 1 / 64 |
| Classical exact-price matches | 64 / 64 |
| Mean QAOA objective/revenue | 8,868.3653 |
| Mean classical objective/revenue | 10,946.1115 |
| Mean QAOA elapsed seconds | 0.456721 |
| Mean classical elapsed seconds | 0.000505 |
| Mean exhaustive elapsed seconds | 0.000051 |

Use “synthetic expected revenue/objective units,” not actual money earned. Configuration: 100 integer prices, seven qubits, depth two, COBYLA capped at 80 objective evaluations, 2,048 seeded samples per case. Invalid binary states receive a penalty; selection uses the most frequent feasible sampled state. The random reference is not an LLM price recommendation. This study does not change live asset prices.

The roughly 19.0% reduction shown using mean revenues differs from the 17.60% mean of per-case relative gaps. Both aggregations can be valid, but label them separately. Figure 4 currently says “Gap Distribution” without showing a distribution; rename it “QAOA and classical pricing comparison” or plot the actual per-case gaps.

## 6. Deployment evidence appendix

Network: Polygon Amoy, chain ID 80002. Tokens are test assets, not evidence of mainnet readiness.

| Contract | Current | Legacy |
|---|---|---|
| Knowledge registry | `0xCA6f1E6C08Dddda08e4288B8eFE07bF54f67AeD7` | `0x2C16409A3db9880f9A70e71B5b131A17db533Fc9` |
| Marketplace | `0xc1cfA63fDA41cD1Ee76B24F1D1B2b993661a67A5` | `0xDe7bdacb8B3ff631dbcdb09C81c0de7421475A5d` |
| Royalty splitter | `0x36CAa5b59825a378664E75b5EFB30988F71901c0` | `0x43cE72CEd667bDe9252044451b07ecA1aec2D300` |
| MockUSDC | `0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719` | Unchanged |

Use `contracts/cents-deployment.json` as the deployment artifact, including transaction hashes and block numbers. The successor reads existing IDs 1–6 from the original registry; new IDs begin at 7. Preserve chain, registry and token ID together as asset identity. The current deployment used Solidity 0.8.37, optimizer 200 and Shanghai target; do not assign that compiler retrospectively to legacy deployments.

Keep full addresses and receipts in an appendix or public artifact package, not a cramped main-text table. RPC/receipt checks do not imply independent explorer source verification or an external audit.

## 7. What needs proof, and what kind

| Paper section or claim | Appropriate support |
|---|---|
| Introduction: broader problem | Relevant literature or concrete use cases; no mathematical proof is needed for the motivation. Avoid universal claims. |
| Related work and novelty | Original sources plus a reproducible review scope: databases, query strings, date range, inclusion rules and a feature-definition matrix with supporting page/section references. “Not described in the reviewed paper” is safer than “does not exist.” |
| Architecture | Current code paths, sequence diagram and deployment manifest. A conceptual diagram alone is not implementation evidence. |
| Registration and entitlements | Receipts/events plus contract state and positive/negative authorization checks. Registration does not prove legal rights. |
| Encryption | Cite the primitive and state key-management assumptions; validate tamper rejection and access checks. Using AES-GCM does not prove the complete application secure. |
| Quality scoring | Rubric and prompt/configuration for implementation; independent human ratings and agreement/error analysis for claims of usefulness or accuracy. |
| Search quality | Fixed corpus, explicit labels, baselines, identical evaluation protocol, per-query results and uncertainty. Screenshots prove UI behavior, not ranking quality. |
| Quantum claims | Circuit, encoding, objective, optimizer budget, simulator, seeds and classical comparators. Circuit execution does not establish quantum advantage. |
| Performance | Hardware at run time, versions, workload, sample size, warm/cold distinction and latency distributions. Single elapsed values are insufficient for scalability. |
| Reliability | Explicit failure injection, recovery outcomes and boundary cases. Do not generalize a database-only drill to complete disaster recovery. |

## 8. Most valuable additional experiments — not yet claimed as done

1. **Production retrieval comparison:** evaluate keyword/BM25, original full-text or excerpt embeddings, generated-summary cosine retrieval and summary cosine plus MMR using the same corpus and labels. Measure NDCG@10, Recall@10 and redundancy/diversity. Keep tuning on validation data. This directly addresses the actual application instead of relying on the VQC benchmark.
2. **Independent relevance judgments:** obtain at least two assessors, document instructions and disagreement handling, and separate in-domain and unseen-topic tests. Add a suitable public corpus if licensing and task match permit. Author-defined topic labels are a controlled test, not a substitute for this.
3. **VQC repeated runs and ablation:** repeat multiple declared seeds; report mean, spread and paired comparisons. Vary PCA dimension, circuit depth, trained versus untrained and reconstruction. Keep sample budgets comparable. Query bootstrap uncertainty alone would remain conditional on one fitted model; it would not measure training variability.
4. **Quality-rubric validation:** have independent readers score a varied document set using the same rubric. Compare criterion-level agreement and rank correlation, inspect acceptance-threshold errors, and test misleading but well-written excerpts. Record exact model version/digest and prompt. Do not label rubric scores scientific truth.
5. **One complete access trace:** preserve a successful on-chain entitlement event/receipt, authorized download digest, unauthorized-wallet denial and expired-session denial. If checkout is excluded from the paper, focus the report on entitlement verification and content delivery while stating how the test entitlement was established.
6. **Failure/recovery matrix:** failed mint after upload, pending mint reload, confirmed mint with failed DB linking, duplicate recovery, wrong-account recovery, old/new registry identity collision, cancelled listing and modified ciphertext. Distinguish local automated tests from public-testnet observations.
7. **Latency evidence:** measure extraction, model inference, embedding, search, storage upload and download separately; report sample counts and median/p95 with cold/warm conditions. Do not combine testnet confirmation time with local computation into a vague “fast” claim.

Prioritize 1, 4 and 5 for application credibility, and 2–3 for a stronger algorithmic research contribution. These are proposed experiments, not results produced by this review.

## 9. Figures, tables and organization

- Replace Figure 1's graph/QUBO component with cosine candidate retrieval, deduplication and MMR. Show the backend/key-custody trust boundary, encrypted storage, public metadata and blockchain separately.
- Add a small sequence diagram: upload → persisted draft → wallet mint → receipt → token link → entitlement check → content delivery. Include the failed-mint recovery path.
- Separate the deployed application diagram from experimental VQC/QAOA diagrams. Readers should not infer that simulated circuits execute during every search or purchase.
- Replace Table II's red internal draft notes with “implemented,” “locally tested,” “public-testnet observed” and “not evaluated,” each with a precise evidence reference.
- Rename or redraw Figure 4 as noted above. Enlarge labels and use vector graphics where possible; small one-column panels currently make the quantitative evidence harder to read.
- Move contract addresses and lengthy configuration details to an appendix. Use the main-text space for research questions, protocol and limitations.
- Remove every VERIFY placeholder, conversational note and unqualified novelty statement before submission. Do not erase an unresolved issue by silently converting it into a positive claim.

Recommended structure: Introduction; Related Work; System and Trust Model; Implementation; Experimental Protocol; Results; Threats to Validity; Conclusion; Artifact Availability. Keep QAOA and VQC results in distinct subsections.

## 10. Primary references to add or check

These support methods, not claims that DKM itself has been validated:

- Reimers and Gurevych, Sentence-BERT: https://arxiv.org/abs/1908.10084
- Official all-MiniLM-L6-v2 model card, including 384-dimensional output and default 256-wordpiece truncation: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- Carbonell and Goldstein, MMR: https://www.cs.cmu.edu/afs/cs/Web/People/jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf
- Farhi, Goldstone and Gutmann, QAOA: https://arxiv.org/abs/1411.4028
- Lloyd et al., Quantum embeddings for machine learning: https://arxiv.org/abs/2001.03622
- Bergholm et al., PennyLane: https://arxiv.org/abs/1811.04968
- NIST FIPS 203, ML-KEM, only if retained as future work: https://csrc.nist.gov/pubs/fips/203/final

The AQUASTREAM DOI referenced by the paper is `10.1109/ICoICI65217.2025.11252760`. Its full text was not independently inspected in this review. The feature-absence claims across all 18 related-work papers are therefore not certified. Obtain and read the originals before using the comparison table as the foundation of a novelty claim.

## 11. Artifact package and your remaining inputs

Before submission, freeze a named repository commit and package the corpus/query generation code, relevance labels, training split, configuration, package versions, result JSON files and model artifact. Include run commands, environment information and a clear statement that the circuits ran on a classical simulator. Inspect the package for secrets, personal data and redistribution restrictions before making it public.

Provide or confirm:

1. Real corresponding-author email, author spellings and affiliation.
2. Target venue/template and page limit, so content can be sized appropriately.
3. Original benchmark CPU/RAM/OS if known from the run; otherwise report the omission honestly or rerun with recorded hardware.
4. The editable LaTeX/Word source if you want these revisions applied directly to the paper.
5. Independent assessors or labeled data if you want stronger retrieval/quality claims; these cannot be fabricated from the current code.

This review did not retrain models, run new live purchases or complete an independent security/bibliography audit. A hardware-inspection attempt was blocked because automatic approval review encountered a usage-limit error; no hardware value has been guessed. The retained results support a bounded prototype paper, not production security, fully decentralized custody, post-quantum security or quantum advantage.
