# Payment delivery checklist and owner actions

> 2026-10-09: Onmeta is no longer the first onboarding dependency. Follow MASTER_TODO.md for Transak sandbox, Onramp.money qualification and LI.FI/Relay alternatives; older provider choices below are historical.

> Start with [MASTER_TODO.md](MASTER_TODO.md), the consolidated owner and engineering checklist. This document retains detailed background.

Updated 2026-10-01. This tracks the latest payment requests; ROADMAP_STATUS.md
retains the wider application/security/research roadmap. Checked means implemented
locally, not deployed or independently audited.

## Agreed requirements and engineering checklist

- [x] Preserve welcome -> signup/login -> authenticated application navigation.
- [x] Preserve seller-owned NFTs and buyer access entitlements. Do not silently
  change the product into NFT ownership transfer.
- [x] Document the fee rule: buyer pays asset price plus external costs; DKM's
  existing 5% is deducted from asset proceeds, never added again to the buyer.
- [x] Show that rule on funding and test checkout pages.
- [x] Add explicit review before opening a newly prepared Razorpay test payment;
  show persisted amount/rate and distinguish missing production fees from zero fees.
- [ ] Integrate LI.FI supported EVM token/network discovery and quotes for the
  reviewed production destination. Amoy/MockUSDC remains unsupported.
- [ ] Validate quote chain, exact token, recipient, approval target, calldata,
  minimum received, gas and expiry; require re-confirmation of changed totals.
- [ ] Execute/resume swaps and bridges; track source and destination transactions,
  partial completion and intermediate tokens. Conversion is not purchase success.
- [ ] Evaluate Onmeta staging first, Onramp.money second, for INR/UPI conversion.
  Merchant approval and enabled exact-token routes are still unverified.
- [ ] Integrate authenticated order/status/quote APIs and signed webhooks with
  durable references, duplicate handling and out-of-order event protection.
- [ ] Add embedded wallets tied securely to existing DKM accounts; evaluate Privy.
  Test account linking, recovery, logout, wallet changes and sponsored gas.
- [ ] Persist the accepted quote, fee breakdown, expiry and payment destination.
  Use integer minor/base units and explicit rounding. Never trust frontend prices.
- [ ] Show final payer total and seller proceeds separately. Reconcile provider
  included fees versus additional fees to prevent double counting. Quote enough
  net USDC for the full asset price. Keep source gas paid separately visibly separate.
- [ ] Preserve historical access/listings/auctions/refunds before changing the
  active marketplace. Deploy funded settlement only after migration tests.
- [ ] Complete provider delivery -> purchase -> canonical receipt -> entitlement
  verification. Store opaque order references on-chain, not UPI/KYC information.
- [ ] Define failed-purchase handling, refund responsibility, late captures,
  retries and timeouts. Any exclusive reservation must be enforced by contracts.
- [ ] Test successful purchase, duplicate callback, quote expiry, price change,
  sold listing, wrong token/address, insufficient gas, restart, partial bridge,
  reverted/pending transaction and refund races; then perform controlled live E2E.
- [ ] Production security: scoped secrets, protected signer, logging review,
  restore/load drills and independent contract/application audit.

No real-money provider integration, embedded wallet, mainnet deployment, automated
refund or contract reservation has been completed. Existing Razorpay stays test-only.

## Owner tasks: do these in order

### 1. Obtain Onmeta sandbox access and a written feasibility response

1. Open https://docs.onmeta.in/docs/widget/getting-started/ and follow its staging
   dashboard link (stg.dashboard.onmeta.in). Register a business/developer account.
2. Request staging API access. Keep credentials in a password manager for now;
   do not paste them into chat or add invented environment variables to the app.
3. Use Onmeta's official contact/demo form to send the message below. You send it;
   no message has been sent on your behalf.
4. Return the non-secret reply, enabled routes, fee schedule and sandbox access
   status. We will map the actual credentials into backend-only configuration.

Copy-ready enquiry:

> We are building DKM, a knowledge-content marketplace. Buyers purchase access
> licences; creators retain their NFTs. Indian customers should pay INR by UPI,
> with settlement in native USDC on Polygon PoS (chain 137), token
> 0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359. Do you approve this business model?
> Can our merchant account currently receive that exact token, rather than USDC.e
> or USDT? Can delivery go to a customer's embedded wallet, or an approved
> settlement wallet that calls our marketplace contract? Specify KYC/KYB,
> destination ownership requirements, transaction limits, UPI availability,
> fee/tax breakdown, exchange spread, quote expiry, net received guarantees,
> gas costs, refunds after conversion, failed purchases and support SLA.
> Please supply sandbox access and authenticated quote/order/status/webhook docs.
> DKM deducts its platform fee from seller proceeds; customers pay external costs.

If unavailable, send the same enquiry through https://onramp.money and request
access to their documented INR/UPI -> USDC flow. Do not open multiple paid plans.

### 2. Prepare embedded-wallet access

1. Read https://docs.privy.io/wallets/connectors/usage/connect-or-create.
2. Create a development app through Privy's official dashboard link.
3. Request the applicable pricing for active wallets/users and sponsored gas,
   recovery/export options, and integration with our existing account login.
4. Share only the public app identifier, pricing and approved origins information.
   Keep app secrets private. We will configure origins and secret injection during
   integration; do not replace the existing login database yourself.

### 3. Supply operational choices

1. Provide the intended production domain, backend hostname and hosting provider.
2. Name the person/business responsible for provider KYB and customer refunds.
3. Provide the preferred support email and approve a maximum test-spend budget
   before any real-money acceptance run. No funds are needed for the local changes.
4. Preserve the encryption-key backup. Follow OWNER_HANDOFF.md for existing Amoy
   test wallets, key rotation and optional Razorpay test setup; that setup is not
   a prerequisite for Onmeta research or approval and does not enable conversion.

### 4. Participate in the acceptance run after engineering readiness

Connect your test buyer/seller wallets and approve test signatures when the
application is ready. Supply provider sandbox access securely and perform test
payments/refunds using the provider's test instructions. Do not send real funds
to Amoy. Do not change marketplace addresses or deploy contracts yourself to
unblock the UI; historical-access compatibility remains engineering work.

## Fee acceptance example (illustrative, not provider pricing)

100 USDC asset at quoted INR equivalent 9,000; external charges 200; buyer total
9,200 INR. Marketplace receives the full 100 USDC; existing fee takes 5 USDC;
seller receives 95 USDC before royalties. If the provider's 9,200 quote already
includes the 200, never add it again. Actual fee/tax/spread values come from live
quotes and merchant terms, not this example. Unknown fees must block live checkout.

## Verification

Run from frontend: `node --test tests/checkoutReview.test.mjs` and
`node_modules/.bin/next.cmd build`. Existing purchase safety checks:
`npm run test:purchase`. Live provider and wallet acceptance remains pending.
