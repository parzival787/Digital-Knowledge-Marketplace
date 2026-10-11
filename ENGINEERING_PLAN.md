# DKM local college demo engineering plan

Updated 2026-10-11. Continue codex/dkm-payment-persistence and draft PR #1.
Current work extends b49d5f6. No public deployment, merge or funds spending.

## Implemented in this continuation

1. Account-bound Transak SELL sessions, durable order history, server-side binding/
   currency verification, conflict holds and audited operator resolution.
2. Immutable audit evidence, durable receipt/reversal jobs, separate recorder
   configuration, checkpoint-before-broadcast, nonce serialization and canonical
   source/transaction/event checks. Recording remains disabled.
3. Current/legacy event indexing, durable checkpoints, reorg holds, exact payout
   event accounting, reconciliation command and account-scoped history.
4. Direct paginated wallet positions, licenses, listings, highest auction bids,
   refundable balances, provider histories, reviews and recording status.
5. Read-only migration inventory, preserved KnowledgeAsset, legacy API/UI tests,
   compiler upgrade review, Slither and PostgreSQL restore drill.
6. Consolidated automated acceptance and separate human demo runbook.

Capabilities, five-minute fixed-price quotes, QAOA and VQC were already completed.
Research results are preserved; no experiments were rerun. QAOA/VQC are required,
and their measured underperformance is reported honestly.

## Verification and external gates

Use acceptance_results.json and TEST_EVIDENCE.md for actual run outcomes.
Provider fixtures are not completed Transak transactions. Historical backfill is
still incomplete: the configured RPC allows small log pages over millions of
blocks. Direct positions do not depend on that backfill.

HUMAN_ACTION_REQUIRED.md and DEMO_RUNBOOK.md cover wallet signatures, provider
interaction, Google setup if desired and future deployment approval. Codex owns
all code, database, tests and reconciliation commands. MIGRATION_PLAN.md is a
proposal, never authorization. Production hosting, live fiat licensing/KYB,
independent audit and managed signing remain production-only.

The existing Razorpay test funded-treasury route is not INR-to-USDC conversion.
Transak sandbox funding does not provide Amoy MockUSDC. No universal currency,
UPI availability, FX quote or seller bank payout is inferred from integration code.
