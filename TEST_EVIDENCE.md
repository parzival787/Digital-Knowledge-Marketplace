## Latest TRNSK acceptance — 2026-10-12

- Consolidated acceptance_results.json: 82 backend tests, 15 frontend regressions,
  production frontend build, 129 contract tests and contract typecheck passed.
- Additional canonical-sale eligibility test passed: correct seller/token/positive
  proceeds, changed block and rejected mismatches. This test is included in the 82-test run. Final Transak/funding follow-up: 11 passed.
- Deployment script rejected the in-process non-Amoy network before any journal
  or public transaction. An initial sandbox command could not load local Hardhat;
  the subsequent permitted run executed the script and verified the guard.
- Read-only TRNSK evidence: transak_token_evidence.json. Chain 80002, contract code,
  TRNSK symbol, 18 decimals, balance/allowance and zero-value approve/transfer
  eth_call passed. These calls do not prove funded transfers.
- Provider coverage/quote evidence: transak_coverage_evidence.json. Actual staging
  API response offered USD/EUR card methods, no INR/UPI for localhost lookup.
  Observed 10-token BUY quote USD 11.46 total with USD 1.46 provider fees; this is
  expired evidence, not a current price or real FX claim. No order was paid.
- Migration snapshot refreshed at block 49969644, five listings, zero auctions,
  matching app configuration. Old addresses/wiring preserved.
- Restarted API returned old token USDC/6 and both purchase/auction capability;
  Razorpay unavailable with absent signer. Browser welcome/signup show only auth
  navigation; Google reports setup pending. No wallet/provider E2E was simulated
  into a live-success claim.
- Bounded adaptive history attempt left next_block 45942252, state backfilling,
  error 'Indexer unavailable; checkpoint preserved'. Full history is unverified.
- Original QAOA/VQC and backup/Slither evidence retained; no research rerun.

Everything below records earlier milestones and is superseded by this section.

# Verification evidence

## Autonomous remaining-work continuation (after b49d5f6)

- RPC follow-up: Polygon's formerly documented rpc-amoy.polygon.technology endpoint
  failed DNS resolution. Polygon's July 2026 announcement confirms its retirement.
  The replacement documented polygon-amoy.drpc.org responded, but a 2,000-block
  eth_getLogs request for 45927547–45929546 returned HTTP 400 / code 35, message
  "ranges over 10000 blocks are not supported on free plan". That inconsistent
  limit response was not treated as an empty result or successful backfill.
  Existing credentials/configuration were not changed. Sources:
  [current RPC documentation](https://docs.polygon.technology/pos/reference/rpc-endpoints)
  and [retirement announcement](https://forum.polygon.technology/t/deprecation-of-polygons-public-rpc-endpoints-mainnet-amoy/22014).

- Latest consolidated run: **68 backend tests**, **12 frontend regressions**,
  production frontend build, **128 contract tests**, and contract typecheck all
  passed. acceptance_results.json records all five zero exit codes.
- Direct current/legacy positions test passed: wallet scope, block-pinned license,
  listing/auction/refund reads, pagination and wrong-registry rejection.
- Legacy download and review tests now exercise current-false/old-true entitlement
  lookups through the actual APIs; frontend legacy cancellation, bid, finalization,
  refund and duplicate-purchase regression tests also passed.
- Original payment canonical/reorg checks and no-signing-on-source-removal passed;
  both buyer and verified seller can see sanitized audit status.
- Browser: welcome and signup show authentication controls only. Google correctly
  reports configuration pending. A disposable local account signed in successfully;
  all dashboard sections rendered, direct Amoy positions resolved, and payout/
  recording/backfill limitations were visible. Six account/history APIs returned
  200. Logout restored welcome-only navigation. The test account/sessions were
  removed; no public transaction or provider checkout occurred.
- Follow-up index/source suite: **6 passed**, including the two newer tests for
  actual auction/refund ABI decoding and fair source polling. The initial command
  was blocked by approval-review quota; the later approved run completed normally.

- SELL: three new database tests passed for binding, duplicates, amount/currency
  conflicts, terminal regression, late completion, audited resolution and restart/
  outage recovery. Nine existing BUY/provider tests also passed.
- Recorder: durable persistence/restart/nonce-serialization tests passed. Actual
  signed transaction decoding and emitted-event fixtures passed after correcting
  a missing-transaction fixture constructor. No chain broadcast performed.
- Indexer: two tests passed for concurrency/idempotency, exact integer totals,
  deployment discovery, checkpoint reorg fail-closed handling and derived rebuild.
- Source adapters: two tests passed for reverified chain evidence, duplicate/reorg
  rejection and provider amount/currency/status binding.
- First combined backend run: 63 tests, one payout fixture failure. The fixture
  now initializes seller_payouts in its isolated schema; the targeted test passed
  and includes API history isolation. The later 68-test run above passed; the
  initial fixture failure is retained here as historical evidence.
- Slither after compiler adoption: 29 contracts / 102 detectors, zero high/medium,
  four low timestamp findings and one informational pragma-range finding. Registry
  included. Source compilation succeeded; no independent audit claim.
- Solidity 0.8.30 and 0.8.37 each passed 128 local tests; default local build now
  uses 0.8.37/Shanghai. Contract TypeScript checking passed.
- Live read-only: Amoy index pages persisted; snapshot at block 49870192 found
  five listings and zero auctions, matching frontend/backend legacy configuration.
- Restore: streamed local PostgreSQL dump into a disposable database; counts and
  content digests matched for all 12 public tables. Disposable copy removed.
- Provider completion, registry deployment/recording and interactive E2E remain
  unverified. Backfill does not yet prove lifetime totals or all historical buyers.

## Research and BUY reconciliation milestone (2026-10-11)

- LOCALLY TESTED: 9 Transak database/provider-boundary tests passed, including
  concurrent worker claims, outage recovery and contradictory terminal evidence.
  Provider calls are simulated; no real checkout or payout was performed.
- LOCALLY TESTED: 7 QAOA/VQC/results-API tests passed: known quantum circuit,
  probability normalization, seeded sampling, feasible prices, finite/dimension
  validation, ranking metric, training transform and authenticated result access.
- EXPERIMENT EXECUTED: 64 synthetic QAOA price cases; 17.60% mean revenue gap,
  1 exact price match versus 64 for classical optimization.
- EXPERIMENT EXECUTED: trained four-qubit VQC with 40 epochs; test NDCG@10
  0.6093 versus original 0.9053 and PCA4 0.7027. Full per-case/per-query outputs
  and model arrays retained under research_results; no quantum advantage claim.
- LOCALLY TESTED: all 12 frontend regressions passed; production build, typecheck
  and lint passed, including /research. Optional pino-pretty warning remains.
- Restricted-shell in-process API tests stalled; the same seven tests passed
  under normal approved local execution. Stalled test processes were stopped.
- Not INTERACTIVE E2E VERIFIED: research-page browser inspection, signed wallet
  purchases and completed provider payment/payout flows. No public deployment.

## 2026-10-11 baseline (commit 6612caf)

- LOCALLY TESTED: `backend/venv/Scripts/python.exe -m unittest tests.test_auth
  tests.test_payments tests.test_transak tests.test_receipts tests.test_activity
  tests.test_legacy_access -q`: **41 passed**. Disposable database schemas;
  provider/chain boundaries simulated where the tests patch them.
- LOCALLY TESTED: `contracts/node_modules/.bin/hardhat.cmd test`: **128 passed**.
  Hardhat 3 local in-memory execution; no public deployment.
- LOCALLY TESTED: from frontend, `node --test tests/*.test.mjs`: **10 passed**.
- LOCALLY TESTED: frontend `next build`: passed compilation, lint/type checks and
  static generation. Existing optional WalletConnect `pino-pretty` warning remains.
- GitHub PR #1 confirmed open/draft/unmerged, head 6612caf matching the local
  feature branch. No duplicate PR created.

## Capability milestone

- LOCALLY TESTED: capability + auth suites: **18 passed** (15 existing + 3 new).
- LOCALLY TESTED: all frontend regression tests: **11 passed**.
- LOCALLY TESTED: frontend production build/typecheck/lint passed.
- READ-ONLY DEPLOYMENT VERIFIED: capability probe returned Amoy marketplace
  0xDe7bdacb8B3ff631dbcdb09C81c0de7421475A5d, payment token
  0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719 and paused=false.
  Fixed-price and auction routes available with per-transaction checks;
  configured Transak BUY/SELL sandbox entry available; Razorpay, actual UPI,
  arbitrary crypto routing and receipt recording unavailable.
- Not INTERACTIVE E2E VERIFIED: wallet signing, completed provider payments,
  payouts, Google login, new registry deployment or recording.

Baseline sandbox attempts could not use local Hardhat paths/Docker connections;
the same suites passed with approved local execution. This was a tooling boundary,
not a contract migration. The PDF's older tests remain historical evidence only.

## Fixed-price purchase quote milestone

- LOCALLY TESTED: 3 quote tests passed, covering Solidity-style integer rounding,
  account isolation, concurrent idempotent acceptance, changed terms, expiry and
  failed revalidation. The three capability tests passed alongside them.
- LOCALLY TESTED: new authenticated quote API test passed (session, verified
  wallet, CSRF, UUID validation and no-store responses).
- LOCALLY TESTED: all 12 frontend regressions passed; production build/typecheck
  and lint passed with the same optional logging dependency warning.
- READ-ONLY DEPLOYMENT VERIFIED: token 1 fixed listing quoted 10,000,000 payment
  token base units, 500,000 platform fee, zero royalties and 9,500,000 seller net.
  No account order, wallet signature or payment was created by this probe.
- Limits: a saved quote does not spend tokens, reserve a listing or grant access.
  Final on-chain terms can change after the last read; the deployed buyAsset
  method does not bind an expected quote hash. This race needs explicit treatment
  in the deployment/failure review. No wallet purchase was signed for these tests.

Final staging coverage/quote probe refreshed successfully with the same supported routes and amounts. Staged exact-local-credential scan: no matches; unrelated enrichment edit excluded. Build has the existing optional WalletConnect pino-pretty warning; build/typecheck passed.
