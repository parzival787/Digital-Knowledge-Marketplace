# Audit-only blockchain payment records

PaymentReceiptRegistry records verified payment evidence. It never moves funds,
changes NFT ownership or grants access. Marketplace.hasPurchased remains the
license authority. The registry source and backend integration are implemented;
there is no deployed registry or public recording claim.

## Implemented flow

Confirmed current/legacy sale event -> historical splitter payout verification ->
immutable payment_evidence -> durable receipt_jobs -> separate recorder signer ->
signed transaction checkpoint -> identical-byte retry -> canonical transaction,
calldata, emitted event and stored payment hash verification -> recorded status.

The source payment is rechecked immediately before signing/broadcast. Reorgs,
configuration changes and contradictory evidence enter review_required. An
uncertain signed job blocks new nonce allocation. Jobs use database advisory locks;
polling rotates pending work so old unfinished evidence cannot starve later work.

The adapter accepts Amoy Marketplace sales and independently verified Razorpay
test captures associated with completed funded purchases. Funding-only Transak
BUY, standalone SELL, mock payments and client redirects cannot create sale
evidence. SELL history remains separate because no verified asset-sale association
exists for a standalone withdrawal.

Payment and payout denominations commit to token chain/address/base units or ISO
currency/decimals. Integer amounts preserve units. The payout amount is actual
splitter seller net; the existing seller-paid platform fee is not added again to
the buyer. Raw provider IDs, KYC, emails, bank/card data and keys never go on chain.
Provider references use environment/provider-domain HMAC; source evidence uses a
private random salt. Preserve the content master key during rotation planning:
existing reference deduplication and encrypted content depend on it.

## States and reversals

Provider evidence has pending verification and verified/conflict states in its own
order ledger. Only verified sale evidence enters the recorder: verified ->
recording -> recorded, or review_required. Temporary RPC failure retains the
checkpoint and a generic error. A submitted hash is not proof of confirmation.

Full Razorpay test refunds are fetched server-side and linked to the immutable
original record. The registry/job model supports terminal full refund (2) and
chargeback (3). Automatic chargeback ingestion is not claimed: it needs an
authenticated provider dispute source and verified eligibility; no public endpoint
accepts a user's or operator's assertion of a chargeback. Partial reversals are
unsupported and require review rather than fabricated full-refund evidence.

## Configuration and operations

RECEIPT_RECORDING_ENABLED defaults false. After separately approved deployment,
configure PAYMENT_RECEIPT_REGISTRY_ADDRESS and a dedicated
RECEIPT_RECORDER_PRIVATE_KEY, distinct from SETTLEMENT_PRIVATE_KEY, in ignored
backend/.env. The registry must be on chain 80002, sandbox=true, with the recorder
role granted. Never commit these keys. Preserve signed checkpoints during recovery;
do not delete uncertain jobs or blindly re-sign. Investigate held evidence and
canonical receipts before any operational repair.

GET /api/payments/recordings shows sanitized audit status to the buyer and verified
seller wallet. Dashboard distinguishes reversal, pending, recorded and review.
No arbitrary evidence-creation or force-complete API is exposed.

See MIGRATION_PLAN.md for approval/rollback, SECURITY_NOTES.md for verification,
and DEMO_RUNBOOK.md for local versus deployed acceptance.
