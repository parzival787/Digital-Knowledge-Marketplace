# UI, search and assessment verification

Updated 20 October 2026. Changes remain local on the existing feature branch.

## Delivered

- Responsive search cards with summaries, topic tags, collapsible filters,
  useful loading/empty/error states and direct single-asset links.
- Active navigation, consistent surfaces and focus indicators. Service diagnostics
  removed from primary navigation; history synchronization details are expandable.
- Fiat/Transak/UPI/card panels remain removed. Wallet purchase and auction controls
  remain; useful blockchain confirmation links replace raw listing hashes.
- Search filters out unfinished uploads and deduplicates token/content identities
  before the candidate limit. Separate documents sharing a title are not deleted.
- Semantic candidates use existing normalized 384D MiniLM summary embeddings;
  production reranking is deterministic maximum marginal relevance. The 0.85/0.15
  weighting is an engineering heuristic, not a measured retrieval improvement.
- Local cached model loading avoids network metadata calls during user searches.
- Ollama produces a schema-validated rubric with reasons and source quotations.
  Four equally weighted 0–4 criteria yield the score divided by 16.
- Client-submitted quality cannot set the stored score. Upload reassesses the file;
  the frontend uses the verified returned score for minting.
- Missing supporting quotes receive zero credit. Invalid or fabricated quotations
  fail validation. Analysis failure never silently assigns 0.5 or another score.
- The score's scope is visible during creation. Evidence quotations are excluded
  from public metadata. Existing scores, files and entitlements remain unchanged.

## Actual checks

1. Frontend: 14 regression tests passed; TypeScript passed; production build passed.
   The existing optional WalletConnect/pino-pretty build warning remains.
2. Backend: first combined run passed 30 of 32 tests and exposed two database vector
   decoding errors. Fixed decoding using the installed pgvector Vector.to_list().
   Final targeted 10-test run passed, covering database filtering/deduplication,
   fractional-price persistence, authoritative upload scores, rubric validation,
   invalid-PDF handling, failure without fallback and deterministic retrieval.
3. QAOA/VQC: circuit, seeded sampling, normalization, feasible pricing, NDCG,
   training dimensions and saved-results/authentication checks passed. No benchmark
   outputs were replaced and no quantum advantage is claimed.
4. Real Ollama on synthetic text: detailed document scored 56.25/100 twice; a vague
   document scored 12.5/100. Full evidence is in
   output/research/ui_search_scoring_checks.json. The model can still misjudge
   evidence; repeatability here is not a general determinism guarantee.
5. Live database inspection: 23 uploads, two linked tokens. Search for “machine
   learning” returned HTTP 200 with unique token IDs 1 and 6 in 2.95 seconds.
6. Browser: signed-in navigation and final search page verified; both returned
   results had a View asset link. A browser-discovered query-parameter issue was
   fixed using useSearchParams/Suspense; the asset-6 link then displayed only
   asset 6. Its description, tags and license loaded without raw storage IDs.
   No fiat/provider checkout controls appeared. Logout restored the welcome-only
   view. The empty disposable test account and its sessions were removed.

## Limitations relevant to the research paper

This revision replaces the production graph/QUBO retrieval path described in the
older paper guide. QAOA pricing and VQC are still separate simulator experiments.
Keep their saved results separate from production-search claims.

The rubric assesses only the extracted excerpt, not full-paper truth, originality,
copyright or scientific validity. Existing legacy scores do not have this rubric.
No independent relevance judgments, retrieval ablation benchmark, large-scale
performance study or full wallet transaction was performed in this UI task.

Reproduction: from backend run the project's venv Python with
`-m unittest tests.test_llm_enrichment tests.test_search_ranking tests.test_qaoa
tests.test_vqc tests.test_research_results tests.test_auth`. Auth/database tests
require the existing local PostgreSQL instance and use disposable schemas.
