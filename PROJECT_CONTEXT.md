# DKM continuation — 2026-09-30

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
