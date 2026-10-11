# Exact local college demonstration runbook

Updated 2026-10-11. This is an acceptance script, not a claim that the steps have
already passed interactively. Use test accounts/assets only. Do not use real money.

## Automated preparation owned by Codex

Run from the repository root:
```powershell
.\backend\venv\Scripts\python.exe backend/acceptance.py
```
The runner checks backend/database boundaries, frontend regressions/build, contracts
and contract type-checking; results go to acceptance_results.json and tmp/acceptance.
It does not deploy, submit provider payments or sign public transactions.

| Requirement | Automated evidence | Human/external boundary |
| --- | --- | --- |
| A Authentication/isolation | test_auth, session/origin/wallet replay and concurrency | Google OAuth interaction |
| B Content/mint/link | auth upload/encryption/link/download tests; KnowledgeAsset tests | Real Pinata upload and wallet mint |
| C Search/filtering | auth search filters; existing search code | Search actual uploaded document |
| D Fixed-price | quotes, capabilities, payment tests and frontend stale-listing checks | Signed deployed purchase |
| E Auctions | Hardhat lifecycle/refunds; selected legacy-market UI regression | Two real test bidders |
| F Transak BUY | test_transak binding/reconciliation/outage/restart | Hosted sandbox completion |
| G Transak SELL | test_payouts binding/currency/conflict/audit | Provider-supported sandbox payout |
| H Audit recording | test_recording/source tests, signed-byte/event/reorg fixtures | Registry approval/deployment/signing |
| I Index/accounting | test_indexer, positions, cursor/reorg/large integers | Complete historical RPC coverage |
| J Legacy | download/review old-market lookup, duplicate buy and old cancel/refund UI tests | Actual migration remains unapproved |
| K Recovery | payment/refund/concurrency tests, immutable reversals | Real provider failure/refund scenario |
| L Research | research_results API, retained QAOA/VQC artifacts | Present limitations to examiner |

The database tests use disposable schemas; provider/RPC responses are simulated at
those boundaries. Backend success is not evidence that a bank payment settled.

## Start the app

PostgreSQL must be available. Codex starts/checks services and migrations; the owner
does not need to perform database or coding work. Operator commands:
```powershell
# backend directory
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
# frontend directory
npm run dev
```
Open http://localhost:3000 (not a different hostname). Welcome -> Create an account
or Log in. No marketplace/dashboard/search navigation should appear before login.
Google remains disabled until OAuth credentials/test users are configured.

## Interactive steps after automated readiness

1. Use separate browser profiles for seller S and buyers B1/B2. Two bidders plus a
   non-bidding seller require three accounts/wallets. Create password accounts; in
   Account connect MetaMask on Polygon Amoy (80002), then verify wallet ownership.
   Never paste wallet keys into DKM. Wrong account must not see another dashboard.
2. As S, Create asset -> select a harmless new document -> analyze -> inspect title,
   description, quality and price -> encrypt/upload -> mint in MetaMask -> link.
   Confirm Dashboard lists it. Reload and use Continue minting/Verify and link mint
   to check recovery without duplicate uploading. The file/hash internals should
   not be marketed as the asset description.
3. S opens the asset in Marketplace and creates a fixed-price listing. Record
   asset ID, price and public transaction hash. NFT ownership stays with S.
4. B1 opens the asset, reviews the quote (gross, seller-paid fee, royalties, net),
   approves the displayed token allowance if needed and confirms purchase. Do not
   bypass a disabled capability. After confirmation, check license in Dashboard,
   download, compare contents and submit a review. B2 must still lack access.
5. S creates an auction for a separate eligible asset. B1 bids, B2 outbids. B1 uses
   Withdraw bid refund. After the displayed chain deadline, finalize. Verify B2's
   entitlement, S's proceeds and the auction transaction. Seller remains NFT owner.
6. Funding -> Transak sandbox BUY. Use only official provider test details for
   routes the widget actually offers. Return and verify the saved order in DKM.
   Funding alone must not unlock an asset. TRNSK on the sandbox is not Amoy MockUSDC.
   Report missing UPI/card/currency options; do not select an unsupported live route.
7. Seller payout -> choose a supported preference -> open SELL sandbox. If supported,
   complete official test steps, save the provider order reference in the matching
   DKM payout session and refresh. Session creation must say pending verification;
   completed requires server evidence and matching currency/account references.
   If provider refuses staging SELL, record that exact non-secret limitation.
8. Previous-market selector, if configured: old buyer downloads/reviews; an already
   licensed asset cannot be purchased again; old seller cancels on old market;
   old auction finalization/refund targets old market. Current inventory has no
   configured legacy market, so mark this interactive case not applicable until an
   approved migration, rather than fabricating a pass.
9. Research: open /research after login. Present QAOA 64-case experiment and VQC
   ranking comparison. State that the main classical baselines performed better.
10. Dashboard: review uploads, current positions, provider orders, payout status,
    reviews, indexed history/accounting and audit status. Index coverage must be
    visible; no bounded total is lifetime earnings.

## Receipt and Web2 settlement gates

Registry recording remains disabled until approval and deployment. Existing
Marketplace transactions already record on-chain purchases. Razorpay test uses a
prefunded settlement wallet, not currency conversion, and its funded contract route
requires compatible deployed code. Do not enable unsupported routes for a demo.
The final registry test must compare source payment, audit event, buyer/seller,
denominations/amounts and reversal linkage; a registry entry must never unlock files.

## Pass/fail evidence to retain

For each numbered step record PASS / FAIL / BLOCKED, account label, asset ID,
public transaction hash, selected network/provider route, expected/actual result.
Screenshots must exclude passwords, OTPs, provider secrets, bank/card/KYC details.
Send only non-secret errors/references. Codex investigates failures and updates
TEST_EVIDENCE.md; no failure should be replaced with a mock success claim.
