# Production payments and recovery decision

> 2026-10-09: Onmeta is no longer the first onboarding dependency. Follow MASTER_TODO.md for Transak sandbox, Onramp.money qualification and LI.FI/Relay alternatives; older provider choices below are historical.

Prepared 2026-09-30 following the owner's instruction to choose the production model.

## Current direction (2026-10-01)

The latest owner requirements and actionable checklist are in PAYMENT_TODO.md.
Use LI.FI for supported crypto routes; evaluate Onmeta first and Onramp.money
second for INR/UPI, subject to merchant approval and the exact native USDC route.
Evaluate embedded wallets so UPI buyers need not install or manage MetaMask.
The earlier explicit wallet-funding flow below is a recoverable interim design;
a combined purchase is the target, not an implemented feature. Wallet recovery,
provider destination rules and transaction sponsorship must be verified first.

Buyer total = asset price + external payment/conversion/network costs and applicable
taxes on those costs. The existing DKM fee is seller-paid out of asset proceeds.
Never add it to the buyer total or double-count provider fees included in a rate.
Persist and review an authenticated live quote before paying; missing fees are
unknown, not zero. The current fixed Razorpay test quote has no production fee model.

Evidence: [Onmeta checkout](https://onmeta.in/checkout),
[merchant token availability](https://docs.onmeta.in/docs/api/fetch-tokens/),
[Onramp transaction API](https://docs.onramp.money/onramp-whitelabel-unlisted/whitelabel-onramp-endpoints/create-transaction),
[Privy wallets](https://docs.privy.io/wallets/connectors/usage/connect-or-create).
Onmeta advertises USDT/USD checkout and mentions USDC use cases; native Polygon
USDC must be confirmed from the merchant's supported-token list. Razorpay's
[terms section 2.13(5)](https://razorpay.com/terms/) restrict crypto/NFT activity;
adding a converter does not establish approval. Keep Razorpay test-only.

## Earlier decision and interim flow

Target a provider-operated fiat on-ramp that delivers USDC directly to the buyer's
verified wallet. The buyer then approves and buys through the marketplace. Keep
funded Razorpay -> MockUSDC settlement restricted to the Amoy demonstration.
DKM should not launch an INR collection/treasury conversion business as the default.

This is a design decision, not an integrated or approved production service. No
provider has been contracted, no INR has been exchanged, and no mainnet address
has been selected. Production INR checkout remains unavailable.

The initial production UX will have two explicit steps:

1. **Add USDC:** provider checkout shows INR amount, fees, USDC amount, network,
   destination wallet, quote expiry and refund terms. The provider handles identity
   checks and conversion under its approved service terms. DKM stores the provider
   reference and minimum necessary order data, not identity documents or card data.
2. **Buy asset:** refresh listing availability and exact USDC price. The buyer
   authorizes approval and purchase from their wallet. Confirm the canonical chain
   receipt and marketplace entitlement before enabling the protected download.
   Native gas funding must be available and disclosed before the user buys USDC.

If the asset becomes unavailable, the USDC remains in the buyer's wallet. Funding a
wallet does not reserve or buy the asset. Do not display "purchase complete" on a
provider callback. A combined checkout may be considered later only when a provider
explicitly supports this contract's entitlement semantics, execution and failure
recovery. An NFT product name alone does not establish that compatibility.

## Provider selection evidence and acceptance criteria

Transak is a candidate, not the selected INR supplier. Its current public coverage
page did not list India when checked on 2026-09-30. This does not establish that
India can never be supported; it means INR/India support is unverified and cannot
be advertised. Written partner confirmation and runtime country/currency/network
availability checks are prerequisites. Do not bypass restrictions by selecting
another country or currency.

Before implementing a provider-specific production adapter, obtain confirmation of:

- DKM's business entity, knowledge-content marketplace use case and customer regions.
- Indian resident eligibility, actual INR payment methods, limits and onboarding.
- Exact native USDC token and network, including fees, minimums and gas provisioning.
- Direct delivery to the buyer's proof-verified wallet and policy for wallet changes.
- Quote expiry, failure/refund ownership, service support and reconciliation access.
- Authenticated server order creation and status lookup, signed event validation,
  replay handling, retries, duplicate-charge protection and test scenarios.
- Applicable provider approval and independent legal/compliance review for launch.

Transak documents that production webhook registration requires KYB approval, and
that on-ramp completion means crypto was sent to the user. Neither is evidence of
DKM purchase entitlement. Keep provider funding and marketplace purchase records
separate, linked to one user and verified wallet. Verify order ID, customer,
network, token, destination and received amount server-side; never trust a widget
success message. Duplicate and out-of-order events must not regress terminal state.

Sources checked: [coverage](https://transak.com/global-coverage),
[webhooks](https://docs.transak.com/features/webhooks),
[public API discovery](https://docs.transak.com/api/public/end-points).

## Current Amoy payment recovery implementation

The existing seven payment states remain intact. `recovery_status` is a separate
hold/refund flag so the original chain state and signed transaction are retained.

- Settlement attempts are separated by at least 30 seconds across processes and
  browser requests, using the existing database signer lock.
- After 20 attempts or 15 minutes from the first attempt, whichever comes first,
  settlement enters `REVIEW_REQUIRED`. A mined revert also enters review.
- Checkout and the dashboard display the hold and suppress settlement retries.
  Background reconciliation skips held orders. No second payment is requested.
- A signed transaction is never erased because of a timeout. Pending transactions
  continue to block new nonce allocation, including while held for review.
- Operators may resume a held order after investigation, resetting the retry budget
  while preserving its transaction. A reverted transaction is replaced only after
  the existing settlement check again proves the revert.
- Full refunds are operator-reviewed. The tool never initiates a refund or sends a
  transaction. It verifies a refund already processed by Razorpay test mode, including
  payment/order identity, currency, full original amount and provider status.
- Refund recording fails closed if the order is settled, entitled, unverified,
  or its signed transaction is pending/unknown/successful. A stored signed transaction
  requires a matching hash and a mined revert at the current two-block test policy.
- A recorded refund prevents all future settlement attempts. Actions are recorded
  with timestamp, database actor and an operator reason. Use individual operator DB
  roles in production; a shared development DB login is not individual attribution.

The numerical retry policy above is implemented for the test system. Production
confirmation depth, support SLA and provider retry timing need a deployment-specific
review. Two-block test confirmation is not a mainnet finality guarantee.

## Operator procedure

Run from `backend` on a restricted operator host after normal schema initialization:

```powershell
venv/Scripts/python.exe payment_recovery.py list
venv/Scripts/python.exe payment_recovery.py hold --order ORDER_ID --reason "Investigating captured payment without entitlement"
venv/Scripts/python.exe payment_recovery.py resume --order ORDER_ID --reason "Listing and funding checked; retry approved"
venv/Scripts/python.exe payment_recovery.py record-refund --order ORDER_ID --refund-id rfnd_EXAMPLE --reason "Full test refund processed and independently checked"
```

For refund handling, hold first and keep the order held throughout. Confirm no
settlement transaction was signed, or verify its final mined revert, **before**
initiating any provider dashboard refund. If pending/unknown, investigate nonce and
chain state; absence from one RPC is not proof of failure. Do not refund on timeout.
Use a second operator to check provider payment ID and amount before issuing the
full refund in the provider dashboard. Then record its processed refund ID with
the command above. If the tool fails, retain the hold and reconcile; do not issue
another refund. Never resume an order while a provider refund is requested/pending.

The CLI requires database credentials and is intentionally not a customer-facing
admin endpoint. Keep its host restricted. The application never automatically
issues money-moving refunds. Provider dashboard activity must be correlated with
local recovery events during review.

Refund policy for this test design: verified captured payment without deliverable
entitlement is eligible for a full refund to the original payment method after
settlement is ruled out. No partial refund or alternate-wallet refund is supported.
Provider processing times apply; do not promise immediate receipt.

Razorpay verification reference:
[fetch refund by ID](https://razorpay.com/docs/api/refunds/fetch-with-id/).

## Reservations and timeout boundaries

There is currently no exclusive listing reservation. Database checkout deduplication
is account-scoped and cannot prevent a direct on-chain buyer or seller cancellation.
A UI timer or database lease must never be presented as an exclusive reservation.
The selected wallet-funding model avoids charging for an asset during an on-ramp
wait. Revalidate the listing immediately before the buyer signs the purchase.

For the existing demo, a failed/unavailable listing after capture follows review
and refund reconciliation above. An abandoned unpaid provider order remains
resumable; a locally elapsed timer must not hide a late capture or produce a second
charge. A future single-step fiat purchase would require contract-enforced
reservation/expiry and a separately audited late-capture refund path before launch.
No such reservation contract is implemented in this change.

## Production release evidence still required

Approved provider and supported geography; authenticated provider sandbox E2E;
mainnet chain/token and contract review; finality/reorg tests; secret manager and
signer policy deployment; independent audit; actual restore/load drills; restricted
operator roles; production observability and customer support process. Existing
Amoy test guards must not be removed as a shortcut to launch.

## Existing cryptocurrency funding (Web3)

The owner requested payment from existing crypto holdings, including ETH, rather
than having to separately obtain the marketplace currency. Select LI.FI as the
swap/bridge integration target. This is separate from the INR provider choice.
It is NOT installed or enabled in the current demo. Official LI.FI documentation
states that testnets are no longer supported, so Amoy/MockUSDC cannot be given a
working route by adding more wallet networks or a token dropdown.

Production flow: source crypto -> supported swap/bridge -> native USDC in the
account's verified wallet -> current listing validation -> buyer approval/purchase
-> canonical receipt and entitlement. For example, ETH on Ethereum could fund USDC
on Polygon when a valid route and supported deployment exist. The marketplace
continues settling in one token. Conversion success is wallet funding, never asset
purchase, auction reservation, bid placement or entitlement.

Initial scope should match the existing EVM wallet integration: discover supported
source EVM chains/tokens dynamically and display only routes the provider can quote.
Never promise every cryptocurrency; illiquid tokens, unsupported chains and small
amounts can have no viable route. Native Bitcoin/Solana purchases would also need
appropriate wallet connectors, source signing/status handling and separate tests.
Do not silently treat wrapped BTC as native BTC or reuse an EVM address as a
non-EVM receiving address.

The quote review must display source chain/token/amount, destination chain and exact
native USDC contract, verified recipient, expected and minimum received amounts,
provider/bridge fees, source gas, destination gas provision, slippage and validity.
Use the provider's gas-refuel support where available and verify actual POL/USDC
balances after completion. If gas cannot be delivered or sponsored, disclose that
before accepting the route. Buying USDC alone does not guarantee gas for a later
purchase. Source execution still needs source gas unless a supported relayed route
explicitly covers it; no blanket gas-free claim.

Before enabling execution: reviewed production deployment/legacy access migration;
provider route and allowance validation; exact bounded token approval; wallet/network
binding; quote expiry and re-quote on changes; durable source/destination references;
restart/resume and partial-bridge failure handling; canonical destination balance
verification; updated listing check and independent purchase confirmation. Never
forward unvalidated provider calldata, accept a user-supplied destination override,
or mark provider COMPLETED as a purchase. A route may deliver an intermediate token
if destination execution fails; surface the actual outcome and support recovery.

Current implementation only adds a clearly unavailable crypto-funding entry in the
signed-in UI. No SDK, executable quote endpoint, chain switch, approval, transfer,
mainnet deployment or crypto conversion was added. Integration execution remains
blocked on the supported production deployment; this is not a completed payment route.

Sources checked 2026-10-01:
[LI.FI quote API](https://docs.li.fi/api-reference/get-a-quote-for-a-token-transfer),
[testnet limitation](https://help.li.fi/hc/en-us/articles/11825798974107-How-can-I-test-my-integration-with-your-protocol-API-Widget-SDK-via-Testnets),
[gas funding responsibilities](https://help.li.fi/hc/en-us/articles/13304979742363-Who-pays-for-gas-cost-on-the-source-and-destination-chains).
