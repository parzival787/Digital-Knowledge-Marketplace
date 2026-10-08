# DKM handoff: completed work and owner actions

> 2026-10-09: Onmeta is no longer the first onboarding dependency. Follow MASTER_TODO.md for Transak sandbox, Onramp.money qualification and LI.FI/Relay alternatives; older provider choices below are historical.

> Start with [MASTER_TODO.md](MASTER_TODO.md), the consolidated owner and engineering checklist. This document retains detailed background.

Updated 2026-09-30. This is an operational handoff, not a production certification.

## Completed in this continuation

- Added `/funding` and Add USDC links from navigation, fixed-price assets and auctions.
  India/INR funding is visibly unavailable; there is no provider redirect, invented
  quote or alternative-country fallback. Account/wallet details stay behind auth.
- Fixed-price purchases re-read the listing ID, price, active asset and entitlement
  at one fresh block before approval, and again before the purchase signature.
  A changed price/listing requires the buyer to refresh and review it.
- Approval, purchase and auction transactions estimate gas against current fee data
  and native balance, with a 20% fee margin. The UI explains Amoy POL requirements.
  Network fees can still change after estimation; this is not a fee guarantee.
- Buyer purchases and auction transactions wait for two test confirmations and
  verify receipt/block consistency. Replaced, reverted, disappeared or reorganized
  receipts do not produce a success message. Fixed-price purchases recheck access.
  A pending transaction link is retained so the buyer can inspect it before retrying.
- Added `frontend/tests/purchaseSafety.test.mjs` using Node's built-in test runner.
  These are simulated chain boundary tests, not a live network reorg experiment.
- Added a read-only `backend/check_demo_readiness.py` which does not sign or expose
  secrets, and a least-privilege operator role SQL template. Recovery attribution
  now uses SESSION_USER, retaining the personal login through SET ROLE.

## Latest payment owner actions (2026-10-01)

Start with PAYMENT_TODO.md for the current Onmeta/Onramp, embedded-wallet and fee
requirements, exact account steps and copy-ready provider enquiry. The Razorpay
steps below are optional Amoy demonstration setup only, not a production conversion
solution. No provider credentials or approval have been obtained by this change.

## Existing Amoy demonstration setup

1. **Razorpay test setup:** create test API credentials in your own account. Put
   `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` and an explicit
   positive `RAZORPAY_TEST_INR_PER_USDC` test rate in ignored `backend/.env` locally.
   Do not paste secrets into chat. Keep `SETTLEMENT_ENABLED=false` until deployment,
   signer funding and approval are verified. No live Razorpay key is accepted.
2. **Public webhook URL:** provide a stable HTTPS backend hostname or a controlled
   test tunnel. Register `https://YOUR_BACKEND/api/payments/webhook/razorpay` for
   `payment.captured`, using the same webhook secret as the backend. A provider
   cannot call your localhost. Do not expose a development server publicly without
   reviewing its network access and TLS setup.
3. **Dedicated test signer:** create a separate Amoy-only settlement wallet. Store
   its private key in the local backend secret configuration. Supply its public
   address for funding; never paste the private key. Fund it with Amoy test POL.
   Fund the exact deployed MockUSDC contract used by the marketplace and approve
   only the reviewed new marketplace, with a bounded allowance for the demo.
   Buyer and seller demo wallets also need test POL for their own transactions.
4. **Wallet participation:** be available to connect/verify buyer and seller wallets
   and approve the requested test transactions. Browser wallet approvals and
   provider-account setup cannot be replaced with simulated unit tests.
5. **Preserve the encryption key:** securely back up the current CONTENT_MASTER_KEY
   separately from the database. Do not generate a replacement over the existing
   value. Rotate the RPC API key previously exposed in a local diagnostic, and put
   the replacement into the appropriate ignored configurations.

Observed read-only preflight: Amoy RPC connects, existing Marketplace bytecode is
present and its registry matches. Funded-settlement interface is still unavailable.
Razorpay credentials/webhook secret, test quote and settlement signer are missing.
The content-encryption key is present and valid. A deployer key exists locally;
its presence alone does not validate funding, ownership or migration safety.

Run from backend after setup:

```powershell
venv/Scripts/python.exe -X utf8 check_demo_readiness.py
```

This command reports configuration/chain checks only. It does not deploy, mint,
approve, capture money or certify end-to-end purchase success.

## Deployment work still on the engineering side

Do not simply overwrite the active Marketplace address. The current frontend,
reviews, activity and download access checks target one marketplace; a new contract
has a different entitlement/history store. A compatibility rollout remains necessary
before making the new marketplace the default. This is engineering work, not a
request for you to edit addresses by hand.

The rollout must preserve KnowledgeAsset and MockUSDC, keep the old marketplace
and its RoyaltySplitter intact, and deploy a separate new splitter/marketplace.
Do not repoint the old splitter while old listings/auctions still use it. Inventory
old listings, auctions, outstanding bid refunds and entitlements at a recorded block.
Add/test legacy entitlement lookup and visible access to old marketplace activity,
auction finalization and bid refunds before switching the default marketplace.
Sellers must explicitly cancel/relist where required; no silent ownership transfer.
Check both old and new purchaser downloads/reviews after the switch. Retain old
addresses for rollback and never replay a payment against a different deployment.

The existing deployment script reuses registry/token and creates a new splitter,
but it does not solve application-level legacy reads. No deployment or address
switch was performed in this continuation. Contract migration, live Web2 E2E and
recovery drills remain open until the compatibility work and setup above are ready.

## Acceptance run once deployment and credentials are ready

Record transaction/order references in a restricted test report, not secrets.
Use only Razorpay test payments and Amoy test tokens.

| Scenario | Evidence required |
| --- | --- |
| Successful Web2 demo | Login, wallet proof, test capture, webhook/API verification, durable signed settlement, two-block receipt, hasPurchased, encrypted download, purchaser review |
| Repeated capture/callback | Same persisted order, one settlement transaction, no duplicate entitlement/payment |
| Hold/resume | Operator identity/reason, held order cannot settle, reviewed resume keeps original transaction |
| Pending/timeout | Hash/raw transaction retained, review threshold reached, no automatic replacement/refund |
| Mined revert | Depth/identity checked, operator resume, one explicitly authorized replacement |
| Full test refund | Hold first, rule out chain settlement, operator dashboard refund, processed provider verification, local REFUNDED record, all future settle calls blocked |
| Reorg/disappearance | No success until canonical receipt/depth and entitlement agree; retain transaction reference |
| Legacy buyer | Existing old-market entitlement still downloads and can review after rollout |
| Auctions | Browse/create/bid/outbid/withdraw/finalize/completed-history on both relevant deployments |

Two Amoy blocks are only a demonstration rule. Production finality must be reviewed
for the chosen network and RPC; the local mocked reorg tests are not that sign-off.

## Production decisions and access you must supply

- Obtain provider business/KYB approval and written confirmation for Indian residents,
  INR payment methods, knowledge-content purchases, native USDC delivery, fees/limits,
  gas funding and support/refund responsibilities. Use the acceptance criteria in
  PRODUCTION_PAYMENTS.md. Provider selection and legal approval cannot be inferred
  from a logo or a generic availability page. No provider-specific adapter is built
  before this approval, as requested in the roadmap.
- Proposed target: Polygon PoS, chain 137, native Circle USDC
  `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359`, POL gas, subject to provider support and
  deployment review. This proposal is not loaded into runtime configuration.
  Verified against [Circle's contract list](https://developers.circle.com/stablecoins/usdc-contract-addresses)
  and [Polygon network documentation](https://docs.polygon.technology/pos/reference/rpc-endpoints).
  Amoy continues using the existing project MockUSDC, not Circle's test token.
- Provide hosting/project access, production domain and an approved secret store.
  Inject separate scoped provider, RPC, database and content keys into the backend
  through the host secret manager. Frontend bundles must never receive them.
  Production buyers sign ordinary purchases; omit the Amoy treasury signer from
  ordinary production purchase services. Keep contract-owner powers in a separately
  reviewed hardware-wallet/multisig policy.
- Identify real operators and provision personal database credentials/certificates.
  An administrator reviews/runs `backend/operator_roles.sql` after schema setup,
  creates individual logins, grants database CONNECT and group membership, and
  provisions credentials through the secret store. Do not share the development
  superuser or grant this role to the public web service. The template assumes the
  public schema; adapt it before use elsewhere. No real operator accounts were made.
- Arrange independent contract/application security review, a production restore
  exercise, and load/abuse testing against the actual hosting configuration.

## Observability and support procedure

Use order/transaction references with the authenticated account lookup; never log
passwords, cookies, signatures, raw signed transactions, private keys, provider tokens,
full RPC URLs, file encryption envelopes or document plaintext. Disable raw access
query-string logging at the app and proxy (Google callback URLs contain codes).
Disable development traceback pages. Restrict log access and retention to the
approved deployment policy. Environment injection and this runbook do not constitute
an actual production logging/secret-store deployment.

Daily/operator incident query (restricted DB role; no customer content/keys):

```sql
SELECT status, recovery_status, COUNT(*) AS orders,
       MIN(created_at) AS oldest_order, MAX(updated_at) AS latest_update
FROM payment_orders
WHERE status <> 'ENTITLEMENT_GRANTED' AND recovery_status IS DISTINCT FROM 'REFUNDED'
GROUP BY status, recovery_status;
```

Escalate a new REVIEW_REQUIRED payment, growing unsettled backlog, worker/RPC outage,
or verified chain transaction without entitlement. A support person verifies account
ownership before discussing order details. Wrong network: switch to the configured
network, never accept the same token symbol on another chain. Low gas: add the native
gas token, not more USDC. Funding succeeded but asset unavailable: USDC stays in the
buyer's wallet; do not claim a failed funding transaction or reserve the asset.
Pending/reorg: preserve hashes and re-query canonical status before another payment.
Mismatch: hold and reconcile provider, wallet, chain/token and amount independently.
Refunds follow the operator procedure in PRODUCTION_PAYMENTS.md, never a timer.

## Current boundaries

The newly added funding page is an honest unavailable state, not a completed on-ramp.
Mainnet deployment, production secrets/roles/alerts, provider approvals, live test
payments, migration compatibility and independent audit remain incomplete. No money
was moved and no historical entitlements were changed by this continuation.

## Verification for this handoff

- 29 backend unittest cases pass, including operator privilege and audit attribution.
- Three frontend test groups pass for listing/gas/receipt failure conditions.
- Frontend production build, type checking and lint pass (existing optional
  pino-pretty warning). Run `npm run test:purchase` with Node 24 for the new tests.
- Browser inspection verified the funding unavailable message and five live Amoy
  asset cards with the crypto purchase label, POL guidance and funding links.
- `/api/auth/me` correctly returns 401 logged out; capabilities returns 200.
- Live RPC preflight was read-only. No wallet signing, provider capture, refund,
  deployment, production role provisioning or mainnet change was performed.
