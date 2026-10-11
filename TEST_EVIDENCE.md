# Verification evidence

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
