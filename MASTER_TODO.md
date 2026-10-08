# DKM master to-do list

Updated 2026-10-09. **Use this as the single working checklist.** It consolidates
PAYMENT_TODO.md, OWNER_HANDOFF.md and the remaining owner dependencies from
ROADMAP_STATUS.md. Those files retain technical background and historical evidence.
Unchecked items are pending; checked engineering items mean locally implemented,
not production certified. No real-money payment or new deployment has been completed.

## Start here: your progress tracker

Start with A1 (Transak staging plus an Onramp.money enquiry), then A2–A3 and A5. A4 is for the coordinated acceptance run. B can proceed
while providers reply. C is optional test-demo setup. D is required before launch.
You do not need to finish every item before telling me your progress.

| Done | Task | What to return to me |
| --- | --- | --- |
| [ ] | A1. Transak staging access + Onramp.money India enquiry | Non-secret reply, supported token/network, fees and sandbox status |
| [ ] | A2. Privy development app and pricing | Public app ID, pricing and recovery/gas requirements |
| [ ] | A3. Hosting and operational choices | Domain, host, support contact, KYB/refund owner |
| [ ] | A5. LI.FI developer access; Relay optional alternative | API access ready, fee settings and supported routes; no secret keys |
| [ ] | A4. Buyer/seller acceptance participation | Availability for a coordinated test run |
| [ ] | B1. Google login credentials | Confirmation configured locally; no secret values |
| [ ] | B2. Encryption backup and RPC key rotation | Confirmation completed; no keys |
| [ ] | B3. Research/submission requirements | Whether QAOA, VQC and rich scoring are required; deadline/rubric |
| [ ] | C1. Optional Razorpay test account and webhook | Test configuration status and public webhook hostname |
| [ ] | C2. Separate Amoy buyer/seller/settlement wallets | Public addresses only |
| [ ] | D1. Production hosting, backups and secrets | Access arrangement, backup destination and restore owner |
| [ ] | D2. Operators, security review and launch budget | Named operators/reviewer and budget approval |

Do not paste passwords, private keys, API secrets or encryption keys into chat.
Keep them in a password manager/local ignored configuration until we configure
production secret storage. Share provider answers and public identifiers only.

## A. Current payment setup — exact steps


### 1. Unblock fiat testing without waiting for Onmeta

- [ ] Open [Transak Partner Dashboard](https://dashboard.transak.com/) and register
  with your corporate email. Their current documentation says staging access is
  immediate after signup; production needs KYB. Do not pretend to be an incorporated
  business if you are a student project: ask support for developer access if required.
- [ ] Select **Staging**, then **Developers**. Store the staging API key and API secret
  privately. Tell me access is ready; do not paste secrets into chat. No new provider
  environment variables have been added yet: I will wire secure configuration with
  the adapter rather than ask you to invent variable names.
- [ ] Leave any additional partner/integrator fee at zero. DKM already earns its fee
  from seller proceeds. Do not enable a second DKM markup in a provider dashboard.
- [ ] Use only the provider's documented sandbox identities/payments in staging.
  Staging may deliver TRNSK test tokens, not DKM MockUSDC. It can test provider order
  handling, but cannot prove our current marketplace settlement or live INR support.
- [ ] At [Onramp.money](https://onramp.money), use the official business/integration
  contact to request sandbox credentials, app ID and current INR/UPI route approval.
  Its docs specify a sandbox, but instant self-service credential access is unverified.
  **Onramp.money and Onramper are different services.**
- [ ] Send the enquiry below to Onramp.money; optionally send it to Transak for live
  India support. Return non-secret replies, fees, enabled token/network and access status.
  Onmeta is now an optional fallback, not a dependency for continuing development.

Copy-ready enquiry (send yourself; no external message has been sent for you):

> We are developing DKM, a knowledge-content marketplace/capstone. Buyers obtain
> access licences and creators retain their NFTs. We need developer sandbox access
> first, then confirmation whether you approve our business model for Indian
> customers paying INR through UPI. Can you deliver native USDC on Polygon PoS,
> chain 137, token 0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359 (not USDC.e)?
> Please confirm eligibility for a student/unincorporated project versus a registered
> entity, API/app-ID access, KYC/KYB, exact payment methods, minimums, fee/spread/tax
> breakdown, quote expiry, net-output guarantees and gas charges. Do you support
> customer embedded wallets or an approved settlement-wallet destination? Please
> provide authenticated order/status/webhook docs, sandbox failure/refund scenarios,
> and responsibility for funds when conversion succeeds but our asset purchase fails.
> Our 5% DKM fee is deducted from seller proceeds, with zero additional DKM buyer markup.

Sources: [Transak access](https://docs.transak.com/guides/how-to-create-partner-dashboard-account),
[sandbox tokens](https://docs.transak.com/guides/sandbox-credentials),
[Onramp sandbox](https://docs.onramp.money/onramp-whitelabel-unlisted/environment/sandbox-environment),
[INR/UPI transaction API](https://docs.onramp.money/onramp-whitelabel-unlisted/whitelabel-onramp-endpoints/create-transaction).

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


### 5. Web3 developer access (no real funds needed now)

- [ ] For the existing LI.FI target, follow its [official partner instructions](https://help.li.fi/hc/en-us/articles/13304987014299-Can-you-share-some-insight-on-the-fees-structure-of-using-LI-FI-for-a-DApp)
  to register and create an integration. Store the API key privately. Keep our
  additional integrator fee at zero; the provider's own fee is separate.
- [ ] If LI.FI access is difficult or we proceed with the separate bridge test,
  open [Relay Dashboard](https://dashboard.relay.link/), choose **API keys**, then
  **Create key**, labelled `dkm-development`. Keep this key backend-only.
- [ ] Tell me which access succeeded. Do not buy crypto or fund mainnet yet.
  I verified Relay's public testnet list on 2026-10-09: Base Sepolia (84532) and
  Sepolia (11155111); Amoy (80002) was absent. A separate Relay bridge experiment
  does not migrate DKM or prove its custom MockUSDC checkout works.

## Provider comparison — checked 2026-10-09

| Candidate | Use and access | Fees and limitations |
| --- | --- | --- |
| Transak | Fastest documented self-service fiat sandbox: staging keys immediately after signup | Live INR/UPI unverified. Staging token differs from DKM. Current public card rate 3.99% + $1, plus possible spread/network costs; this is not a UPI rate or a merchant quote. |
| Onramp.money | Stronger documented INR/UPI candidate; separate sandbox API and mock flows | Quote API breaks out onrampFee, clientFee, gatewayFee and gasFee. Real rates, native token and account approval must be confirmed; sample payloads are not a tariff. |
| Onramper | Aggregator alternative with onboarding/staging keys | Legal entity and subscription requirements make it a lower-priority option for a student prototype. API access can require sales. Do not subscribe just to explore. |
| LI.FI | Existing Web3 target; free integration/API key through partner portal | Official default platform fee 0.25%, plus route costs; confirm actual quote. No Amoy test route. |
| Relay | Web3 alternative with self-service keys and supported testnet bridging | Standard platform fee 0% token bridge/wrap, 0.01% stablecoin, 0.06% major swap, 0.15% minor swap; execution includes $0.02 plus destination gas, with swap/liquidity costs and normally separate source gas. These are components, not all-in prices. |

Do not silently add a provider's own markup and its all-in quote twice. Show the
buyer the reviewed total and separately paid gas. A bridge or funding success is
never proof of the DKM asset purchase. Testnet swap liquidity may be unavailable.

References: [Transak fees](https://transak.com/fees-pricing-calculation),
[Onramp quote fields](https://docs.onramp.money/onramp-whitelabel-unlisted/whitelabel-onramp-endpoints/quote),
[Onramper onboarding](https://docs.onramper.com/docs/getting-started),
[LI.FI fee/access](https://help.li.fi/hc/en-us/articles/13304987014299-Can-you-share-some-insight-on-the-fees-structure-of-using-LI-FI-for-a-DApp),
[Relay key setup](https://docs.relay.link/references/api/api-keys),
[Relay fees](https://docs.relay.link/references/api/api_core_concepts/fees),
[Relay testnets](https://docs.relay.link/references/api/api_guides/testnet),
[live testnet list](https://api.testnets.relay.link/chains).

## B. Earlier account, security and submission tasks

### B1. Enable Google login/signup

- [ ] Open [Google Cloud Console](https://console.cloud.google.com/) and select or
  create your project. Configure the OAuth consent screen with your app identity,
  support contact and test users while in testing.
- [ ] Create an OAuth client of type Web application. Register the exact local
  redirect URI `http://localhost:8000/api/auth/google/callback`.
- [ ] Put `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` and `GOOGLE_REDIRECT_URI` in
  ignored `backend/.env`. Keep the secret out of frontend environment variables.
- [ ] Tell me configuration is ready. We will restart the backend and test signup,
  login, account linking and logout. Production requires a separate matching HTTPS
  callback and `FRONTEND_ORIGIN`; configure those after the domain is known.

### B2. Preserve existing encrypted files and replace the exposed RPC credential

- [ ] Back up the existing `CONTENT_MASTER_KEY` from your local secret configuration
  into secure storage separate from the database. Do not overwrite or regenerate it.
- [ ] Choose a protected database-backup destination and responsible person. A backup
  of the database alone cannot recover encrypted files without the encryption key.
- [ ] In your RPC provider's dashboard, issue a replacement API key for the one
  previously exposed in diagnostic output. Store the replacement in the relevant
  ignored configurations. We will verify connectivity before the old key is revoked.
- [ ] Tell me when ready without sending secret values. Engineering must implement
  key-version migration before encryption-key rotation; this is not a manual overwrite.

### B3. Confirm academic deliverables

- [ ] Tell me whether your submission requires rich coherence/completeness/originality
  scoring and review summaries, QAOA pricing benchmarks, and VQC embedding/NDCG
  comparisons. These are conditional research items, not completed features.
- [ ] Provide the submission deadline, report/demo requirements and assessment rubric.
  We will schedule experiments and report evidence accordingly; results cannot be
  claimed without running the experiments.

## C. Optional existing Razorpay/Amoy demo setup

This is separate from production UPI conversion. Skip this section for now if your
priority is Onmeta onboarding. Razorpay test credentials do not enable real conversion
or establish approval for a crypto/NFT business. Keep settlement disabled until the
compatible marketplace and historical-access migration have been verified.


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


After setup, run from `backend`:

```powershell
venv/Scripts/python.exe -X utf8 check_demo_readiness.py
```

This only checks readiness. It does not deploy, approve, pay or grant access.
Do not change marketplace addresses yourself. Funding and bounded token approval
must target the reviewed deployment after engineering confirms it is ready.

## D. Before production launch — joint work

- [ ] Owner: provide scoped access to the selected frontend/backend hosting projects,
  domain/DNS, database host and secret store. Earlier Oracle/Vercel references are
  possible hosts, not a requirement to buy both or create duplicate projects.
- [ ] Engineering: configure HTTPS, exact allowed origins, production OAuth redirects,
  authenticated provider callbacks and restricted database access.
- [ ] Owner: select backup retention/storage, name the restore operator and arrange
  a maintenance window. Engineering: perform and record an actual restore drill.
- [ ] Owner: name payment-recovery operators. Administrator/engineering: review
  `backend/operator_roles.sql`, provision personal credentials and scoped permissions;
  do not share the development superuser with operators or the web application.
- [ ] Owner: approve a protected contract-owner/signer arrangement and arrange an
  independent application/contract review. Do not reuse the demo signer for production.
- [ ] Engineering: configure secret rotation, signer restrictions, redacted logs,
  restricted log retention, incident alerts, load/abuse tests and production finality.
- [ ] Joint: agree refund/support responsibilities with the provider and approve a
  small real-money test budget only after sandbox, migration and audit readiness.
- [ ] Joint: complete the acceptance evidence below before public launch. No API key
  or passing local test alone means production payments are ready.

## E. Engineering checklist — these are my implementation tasks


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
- [ ] Use Transak for accessible sandbox evaluation and Onramp.money for INR/UPI qualification; Onmeta is optional.
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


### Additional remaining work carried forward

- [ ] Inventory old marketplace listings, auctions, outstanding refunds and buyer
  entitlements; preserve old contract/splitter wiring. Add legacy access/history and
  auction refund/finalization support before switching the active marketplace.
- [ ] Update runtime addresses/ABIs only from verified deployments and retain rollback
  information. Preserve the existing KnowledgeAsset deployment.
- [ ] Complete live encrypted upload -> mint -> listing -> purchase -> download/review
  regression, including existing buyers and both payment routes.
- [ ] Complete indexed auction/lifetime activity and seller net-earnings reporting;
  current paged fixed-price activity is not complete lifetime accounting.
- [ ] Complete consolidated seller listings/reviews/earnings views.
- [ ] Review remaining timestamp findings and Solidity compiler known bugs; test a
  compiler upgrade if appropriate. Existing Slither findings are not an independent audit.
- [ ] Implement conditional research only when its submission requirement is settled;
  produce reproducible comparisons, numerical results and report sections.
- [ ] Prepare final report, screenshots/demo and release evidence after verification.

## F. Pricing rule to preserve

Buyer total = asset price + external payment/conversion/network charges + applicable
taxes on those external charges. **DKM's existing 5% comes from seller proceeds.**
It must not be added again to the buyer's bill. Royalty deductions remain separate.

Illustration only: 100 USDC asset, INR equivalent 9,000, external costs 200 -> buyer
pays 9,200 INR; marketplace receives the full 100 USDC; DKM receives 5 USDC; seller
receives 95 USDC before royalties. If 200 is already included in the provider quote,
do not add it again. Actual rates, spread, taxes and fees require the provider quote.
Unknown charges must block live checkout. Separately paid source gas must be labelled.

## G. Joint acceptance checklist


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


For production provider/LI.FI flows also verify quote expiry and changed totals,
exact native USDC versus USDC.e, wrong destination/network, insufficient gas,
partial bridge delivery, restart/resume, embedded-wallet account recovery and sold
listings during conversion. Provider success never substitutes for on-chain entitlement.

## Progress update template

Copy this when replying; fill only items you have worked on:

```text
Fiat: Transak staging access; Onramp.money reply; fees and supported route
Web3: LI.FI or Relay developer access status (no secret keys)
Privy: public app ID; pricing; recovery and gas information
Google: configured locally / pending
Hosting: domain, backend hostname, hosting provider, support contact
Security: encryption backup done? RPC replacement ready?
Optional Amoy demo: test setup status; public wallet addresses
Research: required items and deadline
Blocked on: error message with all secrets removed
```

## Work continued without owner credentials — 2026-10-09

- [x] Compared alternative provider sandbox access and actual fee documentation.
- [x] Queried Relay public chain discovery without keys or wallet transactions;
  confirmed the listed testnets do not include Amoy.
- [x] Hardened test checkout to refresh server state before opening payment, block
  held/refunded/already-confirmed orders and require review of changed payment details.
- [x] Expanded regression coverage for changed totals/currency/rate/provider identity,
  holds, prior capture and unavailable status lookup. No provider SDK was installed.

This does not remove the backend/provider race boundary: a final status read is
not a reservation or lock against a later capture. Existing order deduplication and
provider verification remain necessary. No production on-ramp is integrated.
