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
