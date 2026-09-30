# DKM roadmap audit — 2026-09-30

This maps the supplied 44-item roadmap to the current feature branch. “Implemented”
means code exists and local checks support it; it does **not** mean production or
live payment E2E completion. Items overlap, so counts are not an effort percentage.

**25 implemented/local, 9 partial, 7 pending external rollout/E2E, 3 conditional research.**

| # | Roadmap item | Status | Evidence / remaining work |
|---|---|---|---|
| 1 | Mock create/get/confirm/get | Implemented | Payment tests; provider ID saved, no settlement or entitlement |
| 2 | PostgreSQL payment orders | Implemented | `services/payments/service.py`; restart/concurrency checks |
| 3 | Empty royalty recipients | Implemented | Marketplace/splitter source and existing contract tests; not a claim about upgraded live deployment |
| 4 | Amoy contract redeployment | Pending | Preserve KnowledgeAsset and existing entitlements/listings before replacing Marketplace |
| 5 | Live Web3 purchase/access E2E | Pending | Local contracts pass; no live buyer/seller wallet transaction performed |
| 6 | Frontend Web3 purchase UX | Partial | Network/balance/allowance/receipt/access UI exists; live signing verification remains |
| 7 | Decide Web2 entitlement design | Implemented | Funded `buyAssetFor`; provider confirmation is never entitlement |
| 8 | Web2 settlement state machine | Implemented | Durable states through independently verified entitlement |
| 9 | Secure contract settlement | Implemented | Payer-scoped reference, full funded transfer, replay tests; deployment pending |
| 10 | Backend settlement service | Implemented | Signed transaction checkpoint, receipt identity/depth, entitlement validation |
| 11 | Idempotency | Implemented | Unique payment IDs, per-order/signer/checkout DB locks, retry tests |
| 12 | Real Web2 provider | Partial | Razorpay test implementation; credentials/live capture and production onboarding absent |
| 13 | Fiat conversion/quote | Partial | Persisted INR test quote/rate/amount; no actual INR-to-USDC conversion or live expiring FX quote |
| 14 | Buyer wallet validation/binding | Implemented | Signed challenge and immutable verified account wallet |
| 15 | Provider webhooks | Implemented | Raw-body HMAC plus provider capture/order/amount/currency verification |
| 16 | Combined payment options | Implemented | Wallet and UPI/card UI; unavailable fiat setup is explicit |
| 17 | Payment progress/recovery | Implemented | Status-specific messages, server order recovery, settlement retries |
| 18 | Buyer history | Partial | Account Web2 orders plus paged fixed-price chain history; full indexed auction/lifetime history remains |
| 19 | Seller transactions | Partial | Fixed-price sales, gross amount, route and transaction links; net earnings and complete auction reporting remain |
| 20 | Upload/mint DB linkage | Implemented | Real stored vector ID; account, creator, both CIDs and price checked |
| 21 | Storage health check | Implemented | Pinata configuration replaces obsolete NFT.Storage setting |
| 22 | Persistent duplicate detection | Implemented | PostgreSQL hash lookup; concurrent insert guard; failures do not poison retries |
| 23 | Payment validation | Implemented | Address, session, listing, active asset, price, entitlement, state and method checks |
| 24 | Backend payment tests | Implemented | Runnable durable-state/provider/webhook/settlement/account tests |
| 25 | Contract tests | Implemented | 121 tests pass after the audit fixes; contract TypeScript checks pass |
| 26 | Post-deploy addresses/ABIs | Pending | Current addresses preserved; must follow actual deployment, never point to undeployed code |
| 27 | Full mint regression | Partial | Mock storage/mint-link tests and real document pipeline pass; live encrypted upload→mint still needs wallet test |
| 28 | Search regression/filters | Implemented | Domain/price/minimum quality SQL + API/UI; existing 384D semantic/graph pipeline |
| 29 | Debug UI cleanup | Implemented | Raw debug page redirects to status; provider payload prints and raw purchase errors removed |
| 30 | Network handling | Implemented | Amoy chain guards/switches, including home counter reads |
| 31 | User-facing errors | Implemented | Auth, wallet, purchase, provider, storage, reviews and history failures have readable UI paths |
| 32 | Detail/access/download flow | Implemented | Entitlement check, protected download, legacy public link; download rechecks authorization |
| 33 | Secure downloadable files | Implemented | New files AES-256-GCM encrypted before IPFS; server wraps keys and verifies integrity. Legacy public content cannot be made secret retroactively |
| 34 | Reviews/reputation | Implemented | Verified purchaser writes, self-review rejection, 1–5 rating, concurrent update, public aggregate/pagination/UI |
| 35 | Seller dashboard | Partial | Uploads/mint recovery, quality, asset links and fixed-price activity; consolidated listings/reviews/net lifetime earnings incomplete |
| 36 | Rich quality/review analysis | Conditional | Existing single LLM score only; coherence/completeness/originality benchmarks and review summaries absent |
| 37 | QAOA pricing research | Conditional | No QAOA optimizer/benchmark results; not fabricated |
| 38 | VQC embedding research | Conditional | Classical 384D embeddings exist; no VQC/NDCG benchmark; not fabricated |
| 39 | Production security hardening | Partial | Auth/CSRF/CORS/signatures/idempotency/encryption in place; abuse/load review, secret rotation, restore drill and independent audit remain |
| 40 | Smart-contract audit | Partial | Slither completed, actionable ordering warnings fixed; 4 low timestamp and 1 informational compiler finding remain; independent audit still required |
| 41 | Production backend/DB | Pending | No Oracle host/domain/access, HTTPS, secrets, backup target or production sizing supplied |
| 42 | Production frontend | Pending | Build passes; Vercel project/domain and production API origin unconfigured |
| 43 | Mainnet migration | Pending | Intentionally gated on live E2E and security review; current token is Amoy MockUSDC |
| 44 | Final two-route E2E matrix | Pending | Cannot pass until live storage/wallet/provider/settlement/deployment prerequisites are satisfied |

## Work added during this audit

- Persistent duplicate checks, including simultaneous identical insert rejection.
- Purchaser reviews, aggregate rating, pagination and marketplace form.
- Minimum-quality search filter throughout UI/API/SQL.
- Account-specific fixed-price transaction history and gross sales per block page.
- New encrypted uploads, envelope keys, authenticated downloads, integrity checks.
- Removed raw provider logging/debug output and fixed the home counter chain.
- Ran Slither and tightened checks-effects-interactions in Marketplace payments.
- Corrected the frontend Marketplace ABI: `hasPurchased` and `purchaseCount`
  already existed on-chain but were missing from its JSON. This prevented the
  wallet entitlement read (and purchaser review eligibility) from resolving.

## Encrypted storage operations

`backend/init_content_key.py` initializes a random 32-byte `CONTENT_MASTER_KEY` in
the ignored local `.env`, without printing it or replacing a nonempty existing key.
It has been run locally. Back up this key separately and securely alongside regular
database backups **before accepting protected uploads**. Losing it makes encrypted
files unrecoverable. Do not rotate by overwriting it; a key-version migration is
required. New environments run `venv/Scripts/python.exe init_content_key.py` once.

Each upload uses a fresh data key and nonces. AES-GCM authenticates file data and
wrapped keys with the BLAKE3 digest as associated data. Only ciphertext is uploaded
as the file; public catalog metadata remains readable. Envelope keys never appear
in catalog/search/dashboard responses. The backend decrypts only after current
on-chain access is checked and returns an attachment with no-store and nosniff.
This is server-managed encryption, not Lit/decentralized key release or DRM;
authorized users can redistribute downloaded plaintext. Existing public assets
keep explicit legacy labels and URLs; no historical CIDs or entitlements changed.

## Verification and external limits

- 24 auth/payment/activity tests passed against disposable PostgreSQL schemas.
  Storage, identity and payment providers are simulated; encrypted downloads test
  non-purchasers, inactive assets, content tampering and response key isolation.
- Frontend production build/typecheck/lint passed; the existing optional
  WalletConnect `pino-pretty` warning remains non-fatal.
- Extraction, BLAKE3 and updated fraud checks passed. The full document/LLM/cached
  embedding/search pipeline was rerun in a disposable schema and passed. Initial
  harness attempts needed explicit dotenv path and UTF-8 console mode on Windows;
  both were fixed without touching user records. All 121 contract tests were rerun
  after source changes and passed, as did contract TypeScript checking. The Solidity
  interface is unchanged; the frontend ABI gained its two missing deployed read
  methods. No deployment or address changes occurred.
- Browser search with minimum quality 80% returned only qualifying results;
  public reviews and the protected-storage health check returned HTTP 200.
- A live read-only history query passed. The configured free RPC rejects ranges
  above 10 blocks; `RPC_LOG_PAGE_SIZE` defaults to 10. Larger plans may use up to
  2,000. These pages are explicitly not lifetime earnings; use an indexed event
  store for production reports. Empty current pages do not mean no historical sales.
- An RPC error traceback exposed the configured provider URL in local diagnostic
  output during this audit. Rotate that RPC API key; no wallet private key was
  printed. Subsequent probes redact provider errors.
- Google client credentials, Razorpay settings, the dedicated funded settlement
  signer and compatible Marketplace deployment remain missing. See
  `PAYMENT_AUTH_VERIFICATION.md`. No real payment, deployment, mainnet transaction
  or public-site publication was performed.

## Next execution prerequisites

1. Configure Google/Razorpay test credentials locally (never paste secrets into chat).
2. Establish a reviewed Marketplace migration that retains old entitlements and
   seller listings; deploy only affected contracts with funded Amoy signers.
3. Fund/approve the dedicated MockUSDC settlement wallet, then execute both real
   testnet E2E paths including encrypted download and purchaser review.
4. Supply production hosting/domain access and backup destination, and resolve the
   independent audit and production fiat/on-ramp decisions before public launch.
5. Confirm whether conditional research items 36–38 are required for submission.

## Slither scan and triage

Slither ran against fresh Hardhat artifacts using an isolated `uv tool run` install.
Use `hardhat compile --force` first: incremental build-info produced stale source
maps during the first attempts. Run Python with `-X utf8` on Windows. Reproduction:

```
uv tool run --from slither-analyzer python -X utf8 -m slither . --ignore-compile --filter-paths "node_modules|test"
```

The compact scan evidence in `SLITHER_AUDIT.json` preserves every detector's name,
severity, confidence and description before/after fixes. It omits bulky AST element
metadata. Initial scan: 5 medium, 7 low, 1 informational. Final scan: **0 high,
0 medium, 4 low, 1 informational**; 26 contracts and 102 detectors analyzed.
The CLI exits 1 because findings remain, not because analysis failed.

- Moved bid/refund bookkeeping and purchase entitlement effects before external
  token/splitter calls. `nonReentrant` remains; failed transfers revert all effects.
- Explicitly initialized the four royalty sum locals to zero. This clarifies the
  existing Solidity default rather than fixing an observed incorrect balance.
- Remaining low warnings concern timestamps. Auction deadlines deliberately use
  block time and should not promise exact wall-clock execution. Two listing checks
  are flagged through Slither's dataflow; neither uses time as randomness.
- The informational compiler warning remains. Solidity 0.8.20 is pinned in the
  existing build; the application has no custom Yul sequence, verbatim block or
  side-effecting selector expression found in this review. This is limited source
  inspection, not proof that all compiler bugs are inapplicable. Review the current
  compiler bug list and choose/test an updated compiler before production deployment.

References: [Slither usage](https://github.com/crytic/slither/wiki/Usage) and
[Solidity known bugs](https://docs.soliditylang.org/en/latest/bugs.html).
