# Provider-independent blockchain payment records

## Implemented source

PaymentReceiptRegistry is a separate audit registry. It does not replace
KnowledgeAsset or Marketplace and does not grant download access or move tokens.
It can represent differing buyer-payment and seller-payout denominations. Each
deployment has an immutable sandbox classification.

Only RECORDER_ROLE can write. The deployment admin can revoke/rotate recorder
roles. Internal order references and provider reference commitments are each
single-use. A payment hash commits to all original fields. Full-refund and
chargeback events preserve that original hash and cannot return to Paid.

The contract records what an authorized backend attests. It does not verify banks,
provider signatures, bank payout eligibility, FX rates, or a token transfer on a
different chain. Access MUST NOT be derived from this registry alone.

## Fields and trust boundary

- assetContract/tokenId identify the asset on the record's chain.
- buyer/seller are public wallet identifiers, not email or bank account numbers.
- paymentCurrency/payoutCurrency are bytes32 denomination commitments; use a
  versioned canonical identifier including decimals and, for crypto, chain ID
  and token address. Payment/payout amounts are integer units of those respective
  denominations; do not reinterpret INR paise as token base units.
- payoutAmount is the verified net amount actually paid to the seller. A preference,
  quoted amount or buyer wallet funding event is not payout confirmation.
- providerReference must be a deterministic secret-keyed commitment scoped by
  provider and environment, so retries cannot use a new salt to evade deduplication.
- evidenceHash must commit to an allowlisted, canonical verified receipt with a
  private random salt. Never publish raw payment identifiers, bank/card details,
  email, identity documents, private keys or low-entropy unsalted personal data.

## Required backend connection — not implemented yet

1. Persist the seller's effective price/payout agreement and an expiring buyer quote.
2. Verify payment AND seller payout with the relevant provider (or on-chain proof).
   A client redirect, sandbox success message, preference, or arbitrary administrator
   input must not be accepted as paid evidence.
3. Persist an immutable normalized receipt and recording job before signing.
4. Serialize the recorder nonce; checkpoint signed transaction/hash before broadcast.
   Reuse the existing settlement checkpoint pattern, but keep the dedicated
   recording signer separate from the token-spending settlement signer.
5. Retry the identical signed transaction; on receipt, verify canonical block,
   transaction target/calldata, event, stored payment hash and status.
6. Show payment verified / blockchain pending / recorded separately. A record alone
   must not activate access. Marketplace entitlement integration needs its own
   reviewed design, asset/listing authorization and sale-race/refund handling.
7. Verify reversals from the provider before recording their evidence; retain the
   original record. Partial refunds and dispute-resolution reversals need a later
   explicit state model; this contract only supports full terminal reversals.

No provider-recording API, signer configuration, deployment, public chain write or
entitlement integration is claimed by the standalone contract implementation.
Existing MetaMask purchase events remain the record for existing on-chain purchases.
