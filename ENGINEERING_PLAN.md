# Local college demo execution plan

Updated 2026-10-11. Baseline: PDF report, commit 6612caf, active draft PR #1 on
codex/dkm-payment-persistence. Preserve existing implementations and deployments.

## Baseline delta

- IMPLEMENTED / LOCALLY TESTED: accounts, wallet proofs, encrypted content,
  marketplace and auction source, durable payment recovery, Transak sessions and
  saved BUY orders, receipt registry source. Existing 128 contract tests and 10
  frontend regression tests passed again on this continuation.
- PROVIDER VERIFIED (previous run): Transak staging authentication and BUY/SELL
  session creation only. No new provider payment performed.
- Not INTERACTIVE E2E VERIFIED: complete creator/buyer/two-bidder journeys,
  Google login, completed provider checkout and payout.
- Incomplete engineering: shared capabilities, full quotes, SELL verification,
  durable receipt recording, persistent event indexing/accounting, migration
  inventory, failure handling and final acceptance automation.
- Human/external dependencies: HUMAN_ACTION_REQUIRED.md. No deployment or funds
  spending is authorized by this execution plan.
- REQUIRED (owner confirmed 2026-10-11): QAOA pricing and VQC embeddings, including
  trained/optimized experiments, classical baselines, measured evaluation and
  report evidence. Existing classical QUBO reranking does not complete these.
- Other previously conditional additions stay separate; do not ask the owner to
  reconfirm that QAOA/VQC are required.

## Ordered milestones

1. Establish baseline suites; centralize server capabilities and consume them in
   funding, payout, fixed-price and auction controls. Fail closed on unknown state.
2. Persist integer-unit expiring quotes; verify price/accounting from contracts;
   preserve the seller-paid platform fee and require re-review on changed totals.
3. Complete provider BUY/SELL tracking with account binding, verified routes,
   independent payout states and duplicate/out-of-order safeguards.
4. Add normalized immutable evidence and a durable registry recording worker:
   dedicated signer, checkpoint, nonce serialization, canonical/event checks,
   reversal links. Never derive access from registry evidence.
5. Index confirmed events incrementally with reorg reconciliation; expose auction
   lifecycle, refunds, gross/fee/royalty/net accounting in account views.
6. Produce a machine-readable migration inventory and compatibility evidence;
   prepare deployment/rollback proposal without executing it.
7. Finish practical security/recovery checks, backup restore drill, registry audit
   and compiler assessment; preserve existing encryption keys and owner edits.
8. Complete required QAOA pricing and VQC embedding experiments from the handout,
   with reproducible local simulator runs, classical comparisons and NDCG@10 for
   retrieval. Report actual results and limitations without claiming advantage.
9. Update current documentation and final human acceptance script; commit logical
   milestones to existing PR. Keep incomplete and blocked items explicit.

## Milestone progress

- Shared capabilities: implemented and locally tested in 3c486fa; deployment
  wiring also checked read-only. No new deployment.
- Fixed-price wallet quote review: implemented with integer token accounting,
  seller-paid fee/royalties, persisted five-minute terms and account-bound
  revalidation before approval/purchase. This is not an atomic contract reservation.
- Phase 3 remains partial: provider funding/FX/payout quotes remain unavailable;
  Razorpay quote expiry and late capture policy still need integration. Unknown
  external costs are null, never zero. Auction amounts remain their own bid flow.

Completion requires implementation plus the agreed automated and human acceptance
checks. A milestone commit is not a claim that the entire project is complete.
