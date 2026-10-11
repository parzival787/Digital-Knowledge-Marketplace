# DKM master checklist — 2026-10-11

This replaces the previous owner checklist. FINAL_STATUS.md distinguishes evidence
levels; TEST_EVIDENCE.md records actual checks, including checks not yet run.

## Implemented

- [x] Welcome -> signup/login -> authenticated workspace; wallet proof and isolation.
- [x] Encrypted upload, persistent duplicate guard, mint/link recovery, search,
  purchaser reviews and protected downloads.
- [x] Marketplace/auction contract flows and current/legacy client handling.
- [x] Durable Web2 test orders, settlement checkpoints, review/refund recovery.
- [x] Shared route capabilities and expiring fixed-price quote validation.
- [x] Transak sandbox BUY/SELL sessions, account binding, saved histories and
  server verification; independent payout states and audited SELL conflict resolution.
- [x] Audit registry source plus durable backend evidence/recording/reversal jobs,
  nonce protection and canonical transaction/event checks; disabled until deployment.
- [x] Persistent current/legacy event indexing, exact payout-event accounting,
  reorg holds, reconciliation and direct paginated current account positions.
- [x] Buyer/seller dashboard sections for uploads, positions, provider history,
  payment/receipt status, reviews, payout preference and verified payout history.
- [x] Mandatory QAOA/VQC implementation, measured comparisons and research page.
  Results underperform the main classical baselines; retain that conclusion.
- [x] Migration inventory/rollback plan; Slither/compiler review and local upgrade;
  concurrency/abuse/restart checks and PostgreSQL restore drill.
- [x] Consolidated acceptance runner, exact demo runbook and human-only action list.

## Still Codex-owned

- [x] Execute the newest auction/refund decoding and source-polling fairness tests.
  Follow-up suite: six passed after the temporary approval-review quota cleared.
  Latest consolidated run: 68 backend tests and all four other acceptance checks.
- [x] Inspect the signed-in rendered dashboard and six APIs; welcome/signup/logout
  also inspected. Disposable local account removed after checking empty states.
- [x] Review/stage only task implementation changes and commit milestone b871557.
  Preserve unrelated llm_enrichment.py, trailing-space contracts directory, output
  and tmp. Documentation/evidence follow separately on the same draft PR branch.
- [ ] Finish historical backfill and refresh migration sign-off when RPC capacity
  permits. Current data is a confirmed indexed range, not lifetime accounting.
- [ ] Verify final provider/deployment integration after the external gates below;
  fix defects found by human acceptance rather than treating the runbook as a pass.

## Human/external gates

Use HUMAN_ACTION_REQUIRED.md for exact actions; no code/DB tasks are delegated.

- [ ] Separate seller/buyer/bidder wallets and signed test transactions.
- [ ] Completed supported Transak sandbox BUY/SELL; actual provider routes/fees.
- [ ] Google OAuth configuration and login if needed in the presentation.
- [ ] Existing content-key backup and replacement of exposed RPC credentials.
- [ ] Separately approved receipt-registry/funded-market deployment and signer roles.
- [ ] A supported real conversion/swap route if the rubric requires actual arbitrary
  crypto/fiat rather than sandbox demonstrations. Current Amoy MockUSDC has no
  executable universal swap route; no signup or alternative provider guarantees it.

## Explicit remaining limitations

Transak sandbox TRNSK is not Amoy MockUSDC. Razorpay test uses a prefunded treasury,
not INR-to-USDC conversion. SELL preference is not automatic per-sale payout.
All-in provider FX/route costs cannot be promised without an executable provider
quote. The seller pays the existing DKM fee from gross proceeds; it is not added
again to the buyer. Automatic chargeback ingestion/partial reversal processing is
not implemented; terminal linkage exists but unverified assertions are rejected.

Production hosting, mainnet, KYB/live fiat compliance, managed keys/signers,
independent audit, sustained production load and richer scoring are outside this
local-demo continuation. No claim of full project completion is made.
