# Backend to frontend coverage

Current scope (2026-10-24): the frontend is wallet-only. Provider-related rows below describe retained API/component capabilities and historical integration work, not enabled UPI/card checkout. `/funding` redirects to the marketplace. Purchases use the deployed Amoy mock token; no live INR conversion is claimed. Auctions accept 2 minutes to 720 hours. Downloads prefer the configured dedicated Pinata gateway.

## Where to use each feature

| Feature / API | Frontend | Access and state |
| --- | --- | --- |
| Signup, login, session, logout | `/signup`, `/login`, `/account` | Username/password or configured Google OAuth; server-side sessions expire after 12 hours and logout revokes them |
| Public asset description, `/api/assets/{token_id}/details` | Marketplace → View Details | Allowlisted title, summary, topic and tags; no raw metadata, file IDs or hashes |
| Purchaser reviews, `/api/assets/{token_id}/reviews` | Marketplace → View Details | Public aggregate/pagination; verified purchasers can save/update one review |
| Protected download, `/api/assets/{token_id}/download` | Marketplace → Check my access → Download | Rechecks on-chain access; decrypts and verifies new encrypted files |
| Account blockchain activity, `/api/account/activity` | Dashboard → On-chain purchases and sales | Fixed-price history per bounded RPC block page; gross sales, not lifetime net earnings |
| Wallet challenge and signature verification | `/account` | Logged-in account; single-use five-minute challenge; one verified wallet per account |
| Document analysis, `/api/analyze` | `/mint`, step 1 | Login; file size limit; AI quality feedback |
| Upload, `/api/upload-ipfs` | `/mint`, step 2 | Verified wallet; multipart metadata; upload is saved under the account |
| Token link, `/api/assets/{vector_id}/link-token` | `/mint`, step 3; recovery in `/dashboard` | Account owns upload; server checks on-chain creator, both CIDs and price |
| Search, `/api/search` | `/search` | Public; query, domain and price filters; results link to marketplace assets |
| Account uploads and payments | `/dashboard` | Server filters by account ID; latest 100 records per list |
| Asset access, `/api/assets/{token_id}/access` | Marketplace → Check my access | Uses session's verified wallet; no caller-supplied identity; includes creator access |
| Payment create, read, confirm, settle | Retained backend/provider components; not enabled in the wallet-only checkout | Account-owned orders; callbacks authenticated; entitlement requires chain settlement |
| Latest checkout recovery | Marketplace asset checkout | Restored from the server per account/token, including across browsers |
| Health and capabilities | `/status` | Public; indicates setup availability and unavailable payment options |
| Fixed-price Web3 purchases | `/marketplace` | Verified account wallet; USDC approval, receipt checking, chain enforcement |
| Fixed-price listing and cancellation | Owned asset in `/marketplace` | Verified account wallet; smart contract checks seller authority |
| Auction create | Owned unlisted asset in `/marketplace` | Verified account wallet; duration and reserve price |
| Auction browse/history, bid, end, refund | `/auctions` and marketplace asset | All auction IDs, newest first, 12 per page; completed auctions remain visible |
| Wallet connect and network switch | Shared navbar and transaction controls | Wallet connection alone does not authenticate a backend account |

Provider webhooks and background settlement reconciliation are machine-to-machine
operations; they are reflected in payment status instead of exposed as buttons.
Mock payments remain an API/test facility and never grant entitlement. Contract
owner administration (pause, splitter configuration) is not exposed to ordinary
users. Search includes a minimum quality filter alongside domain and price.

## Security and setup limits

- Passwords use salted scrypt (N=2^17, r=8, p=1). Session tokens are random, stored
  hashed in PostgreSQL and sent only in HttpOnly, SameSite=Strict cookies.
- `FRONTEND_ORIGIN` is the exact allowed origin. HTTPS origins enable Secure
  `__Host-` cookies. Production must use HTTPS and same-site frontend/API hosting.
  Use localhost consistently during development, rather than mixing it with 127.0.0.1.
- Mutations require the exact origin and a custom request header; account login
  and registration are throttled in PostgreSQL. Authentication errors do not echo
  submitted passwords or signatures. Private responses use `Cache-Control: no-store`.
- Existing uploads/orders have no account owner. They stay unclaimed and are not
  assigned by a supplied wallet address. A reviewed migration is required to adopt
  legacy private records. Existing public marketplace listings remain browsable.
- New files are AES-GCM encrypted before IPFS upload; authenticated downloads
  recheck on-chain entitlement and integrity. Public catalog metadata remains
  readable. Legacy public files remain public. Back up CONTENT_MASTER_KEY securely;
  see ROADMAP_STATUS.md for server-managed encryption limits and key operations.
- No password recovery, MFA, wallet reassignment or independent security audit is
  implemented. Password signup uses usernames; Google requires a verified email
  and identifies accounts by stable subject, without automatically merging accounts.
- Google setup and detailed payment verification are in PAYMENT_AUTH_VERIFICATION.md.
- Razorpay test settlement still needs deployment of `buyAssetFor`, provider keys,
  a funded/approved dedicated signer and live E2E verification. Bridge checkout is
  unavailable on Amoy. The UI explicitly shows these limitations.
- Account checks in the frontend improve the user flow; smart contracts still
  require wallet signatures and independently enforce blockchain permissions.

## Verification

Run `venv\Scripts\python.exe -m unittest tests.test_auth tests.test_payments -v`
from backend, and `node_modules\.bin\next.cmd build` from frontend.

Security tests use disposable database schemas and real locally generated message
signatures. External payment, storage and chain calls are simulated. Tests cover
session expiry/revocation, CSRF rejection, password error redaction, rate limiting,
wallet proof replay/expiry/mismatch, cross-account payment and upload isolation,
mint content matching and the multipart upload ID. Browser checks cover signup,
login/logout, account/dashboard navigation and logged-out restrictions; no wallet
transactions or live fiat payments are authorized by these tests.

References: [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
and [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

## Entry flow acceptance (2026-10-01)

The application now uses a shared AppShell. Only /, /signup and /login render for
anonymous visitors. All other pages redirect to /login without mounting app content
or navigation. Signed-in visits to the three entry routes redirect to /dashboard.
Password and Google authentication land on /dashboard; logout returns to welcome.
No wallet or feature controls appear before authentication. This UI restriction
supplements existing backend authorization; public on-chain/catalog data is not
made private by hiding navigation.

Repeatable browser acceptance check:

1. Logged out, open /: only welcome, Create an account and Log in actions appear.
2. Follow Create an account: signup form and Back to welcome appear, with no navbar.
3. Create a disposable account: /dashboard opens with marketplace, auctions, funding,
   search, create-asset, dashboard, status and account navigation plus wallet controls.
4. Open /signup while signed in: redirect to /dashboard.
5. In Account, log out: / shows welcome and removes the application controls.
6. Open /marketplace directly: redirect to standalone /login without app content.
7. Log in with the disposable account: /dashboard and full navigation return.
8. Log out and remove only the disposable account after checking it owns no assets,
   payments or wallet. Never delete a real account as part of this check.

All steps passed in the in-app browser against localhost:3000. The disposable account
and sessions were removed. Frontend production build/lint/typecheck and 12 backend
authentication tests passed, including the updated Google dashboard redirect.
Existing optional pino-pretty and webpack cache warnings were non-fatal. No live
Google consent or wallet signature was exercised.
