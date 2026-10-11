# DKM continuation — 2026-09-30

## Current continuation (2026-10-11; supersedes stale blocker notes below)

The PDF baseline and active draft PR #1 at 6612caf were verified against GitHub
and local git. Continue codex/dkm-payment-persistence; preserve unrelated changes.
ENGINEERING_PLAN.md now orders the latest 19-phase local-demo brief;
HUMAN_ACTION_REQUIRED.md isolates real human dependencies. Embedded wallets and
research are conditional, not mandatory blockers without the rubric.

The existing /api/capabilities now models fixed-price, auctions, Transak BUY/SELL,
Razorpay test, unverified UPI, unsupported crypto routes and pending audit registry.
Read-only deployment wiring checks gate purchase availability. Frontend purchase,
auction, funding and payout controls consume server capability state; mismatched
market/token/network or failed checks fail closed. Per-transaction checks remain.
No deployment or token transfer was performed. TEST_EVIDENCE.md records current
baseline and milestone results. All other remaining engineering stays open.

Fixed-price wallet checkout now persists a five-minute account-bound quote from
deployed listing/splitter state, using integer base units and Solidity rounding.
UI shows seller gross, platform deduction, royalties and net; there is no extra
buyer DKM fee. Acceptance rechecks terms, expiry, wallet and old/new entitlements
before approval and again before purchase. Funding/FX/payout costs remain explicitly
unquoted. This is not a reservation or an atomic on-chain expected-price guard.

The full capstone roadmap is still unfinished. Earlier handoff documents described
an in-memory mock payment service; this checkout extends that implementation.

## Project rules

- Preserve FastAPI/asyncpg/pgvector, Next.js/wagmi/RainbowKit, Pinata, BLAKE3,
  384-dimensional embeddings and Polygon Amoy.
- Work on a feature branch. Never edit/push directly to main. Open a PR whenever
  changes are pushed. Merging requires the user's approval.
- Creator retains the NFT. Marketplace entitlement controls access. Neither mock
  nor provider confirmation alone grants entitlement.
- Preserve pre-existing user changes in llm_enrichment.py and the separate
  untracked directory named `contracts ` (with a trailing space).

## Current deployment

Read-only RPC checks confirmed chain 80002 and reciprocal Marketplace/splitter wiring:

| Contract | Address |
| --- | --- |
| KnowledgeAsset | 0x2C16409A3db9880f9A70e71B5b131A17db533Fc9 |
| MockUSDC | 0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719 |
| Marketplace | 0xDe7bdacb8B3ff631dbcdb09C81c0de7421475A5d |
| RoyaltySplitter | 0x43cE72CEd667bDe9252044451b07ecA1aec2D300 |

The ignored backend .env was corrected from the older Marketplace address to the
one above. Restart existing backend processes to load that change. No contracts
were redeployed. The new buyAssetFor source is NOT deployed.

An empty-recipient listing simulation for token 1 hit its existing-listing guard;
that alone does not prove deployed empty-recipient behavior. Local tests prove
empty-recipient funded purchases and royalty payouts.

## Implemented in this branch

- PostgreSQL payment_orders, timestamps, unique provider IDs/hash, persistent
  create/get/confirm, per-order confirmation locks and repeat-safe callbacks.
- Wallet validation and database-authoritative prices. Existing DB prices are
  whole USDC despite the old handoff claiming base units. Settlement multiplies
  by 1,000,000 and rejects any mismatch with the listing. No price migration.
- Razorpay TEST keys only: configured fixed INR test quotes, checkout HMAC,
  captured-payment API verification, exact order/amount/currency checks, raw-body
  webhook signatures. Authorized-but-not-captured stays pending.
- Funded buyAssetFor: payer supplies full USDC and royalties; buyer receives
  entitlement. Payer-scoped payment references prevent replay. No free entitlement
  setter. Existing buyAsset shares the same purchase implementation.
- Backend settlement saves signed transaction/hash before broadcast, reuses it
  after interruption, serializes the dedicated signer across workers, checks
  transaction identity and two-block confirmation depth, then verifies entitlement.
  Raw signed transactions are excluded from public PaymentOrder output.
- SETTLEMENT_ENABLED=true starts reconciliation. Mined reverts retain their hash
  and require explicit retry; background work will not repeatedly spend gas.
  Mock orders cannot settle.
- Frontend sale filters, auction create/bid/countdown/finalize/refund controls,
  listing-price tuple decoding, network switching, balance/allowance checks,
  transaction retry recovery, entitlement display, Razorpay test checkout/status
  and saved-order resume. Shared navbar/wallet controls on every page.
- Ownership-transfer tests now assert creator ownership and buyer entitlement.
  Health checks Pinata. Requirements include installed packages used by the app.

## Verified

- Live mock API create/get/confirm/get and repeat confirmation passed.
- 9 backend tests pass against disposable PostgreSQL schemas. Provider/chain
  boundaries are simulated; these are not live Razorpay/Amoy settlement tests.
- 121 local Hardhat tests pass; contract TypeScript checking passes.
- Frontend production build/typecheck/lint pass. WalletConnect emits a non-fatal
  optional pino-pretty warning. Existing FastAPI on_event usage is deprecated.
- Browser rendered five live Amoy assets with correct prices; filters and the
  disconnected-purchase guard passed. Wallet-signing flows were not exercised.

## Next work and blockers

1. Review/deploy settlement support while preserving existing listings and buyer
   entitlements. Plan historical entitlement lookup/migration before switching
   Marketplace. Preserve KnowledgeAsset and MockUSDC.
2. Configure a dedicated SETTLEMENT_PRIVATE_KEY, test USDC funding/allowance, POL,
   Razorpay test keys, webhook secret and explicit INR test rate. None of the
   provider/signer settings were present. See backend/.env.example. Preflight
   refuses checkout against the old deployed contract.
3. Live provider capture/webhook -> funded settlement -> access E2E. Reconcile or
   refund fiat orders if a listing sells/cancels before settlement. Production
   treasury, automated refunds and listing reservations are not implemented.
4. Combined swap/bridge-and-buy: user delegated provider choice. LI.FI is the
   candidate for destination calls but no longer supports testnets. No fake Amoy
   bridge or unverified quote integration was added. A supported deployment,
   liquidity and reviewed destination integration are required. Keep mainnet
   migration gated on security/E2E verification.
5. Upload Form binding, returned vector ID, correct/authenticated mint-token link,
   search UI, protected/encrypted download, reviews and dashboards remain. Public
   IPFS files are not protected by a UI entitlement check.
6. Historical auction lookup after page reload remains: tokenToAuction clears
   when finalized. The UI retains the ID during in-session finalization only.
7. QAOA/VQC/Lit/Kyber experiments, audit, production deployment and final report,
   screenshots and demo submission remain later milestones.

## Verification commands

From backend: `venv\Scripts\python.exe -m unittest tests.test_payments -v`

From contracts: `node_modules\.bin\hardhat.cmd test` and `node_modules\.bin\tsc.cmd --noEmit`

From frontend: `node_modules\.bin\next.cmd build`

References: [Razorpay](https://razorpay.com/docs/server-integration/python/test-app/),
[LI.FI destination calls](https://docs.li.fi/api-reference/perform-multiple-contract-calls-across-blockchains-beta),
[LI.FI testnet limitation](https://docs.li.fi/sdk/testing-integration).


## Account and feature coverage continuation

See FEATURE_COVERAGE.md for the complete API-to-page map and security boundaries.
Added username signup/login/logout, hashed database sessions, signed wallet binding,
account-scoped uploads/orders, search, dashboard, account and service-status pages.
Minting now uses multipart metadata and the real stored vector ID, verifies the mint
receipt and securely links content/creator/price. Dashboard supports upload recovery.
Checkout resumes from server state across browsers. Dedicated auctions page includes
completed auctions; sellers can cancel fixed listings. Shared navigation works on
small screens. Existing unowned rows require a reviewed migration, never auto-claim.
These changes supersede the earlier notes about missing search/dashboard/upload
binding and historical auction visibility. Live fiat, bridge and encrypted storage
blockers remain. Auth tests plus payments: 14 pass; frontend build passes.

## Google and payment verification continuation

Google authorization-code login/signup with browser-bound state and PKCE is added;
credentials are absent, so the option is visibly disabled until configured. Login
and signup use a standalone layout without marketplace navigation. Asset details
allowlist readable catalog fields and fetch descriptions through the backend;
new uploads save summaries. Legacy descriptions may be unavailable.
Fiat checkout creation is serialized per account/asset to prevent duplicate orders.
19 auth/payment tests, 121 contract tests, frontend build and the document/search
pipeline passed. Read-only RPC still confirms funded settlement is not deployed.
Razorpay is a test INR gateway; no INR-to-USDC converter is integrated. Settlement
requires pre-funded test USDC. See PAYMENT_AUTH_VERIFICATION.md for setup and limits.

## Roadmap audit continuation

ROADMAP_STATUS.md now maps all 44 supplied items: 25 implemented/local, 9 partial,
7 external rollout/E2E pending and 3 conditional research. Added PostgreSQL-backed
duplicate detection with concurrent insert rejection; purchaser-only reviews;
quality search filter; bounded fixed-price account activity; encrypted new files
and revalidated downloads. Legacy public files and deployments remain unchanged.
24 backend tests and frontend build pass. Live history RPC succeeded after honoring
the current 10-block log-query limit. Complete earnings/auction indexing remains.
CONTENT_MASTER_KEY was initialized in ignored backend/.env with init_content_key.py;
back up securely and never overwrite for rotation without a key migration. No
secret is committed. See audit report for diagnostic RPC-key rotation follow-up.
The new services use existing cryptography (now explicitly in requirements), AES-GCM
per-file keys and backend key wrapping, not Lit or post-quantum encryption.
Slither is now available via isolated uv tooling. Payment effects were moved before
external calls and royalty sum locals initialized. Final scan: 4 low timestamp and
1 informational compiler-version finding; zero high/medium. 121 contract tests and
TypeScript checks pass. See SLITHER_AUDIT.json and ROADMAP_STATUS.md for triage.
Solidity interfaces/addresses are unchanged; the source changes are not deployed.
Frontend Marketplace ABI was missing deployed hasPurchased/purchaseCount reads;
these were added so entitlement-dependent UI can resolve. Funded methods remain
deployment-gated in the backend.

## Production payment decision and recovery continuation

The owner delegated the production model choice. PRODUCTION_PAYMENTS.md selects
provider-operated on-ramp delivery to the buyer wallet followed by an explicit
marketplace purchase. Transak remains a candidate only: India/INR support was not
verified from current official coverage. No production converter is integrated.
Added durable review holds after 20 attempts/15 minutes, 30-second retry spacing,
operator hold/resume/full-refund verification CLI, audit events and frontend
review/refund labels. Mined reverts require receipt depth/identity before retry.
No refund is submitted by the tool. Unknown/pending/successful chain transactions
cannot be recorded as refunded. Amoy/test-key guards remain.
Production provider approval, contract-enforced reservation, independent audit,
production security deployment and research items remain outstanding. This payment
preparation does not mark the entire remaining roadmap complete.

## Funding UX and operational readiness continuation

Added /funding with explicit unavailable India/INR state, account wallet display,
gas guidance and links from fixed-price/auction/navigation. No provider adapter or
quote is fabricated. Purchases refresh listing/price/active/access before approval
and immediately before signing; gas estimates and two-block canonical receipt checks
are shared with auctions. Replaced/reorganized receipts fail closed. A new test file
covers price/relisting changes, gas margin and receipt/reorg failure cases.
Added read-only check_demo_readiness.py and operator_roles.sql; recovery actor uses
SESSION_USER so SET ROLE does not hide personal login attribution. No production
operator accounts or credentials were created. OWNER_HANDOFF.md contains owner setup,
engineering migration prerequisites and the live acceptance matrix. New deployment
still requires legacy market access/history compatibility before default address
switch. Preflight confirmed current RPC/registry but no funded-settlement interface;
Razorpay/signing prerequisites remain absent. No live payments or deployment performed.

## Welcome and authenticated application layout

The root route is now a standalone welcome page with only Create an account and
Log in actions. Login/signup include a return-to-welcome link and no application
navigation or wallet controls. AppShell checks the session before mounting any
application page: anonymous direct links redirect to /login, authenticated visits
to entry pages redirect to /dashboard, and logout returns to /. Password and Google
login/signup both lead to /dashboard. Full navigation becomes visible after login.
Backend account/wallet authorization remains the security boundary; this change
controls page visibility, not public blockchain or public catalog data access.

## Other-crypto request

Added a signed-in Use another cryptocurrency entry from fixed-price/auction pages
and a separate crypto section on /funding. It explains supported swaps/bridges and
source/destination gas without advertising universal token support. LI.FI is the
chosen integration target, not installed/enabled; current Amoy/MockUSDC has no route.
PRODUCTION_PAYMENTS.md documents actual execution prerequisites and wallet funding
versus purchase semantics. No executable quote/SDK or live conversion was added.


## Payment fees and owner checklist (2026-10-01)

PAYMENT_TODO.md tracks the latest crypto/UPI/embedded-wallet requirements and exact
owner actions. Onmeta is the first INR candidate, Onramp.money the alternative;
merchant approval, exact native USDC route and rates remain unverified. LI.FI is
still the crypto target. Buyer pays external charges; existing DKM platform fee
comes from seller proceeds. Funding/test checkout now explain this distinction.
New Razorpay test orders are displayed for review before opening checkout; the
stored amount is reused without an additional buyer DKM fee. Production fee
quotes, provider execution, embedded wallets and migration remain unimplemented.


## Alternative providers and checkout review (2026-10-09)

Onmeta API access is difficult for the owner. MASTER_TODO.md now prioritizes
Transak self-service staging for provider testing (not verified India/UPI), and
Onramp.money for actual INR/UPI qualification. LI.FI remains the crypto target;
Relay is a documented alternative. Live Relay testnet discovery returned only
84532 and 11155111, not Amoy. No provider SDK, keys, real payment or deployment added.
Checkout now re-fetches a pending server order before opening Razorpay, refuses
holds/refunds/prior captures and requires another review when payment details change.
Regression cases cover these boundaries. This improves UI safety, not reservation
or atomicity between bank and blockchain. Earlier unrelated user files remain untouched.


## Migration and settlement verification continuation (2026-10-09)

Implemented shared canonical-receipt verification for backend settlement and refund
eligibility. A changed transaction/block/status or disappeared receipt fails closed;
a shallow receipt remains pending. Two blocks remain a test policy, not production
finality certification.

Legacy access is now configurable through backend LEGACY_MARKETPLACE_ADDRESSES and
frontend LEGACY_MARKETPLACES. Defaults are empty: no runtime addresses changed. Only
reviewed old markets on the same chain/KnowledgeAsset registry may be configured.
Backend download/review access and purchase counts include legacy markets; frontend
entitlement checks and purchase guards prevent duplicate purchases across them.
Fiat checkout also checks prior entitlement. Fixed-price activity includes configured
previous markets and preserves their addresses. Auctions can select old markets for
bidding/finalization/refunds, and sellers can cancel previous listings on asset cards.

Migration still needs a recorded inventory, matching frontend/backend configuration,
reviewed deployment, seller cancellation/relisting and live acceptance. Compatibility
code is not evidence that a deployment or migration occurred. Complete event indexing,
auction/net lifetime reporting and provider/embedded-wallet adapters remain engineering
work; they are not owner credential tasks.

Verification: 31 backend tests passed together after Docker/PostgreSQL was restored;
the additional history regression and three related offline checks then passed.
Seven frontend test groups pass. Existing 121 local Hardhat tests passed again.
Read-only Amoy preflight confirms connected RPC and matching registry, but funded
settlement remains unavailable and Razorpay/signer settings are missing.


## Transak local sandbox continuation (2026-10-10)

Added authenticated, origin-protected, rate-limited Transak staging session creation
and /funding UI. The server binds the destination to the verified account wallet,
uses fixed staging endpoints, checks returned widget origin, and encrypts the
shared access-token cache with existing envelope encryption. PostgreSQL locking
serializes token refresh/session use across workers. No provider event grants access.
Lowercase transak_api_key/transak_api_secret in the ignored .env are supported.
Real staging authentication and widget-session creation succeeded; no payment was
submitted. 35 backend tests plus the new route authorization test, eight frontend
groups, frontend build and 121 contract tests passed. See LOCAL_PAYMENT_DEMO.md.
Transak staging TRNSK is not DKM MockUSDC. No chain deployment or end-to-end fiat
settlement occurred. Crypto routing, embedded wallet, provider reconciliation and
full history remain engineering work. Onramp/MoonPay signup is no longer required
for this local Transak development path.

## Transak order tracking and owner queue (2026-10-10)

Added authenticated account-scoped saved Transak staging orders with manual
provider-order-ID lookup and refresh. Server GET verifies provider ID, destination
wallet, BUY direction, Polygon and USDC; responses whitelist bounded decimal
amounts, provider status and a syntactically valid optional transaction hash.
Provider PII/URLs are not persisted or exposed. Status remains provider-reported,
not independent chain verification. No refresh grants entitlement or settles.

Thirty-nine backend tests passed together, including concurrency, lifecycle,
account isolation and route/auth validation. A decimal-precision rejection case
was added and all five Transak tests reran successfully. Frontend build/typecheck
passed; new order-history and existing Transak UI regression tests passed.
No actual completed provider order was available for live status acceptance.

MASTER_TODO.md is now the current local-college-demo owner/engineering split.
Older requests for multiple fiat-provider accounts/hosting are superseded.
The user has not yet answered whether a separate local blockchain setup is allowed.
No local/public contract deployment or existing Amoy configuration change occurred.
Combined settlement, routing, embedded wallet, full indexed earnings/history and
other listed engineering remain incomplete. The required hardhat skill was not
found in the available skill directories; do not silently bypass contracts rules.

## Flexible payment requirement and seller withdrawal (2026-10-10)

The owner clarified that Amoy was an example, not a mandatory settlement route.
Target design separates buyer payment method, seller pricing/payout currency and
blockchain purchase records. Not every route must convert through Polygon USDC.
Off-chain payment records are backend attestations, not independent proof of bank
settlement. Do not place bank/card/identity details on-chain.

Implemented per-account payout currency preference (USDC/USD/EUR/INR/IDR) and a
Transak hosted SELL sandbox entry on Account. Preference saving does not change
existing prices, active listings, settlement token or enable automatic payouts.
SELL session delegates network/asset selection and payout eligibility to Transak;
BUY sessions retain their original verified-wallet destination. Bank details stay
with the provider. The provider must enable SELL and support the requested fiat.
An actual staging EUR SELL session was created successfully, without submitting a
withdrawal. 37 auth/payment/Transak backend tests, three relevant frontend tests,
and the frontend build/typecheck passed. Existing unrelated user edits preserved.

Full multi-method purchase execution, pricing/fee quotes, payout verification and
the new blockchain attestation/access integration remain unfinished. Contract-test
work is blocked by the missing hardhat skill required by contracts/AGENTS.md; the
owner has been asked for its location. No contract deployment was authorized or
performed by the latest clarification.

## Blockchain recording source (2026-10-10)

Located and read both Hardhat skills; the earlier skill blocker is resolved.
Added a standalone PaymentReceiptRegistry with authorized recorder roles,
separate payment/payout denominations, immutable sandbox classification, duplicate
internal/provider-reference rejection and terminal refund/chargeback records.
It does not move funds or grant access. Existing deployments are untouched.
See PAYMENT_RECORDING.md for evidence rules and the unfinished backend connection.

Final verification: compilation, contract TypeScript checking and all 128 local
contract tests passed (121 existing plus seven receipt-registry cases).
