# DKM: current owner and engineering checklist

Latest execution update 2026-10-11: use HUMAN_ACTION_REQUIRED.md for the owner
queue and ENGINEERING_PLAN.md for milestone order. Embedded wallets are conditional
on the rubric under the latest brief. QAOA pricing and VQC embeddings are REQUIRED
core components, explicitly confirmed by the owner; older conditional labels below
are superseded. Baseline tests reran successfully; shared
server route capabilities and frontend gating are implemented and tested. This
does not complete quotes, recording, indexing or interactive acceptance.

Updated 2026-10-10. This replaces earlier requests to acquire several providers
or prepare production hosting. Current scope: a local college-project demo.
Older roadmap documents retain historical findings, not the current owner queue.

## What you need to do now, in order

### 1. Contract tooling — resolved, no owner action

The hardhat skill was found in contracts/.agents/skills/hardhat/SKILL.md.
The matching ethers/Mocha skill is bundled with the installed Hardhat package.
The previous missing-skill request was an incomplete search and is withdrawn.

The provider-independent receipt registry is implemented and locally tested, but
backend recording, entitlement connection and deployment remain engineering work.

### 2. Prepare two test participants

- Confirm MetaMask is on Polygon Amoy, chain ID 80002 (not a different MOI network).
- Use distinct seller and buyer wallet addresses and separate DKM accounts.
- Verify each wallet through the Account page in its own browser profile.
- Share only the two PUBLIC addresses and which is seller/buyer.
- Use Amoy test POL and DKM MockUSDC only. Do not buy real crypto for this demo.
- Keep MetaMask available for your wallet verification and transaction signatures.

### 3. Complete one Transak sandbox checkout

- Your saved credentials already authenticate and create a staging session.
  No Onramp.money, MoonPay or Alchemy Pay registration is required.
- In Transak's dashboard, leave the additional partner fee at zero.
- In DKM, log in, verify your wallet, then open Add USDC > Open Transak sandbox.
- Use only the official sandbox instructions:
  https://docs.transak.com/guides/sandbox-credentials
- Copy the test order ID after checkout, return to Add USDC, and use Verify
  sandbox order. This verifies status server-side and saves it to your account.
- Return the test order ID, selected payment method and any non-secret error.
  Do not provide identity documents, card details, OTPs or credentials in chat.
- UPI availability is not verified. If UPI is absent, report that; do not use a
  real UPI payment. Staging delivers TRNSK rather than DKM MockUSDC.
- Session creation alone is not proof that the whole checkout works.

### 4. Supply the college acceptance requirements

QAOA pricing and VQC embeddings are confirmed mandatory (2026-10-11). Their
implementation, baselines and measured results remain engineering work. Send the
deadline if not already supplied. Existing LLM scores and class names do not
complete the required experiments.

### 5. Enable remaining external account integrations

For Google sign-in:
- Create a Google OAuth Web Application client.
- Register http://localhost:8000/api/auth/google/callback as its redirect URI.
- Save GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI in ignored
  backend/.env. Keep FRONTEND_ORIGIN=http://localhost:3000.
- Tell me only that configuration is ready. Password login already works.

For the requested no-MetaMask buyer experience:
- Create a Privy development app through https://docs.privy.io/.
- Return its public app ID and whether localhost is allowed. Keep secrets private.
- The existing DKM account database must remain authoritative. I implement and
  test secure wallet binding/recovery; do not replace the account system yourself.
- If obtaining this account is difficult, tell me the exact non-secret blocker;
  do not purchase a plan before we confirm the demo needs it.

### 6. Protect existing project data

Back up the existing CONTENT_MASTER_KEY securely; never regenerate it over the
old key. Back up the Docker database. Rotate the previously exposed RPC credential
in its provider dashboard and update ignored local configuration. Share no keys.

## My engineering work — not your implementation tasks

Completed in the current Transak work:
- [x] Staging-only secure session creation and verified-wallet destination.
- [x] Real staging authentication and session creation tested.
- [x] Encrypted shared token cache and serialized multi-worker token use.
- [x] Account-scoped persistent provider order history and manual refresh.
- [x] Server verification of order ID, wallet, BUY direction, Polygon and USDC.
- [x] Display provider-reported amounts/fees without adding fees twice.
- [x] No provider completion/dummy transaction grants access or spends MockUSDC.
- [x] Backend concurrency/isolation/failure tests and frontend regression coverage.

Still open; I must not describe these as owner-only tasks:
- [ ] Blockchain payment-attestation/access integration and complete UI acceptance.
- [ ] Compatible combined fiat payment/payout verification and blockchain recording.
- [ ] Supported crypto swap/bridge execution. No arbitrary-token promise and no
  supported LI.FI route into this Amoy custom-token deployment.
- [ ] Persisted, expiring all-in asset quotes and insufficient-output handling.
- [ ] Embedded-wallet integration after development-app access is available.
- [ ] Automated provider reconciliation/refund workflow and sale-race handling.
- [ ] Complete indexed auction/history/net earnings and acceptance verification.
- [ ] Final feature-by-feature local acceptance run and report/demo evidence.
- [ ] Required QAOA pricing and VQC embedding experiments, comparisons and report.

The new Transak history is provider-verified, not independently chain-verified.
It is limited to the 50 most recently checked saved orders. Users enter the provider
order ID; automatic webhook discovery is not implemented. Provider-reported fees
are not a pre-purchase DKM asset quote, and refreshing does not trigger settlement.

## Latest seller preference implementation

Account now saves a requested payout currency and can open Transak SELL sandbox.
USDC/USD/EUR/INR/IDR are preference choices, not a guarantee that all routes work.
Saving does not change active listing prices or cause automatic conversion.
Enable SELL in the Transak partner portal if necessary. Test only documented
sandbox payout details. EUR session creation worked, but no withdrawal completed.
This is separate from completing and recording a marketplace purchase.

## Do not spend time on these now

Production domains, paid hosting, KYB, a mainnet deployment, mainnet gas, another
fiat provider, an independent production audit, and live-money acceptance are
outside the current local-demo run. They are not needed to test the existing app.

## Completion rule

The project is complete only when the agreed demo requirements are implemented
and the full buyer/seller acceptance matrix passes. Working credentials and unit
tests do not by themselves satisfy end-to-end fiat or cross-chain settlement.

## Blockchain recording source (2026-10-10)

Located and read both Hardhat skills; the earlier skill blocker is resolved.
Added a standalone PaymentReceiptRegistry with authorized recorder roles,
separate payment/payout denominations, immutable sandbox classification, duplicate
internal/provider-reference rejection and terminal refund/chargeback records.
It does not move funds or grant access. Existing deployments are untouched.
See PAYMENT_RECORDING.md for evidence rules and the unfinished backend connection.
