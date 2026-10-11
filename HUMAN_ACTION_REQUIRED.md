# Human-only actions for the college demo

Updated 2026-10-11. This is the future acceptance queue, not a request to perform
coding, database work, tests or migrations. Codex owns commit/push to existing
draft PR #1 and fixes from acceptance. No extra provider signup is required.
QAOA and VQC are required and implemented; no scope reconfirmation is needed.

## 1. Wallet and app acceptance, after the final engineering checks

ACTION REQUIRED: Follow steps 1–5 and 8–10 in DEMO_RUNBOOK.md with test accounts.
WHY: Wallet signatures, test-token approvals and the two-bidder auction need you.
WHERE: http://localhost:3000 in separate browser profiles and MetaMask.
WHAT I MUST CLICK/ENTER: Create seller S and buyers B1/B2; connect Amoy chain
80002; verify wallets; upload/mint/list; purchase/download/review; bid/outbid/refund/
finalize. Use only test gas and test tokens. Keep the creator as NFT owner.
WHAT I MUST NOT SHARE: Passwords, seed phrases, private keys or signing secrets.
EXPECTED RESULT: Only the purchasing/winning account gains access; refunds and
sales match their public chain transactions. Signed steps remain unverified until run.
WHAT TO SEND BACK TO YOU: Step number, PASS/FAIL, account label, asset ID, public
transaction hash and a non-secret error if any. A deadline is useful if available.

## 2. Transak sandbox BUY and SELL

ACTION REQUIRED: Perform the hosted sandbox steps in DEMO_RUNBOOK.md, when ready.
WHY: Authentication/session creation and simulated verification tests do not prove
a completed provider checkout or bank payout.
WHERE: DKM Funding / Seller payout and the Transak staging widget.
WHAT I MUST CLICK/ENTER: Choose only offered sandbox routes, use official provider
test details and keep the partner fee zero. Save the order in its matching DKM
session and refresh verification. If SELL/UPI/currency is absent, report it.
WHAT I MUST NOT SHARE: Real card/bank/KYC data, API secrets, access tokens or OTPs.
EXPECTED RESULT: Server-verified independent funding/payout status. Transak TRNSK
funding alone never grants DKM access or becomes Amoy MockUSDC.
WHAT TO SEND BACK TO YOU: Selected sandbox route, safe order reference, status and
non-secret provider limitation. Do not switch to real-money checkout to pass a test.

## 3. Google login, if it must be demonstrated

ACTION REQUIRED: Configure your Google OAuth application and test user access.
WHY: Google login code is implemented; the current UI correctly says setup pending.
WHERE: Google Cloud OAuth Web Application and ignored backend/.env.
WHAT I MUST CLICK/ENTER: Set callback http://localhost:8000/api/auth/google/callback;
save GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI locally; allow
the demo Google test accounts; retain FRONTEND_ORIGIN=http://localhost:3000.
WHAT I MUST NOT SHARE: Client secret, account password, tokens or OTPs.
EXPECTED RESULT: Codex validates configuration without printing secrets; you then
complete Google login and verify that it opens only your account.
WHAT TO SEND BACK TO YOU: “Saved locally” or a sanitized setup error.

## 4. Existing key backup and credential rotation

ACTION REQUIRED: Securely back up the existing CONTENT_MASTER_KEY and replace any
previously exposed RPC credential through its provider dashboard.
WHY: Losing or overwriting the content key breaks decryption and evidence-reference
continuity. Database restoration does not back up separately stored key custody.
WHERE: Private password manager/offline backup and RPC provider portal.
WHAT I MUST CLICK/ENTER: Save a replacement RPC URL only in ignored local settings;
tell Codex to validate it before revoking the old one. Do not replace the content
master key without an explicit re-encryption/reference migration plan.
WHAT I MUST NOT SHARE: Keys, full credential-bearing URLs or private database data.
EXPECTED RESULT: Recoverable encrypted content and a verified replacement RPC.
WHAT TO SEND BACK TO YOU: Backup secured/replacement saved locally, without values.

## 5. Deployment only after a separate concrete approval

ACTION REQUIRED: Review the approval package in MIGRATION_PLAN.md when deployment
becomes the only remaining gate for the requested chain route.
WHY: Receipt recording needs a deployed registry; funded checkout needs compatible
deployed Marketplace code. Local compilation does not update deployed contracts.
WHERE: This chat for approval, then your wallet for exact deployment transactions.
WHAT I MUST CLICK/ENTER: Approve only the identified contracts, constructor/role
addresses and test-gas budget after refreshed inventory and migration verification.
Keep recording disabled until then. No deployment is requested or authorized now.
WHAT I MUST NOT SHARE: Deployer, admin, settlement or recorder private keys.
EXPECTED RESULT: KnowledgeAsset and old entitlements preserved; separate recorder
custody; verified sandbox registry. A receipt never grants access or transfers funds.
WHAT TO SEND BACK TO YOU: Explicit approval of the finalized package or your choice
to demonstrate local contract tests while leaving deployed recording blocked.

Production hosting, company onboarding, live fiat conversion, independent audit
and production key-management procurement are outside the local demo acceptance.
