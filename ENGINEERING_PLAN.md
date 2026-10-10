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
- Conditional: embedded wallet and research only if the rubric requires them.

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
8. Update current documentation and final human acceptance script; commit logical
   milestones to existing PR. Keep incomplete and blocked items explicit.

Completion requires implementation plus the agreed automated and human acceptance
checks. A milestone commit is not a claim that the entire project is complete.
