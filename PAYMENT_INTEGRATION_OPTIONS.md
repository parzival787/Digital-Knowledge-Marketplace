# Future payment options — research only, 17 October 2026

The current UI uses wallet purchases and auctions. Provider checkout, sandbox
funding, fiat payout controls and their navigation have been removed. Backend
provider code and historical records remain intact. No new integration is enabled.
The retained provider-order API keeps its existing whole-USDC convention and
rejects fractional upload prices; cent-priced purchases use wallet checkout.

## What each route would require

| Goal | Route | Requirements |
|---|---|---|
| INR UPI and cards | Razorpay or Cashfree hosted checkout | Approved merchant account and business use case, KYC, bank details, enabled methods, backend credentials, signed webhooks, refunds and reconciliation |
| Fiat payment with seller receiving USDC | An approved crypto on-ramp, or an explicitly funded treasury settlement design | Country/method/token/network eligibility, user KYC where required, actual USDC delivery or treasury inventory, protected signer and gas, canonical purchase verification |
| Other cryptocurrencies | A supported swap/bridge provider such as LI.FI, then marketplace purchase | Supported source and destination chains/tokens, available liquidity, reviewed quotes, slippage/minimum received, approvals and gas on both sides |
| Seller paid EUR, INR or another fiat currency | Separate off-ramp or marketplace payout provider | Seller onboarding, supported destination bank/country/currency, conversion and payout fees, payout verification |

Razorpay's standard Indian payment-gateway settlement is INR, including supported
international payments. That is not an INR-to-USDC conversion service. Cashfree
also advertises international card acceptance with INR settlement. Neither should
be assumed to approve an NFT/crypto-related merchant: obtain approval for this
specific marketplace before designing around production availability.

Sources: [Razorpay settlement documentation](https://razorpay.com/docs/payments/settlements/),
[Cashfree international payments](https://www.cashfree.com/international-payment-gateway/),
[Cashfree supported payment methods](https://www.cashfree.com/support/),
[Transak integration and coverage discovery](https://docs.transak.com/integration/api),
[LI.FI quote API](https://docs.li.fi/li.fi-api/li.fi-api/requesting-a-quote).

## Required implementation, if authorized later

1. Select the seller settlement currency/token and supported countries first.
   Buyer payment currency, blockchain payment token and seller payout currency
   are separate choices. No provider supports every currency, coin or method.
2. Fetch server-side quotes with expiry, exact base-unit amounts and itemized
   costs. Show the final payer amount before authorization. Preserve DKM's
   existing seller-funded fee; do not add it to the buyer again.
3. Use hosted checkout and signed/idempotent backend webhooks. Never store raw
   card details. Reconcile provider order, payer, asset, amount and currency.
4. Confirm actual token delivery or treasury funding, then execute the marketplace
   purchase for the verified beneficiary. Provider success alone grants no access.
5. Verify a canonical purchase receipt and entitlement, including confirmations,
   reorg handling and retries. Record only non-sensitive references on-chain.
   A blockchain record of a fiat payment is an attestation; the fiat payment
   itself remains on the provider's payment rails.
6. Define listing reservation/expiry, failed-settlement refunds, chargebacks,
   inventory management and seller payout recovery. Token funding, purchase and
   bank payout must have separate states and transaction/order identifiers.

## Fees and testing

Payer total = asset value in payer currency + applicable external processing,
conversion, swap/bridge and network charges + applicable taxes on those charges.
Do not double-count costs already included in a provider quote. Passing charges
to the payer is subject to provider terms and applicable payment-method rules.
Seller proceeds = asset value minus DKM's existing seller fee and configured
royalties, with off-ramp charges disclosed separately if requested.

Use live provider quotes and the approved merchant pricing agreement instead of
promising a fixed fee. Small cent-priced purchases can fall below provider minima
or have fees larger than the purchase price. See
[Transak fee explanation](https://docs.transak.com/guides/partner-faqs) and
[LI.FI pricing explanation](https://help.li.fi/hc/en-us/articles/13304987014299-Can-you-share-some-insight-on-the-fees-structure-of-using-LI-FI-for-a-DApp).

For the present college demo, test POL pays gas and the deployed market's exact
MockUSDC token pays the asset price. Reducing the price does not reduce gas in
proportion, and real USDC or another test USDC contract is not interchangeable.
Transak staging delivers TRNSK for its documented ERC-20 sandbox flow, not DKM's
MockUSDC. Mainnet crypto cannot be assumed to bridge to Amoy demo tokens.
[Transak sandbox mapping](https://docs.transak.com/guides/sandbox-credentials).

No provider payout or coverage was tested for this research. Production approvals,
fees, supported routes and account eligibility must be rechecked before integration.
