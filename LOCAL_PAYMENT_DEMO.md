# Local payment demo — 2026-10-10

## What was verified

- The owner’s saved Transak staging credentials authenticated successfully.
- A real Transak staging widget session was created using a disposable test wallet.
  No checkout was opened and no payment was submitted during this API check.
- 35 backend tests passed, followed by the additional authenticated Transak route
  test. Tests use disposable schemas and simulated provider responses.
- Eight frontend regression groups and the production build passed.
- All 121 existing local Hardhat tests passed, including funded settlement,
  minting, auction finalization/refunds, royalties and seller platform fees.
- No blockchain deployment or marketplace address was changed.

## Run locally

PostgreSQL must be running. From backend, run:

```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

From frontend, run `npm run dev` (or `npm run build` then `npm start`).
Open http://localhost:3000, matching FRONTEND_ORIGIN exactly.

The ignored backend/.env already contains the owner’s lowercase `transak_api_key`
and `transak_api_secret`. These are supported alongside the documented uppercase
TRANSAK_STAGING_API_KEY / TRANSAK_STAGING_API_SECRET names. Do not copy values to
frontend configuration, screenshots, chat, or Git. Keep the existing content key;
it also encrypts the cached Transak access token in PostgreSQL. Concurrent backend
workers reuse the token under a database lock instead of invalidating one another.

## Test Transak

1. Log in and connect/verify your account wallet on the Account page.
2. Go to Add USDC (/funding), then Open Transak sandbox.
3. Use only the official test credentials:
   https://docs.transak.com/guides/sandbox-credentials
4. Review the provider’s displayed currency, payment method, amount, and fees.
   Only methods supported in staging can be exercised; UPI is not verified.
5. Complete the provider’s test steps yourself. Never enter a real payment card.
6. Return to /funding. Provider completion must NOT grant marketplace access.
   Transak selects USDC but delivers its TRNSK token in staging; this is not the
   DKM MockUSDC token. Enter the provider order ID in Verify sandbox order to persist and refresh
   its server-verified status. This is not settlement, a marketplace receipt,
   or entitlement.

If session creation fails, check the Transak staging domain/IP allowlists. The
adapter uses the actual request peer IP, never an untrusted forwarded header;
reverse-proxy deployment requires reviewed trusted-proxy configuration later.
Set the Transak dashboard partner fee to zero to avoid a second DKM buyer markup.
Fees embedded in provider totals must not be added a second time.

## Test marketplace separately

Use Polygon Amoy (chain 80002), test POL for gas and the existing DKM MockUSDC.
A seller lists an asset; a different verified buyer approves MockUSDC and buys.
Check the confirmed transaction, buyer access and seller/royalty/platform payouts.
The creator retains the NFT; the buyer gets an on-chain access entitlement.
The same separation applies to auction bidding and finalized entitlements.
These interactive MetaMask transactions have not been performed in this run.

## Remaining requirements — not completed by staging credentials

- Universal crypto is not supportable: only provider-supported tokens/networks
  with liquidity can work. LI.FI is not integrated and has no current Amoy route
  to this custom MockUSDC. A real bridge-and-buy demo needs a compatible network,
  assets and deployment. A local simulation must remain labelled as simulation.
- Transak staging UPI is not verified. Card/provider sandbox testing and actual
  INR-to-USDC conversion are different acceptance criteria.
- Combined fiat-to-marketplace settlement is not implemented by this adapter.
  The existing deployed market lacks buyAssetFor; newly compiled source does not
  change that. No deployment is being performed under the current instruction.
- A walletless buyer still needs secure embedded-wallet/account binding; that
  adapter is not implemented. This sandbox entry requires a verified wallet.
- Seller pricing is currently USDC, with the existing platform fee taken from
  seller proceeds. Arbitrary fiat payouts or seller-selected payout tokens are
  not implemented. Provider fees are reviewed in provider checkout, not a new
  persisted DKM all-in asset quote.
- Automatic provider order reconciliation, net lifetime/auction history, and other remaining
  roadmap engineering are still open. Production hosting/audit work is outside
  this local-demo run and is not claimed complete.

The local app is suitable for testing these separate flows, not for claiming a
flawless end-to-end UPI or arbitrary-crypto marketplace payment.
