# Google login, asset descriptions and payment verification

## Google setup

Password login remains available. Google login/signup use the same “Continue with
Google” flow and create or reuse an account identified by Google's stable `sub`.
Accounts are never automatically merged by email or display name. Google-only
accounts cannot use password login until a separate password-setting feature exists.

Create a **Web application** OAuth client in Google Cloud, configure the consent
screen and test users if the app is in testing, and register this exact redirect:

`http://localhost:8000/api/auth/google/callback`

Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in the
ignored `backend/.env` and restart the backend. Keep the secret out of frontend
variables and Git. Production requires HTTPS URLs and matching `FRONTEND_ORIGIN`.
Missing configuration disables the Google button with an explanation.

The backend creates five-minute, one-use state bound to an HttpOnly browser cookie,
uses PKCE S256, exchanges the authorization code with Google server-to-server, then
fetches the identity from Google's UserInfo endpoint using that access token.
Tokens/profile claims from the browser are never trusted. The session uses the
existing revocable HttpOnly cookie. Google tokens are not stored.

Reference: [Google web-server OAuth](https://developers.google.com/identity/protocols/oauth2/web-server)
and [Google endpoint reference](https://developers.google.com/identity/openid-connect/reference).

## What actually handles INR and USDC

| Path | Intermediary / mechanism | Current limit |
| --- | --- | --- |
| Web3 | User wallet pays the Marketplace with its configured ERC-20 after approval | Polygon Amoy and MockUSDC, not mainnet USDC |
| Web2 | Razorpay test-mode INR order/capture, checked by HMAC and provider API | Test payments only; keys are absent |
| Web2 on-chain settlement | Dedicated DKM wallet supplies pre-funded test USDC through `buyAssetFor` | Dedicated signer/funding and compatible deployment are absent |
| INR → USDC conversion | **No converter or fiat on-ramp is integrated** | Fixed INR-per-USDC value is a test pricing quote, not a currency trade |
| Cross-chain swap/bridge | Not implemented on Amoy | LI.FI research is not a deployed integration |

Expected test flow: quote → Razorpay test capture → provider verification → signed
funded settlement transaction → two-block confirmation depth and entitlement checks.
Mock success and provider confirmation alone do not grant access. If a listing sells
or is cancelled before settlement, captured payments need operator reconciliation;
automated refunds/reservations remain unimplemented. Checkout creation now serializes
per account/asset and reuses an existing order across concurrent browser tabs.

Reference: [Razorpay verification](https://razorpay.com/docs/server-integration/python/test-app/).

## Asset presentation

Marketplace cards no longer display file/metadata CIDs. “View Details” renders only
title, summary/description, topic, tags, license and quality. Raw metadata JSON and
BLAKE3 hashes are not rendered. Descriptions use a public backend endpoint, first
checking stored catalog content and then fixed IPFS gateways; arbitrary URLs are
not accepted. New uploads persist their summary. These are presentation changes:
the underlying public IPFS/blockchain data remains public.

## Checks and limits

- 19 passing backend auth/payment tests cover Google state/cookie/expiry/replay, verified
  identity, repeat login, separation from password accounts, payment capture,
  spoofing/replay rejection, duplicate checkout prevention, durable settlement,
  transaction hash/sender/call/depth and account isolation. Provider calls are
  simulated; this does not certify live Google or Razorpay login/payments.
- 121 Hardhat tests passed, including fixed-price payments, insufficient funds,
  allowances, auctions/refunds, royalty distribution and funded-purchase replay.
- Frontend production build, type checking and lint passed.
- The extraction/hash/fraud/LLM checks passed. The full AI → 384-dimension embedding
  → PostgreSQL → search/reranking → integrity pipeline passed in a disposable
  database schema using the existing cached embedding model. The initial attempt
  was blocked by a sandboxed Hugging Face network request; the cached-model retry
  passed without downloading or altering user records.
- Read-only RPC confirmed chain 80002, deployed marketplace code, active listing 1,
  MockUSDC address `0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719`, and absence of
  the new funded-settlement method on the current deployment.
- No live wallet transaction, fiat capture, Google consent flow or deployment was
  performed. Credentials and the settlement deployment remain required for live E2E.
