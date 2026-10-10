# Verification evidence

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
