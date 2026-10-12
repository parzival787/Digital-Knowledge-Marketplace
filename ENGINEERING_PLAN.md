# Active TRNSK plan — 2026-10-12

Continue codex/dkm-payment-persistence and existing draft PR #1 from 83e8ea2.
No new PR, deployment, merge, mainnet, real-money payment or research rerun.

## Completed before deployment

1. Read-only official TRNSK Amoy verification and sanitized evidence.
2. Per-market token metadata, exact 6/18-decimal amounts, seller-confirmed listings/
   auction reserves, quotes, balances/allowances and token-separated history.
3. Runtime Transak coverage and fees; unsupported methods remain unavailable.
4. Persisted listing/account/wallet-bound BUY with fresh quote review, provider
   evidence and independent canonical TRNSK delivery. Funding is never access.
5. Sale/account/amount-bound SELL with server verification, durable concurrency
   guards, conflict holds and separate outgoing-transfer evidence.
6. Dynamic Razorpay test-mode prefunded settlement and legacy amount compatibility.
7. Audit-only recording using actual sale denominations and seller proceeds.
8. Cross-market listing preflight, old access/refunds preserved, migration snapshot.
9. Fail-closed Amoy preparation/deployment script, public role template, rollback.
10. Persistent adaptive indexing/backoff and local automated acceptance.

## Approval-dependent sequence

Request exactly the deployment package in HUMAN_ACTION_REQUIRED.md after review.
With explicit approval/public roles: read-only final plan, estimate gas, deploy
ONLY three named contracts and wire ONLY the new splitter, verify manifest,
then activate current/legacy configuration. Re-run acceptance.
Fund separate settlement/recorder test wallets and bounded allowance only with
authorization. Run S/B1/B2 hosted/wallet acceptance, save sanitized evidence and
update FINAL_STATUS.md. Google configuration remains a human action if required.

All production-only work is separated from the local college definition of done.
