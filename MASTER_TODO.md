# DKM: current owner and engineering checklist

Updated 2026-10-10. This replaces earlier requests to acquire several providers
or prepare production hosting. Current scope: a local college-project demo.
Older roadmap documents retain historical findings, not the current owner queue.

## What you need to do now, in order

### 1. Confirm the separate local blockchain demo

Answer the pending question: may we create a separate local blockchain and test
contracts, without touching existing Amoy deployments or assets?

Recommended: yes. Local simulated funds can exercise settlement, fee distribution
and buyer access. Transak remains a separate sandbox because an external provider
cannot deliver tokens into our localhost chain. This is not a real UPI conversion.
If you choose Amoy only, the current deployment cannot demonstrate the new funded
settlement method without a reviewed testnet deployment.

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

Send the deadline and relevant rubric/report requirements. In particular, say
whether QAOA pricing, VQC embeddings and rich quality scoring are mandatory.
These research experiments cannot be labelled completed based on the existing
LLM score or class names.

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
- [ ] Separate local chain setup and full UI settlement acceptance, if approved.
- [ ] Compatible combined fiat settlement; TRNSK is not our deployed MockUSDC.
- [ ] Supported crypto swap/bridge execution. No arbitrary-token promise and no
  supported LI.FI route into this Amoy custom-token deployment.
- [ ] Persisted, expiring all-in asset quotes and insufficient-output handling.
- [ ] Embedded-wallet integration after development-app access is available.
- [ ] Automated provider reconciliation/refund workflow and sale-race handling.
- [ ] Complete indexed auction/history/net earnings and acceptance verification.
- [ ] Final feature-by-feature local acceptance run and report/demo evidence.
- [ ] Conditional research work if required by the rubric.

The new Transak history is provider-verified, not independently chain-verified.
It is limited to the 50 most recently checked saved orders. Users enter the provider
order ID; automatic webhook discovery is not implemented. Provider-reported fees
are not a pre-purchase DKM asset quote, and refreshing does not trigger settlement.

## Do not spend time on these now

Production domains, paid hosting, KYB, a mainnet deployment, mainnet gas, another
fiat provider, an independent production audit, and live-money acceptance are
outside the current local-demo run. They are not needed to test the existing app.

## Completion rule

The project is complete only when the agreed demo requirements are implemented
and the full buyer/seller acceptance matrix passes. Working credentials and unit
tests do not by themselves satisfy end-to-end fiat or cross-chain settlement.
