"use client";
import Link from "next/link";
import TransakOrders from "@/components/marketplace/TransakOrders";
import TransakFunding from "@/components/marketplace/TransakFunding";
import PaymentCapabilities from "@/components/marketplace/PaymentCapabilities";
import { useAccount, useBalance } from "wagmi";
import { polygonAmoy } from "viem/chains";
import { AccountGate } from "@/providers/AuthProvider";
import { usePaymentCapabilities } from "@/lib/api/capabilities";

export default function FundingPage() {
  const { address } = useAccount();
  const { data: capabilities } = usePaymentCapabilities();
  const profile = capabilities?.markets.find(m => m.current);
  const { data } = useBalance({ address, chainId: polygonAmoy.id });
  return <main className="mx-auto max-w-2xl space-y-6 px-6 py-12">
    <h1 className="text-3xl font-bold">Fund your demo wallet</h1>
    <PaymentCapabilities />
    <p>Each marketplace accepts its configured payment token. The current market accepts {profile?.symbol ?? "a token being verified"}; Amoy test POL pays the network fee.</p>
    <section className="space-y-2 rounded-xl border p-5" aria-labelledby="fees-title">
      <h2 id="fees-title" className="text-xl font-semibold">What you will pay</h2>
      <p>The asset price plus external payment, conversion and network charges, including applicable taxes on those charges. A live quote must show the total before you confirm.</p>
      <p>DKM’s platform fee comes out of the seller’s asset proceeds. It is not an extra charge to you.</p>
      <p className="text-sm text-slate-600">Start from a TRNSK listing to obtain a current provider quote. Costs included in the provider total are not added twice. Wallet gas is separate.</p>
    </section>
    <section id="crypto" className="space-y-3 rounded-xl border p-5" aria-labelledby="crypto-title">
      <h2 id="crypto-title" className="text-xl font-semibold">Use another cryptocurrency</h2>
      <p>Have ETH or another supported token? The planned swap and bridge option will convert it into USDC in your verified wallet before you buy.</p>
      <ol className="list-decimal space-y-2 pl-5"><li>Select your source network and token.</li><li>Review the amount, fees, minimum USDC received and gas funding.</li><li>Confirm the conversion in your wallet, then return to purchase or bid.</li></ol>
      <p role="status" className="rounded bg-amber-50 p-3">Unavailable on this demo: there is no verified swap/bridge route to the Amoy test tokens. Do not send real cryptocurrency.</p>
      <button disabled aria-describedby="crypto-unavailable" className="rounded border px-4 py-2 opacity-50">Find a swap / bridge route</button>
      <p id="crypto-unavailable" className="text-sm text-slate-600">Requires a supported production deployment and an enabled route integration. No transfer will be started here.</p>
      <p className="text-sm text-slate-600">Only tokens and networks with an available route can be supported. Source-network fees may still require its native token. Destination POL funding must be included or checked before purchase.</p>
    </section>
    <section id="fiat" className="space-y-3 rounded-xl border p-5" aria-labelledby="fiat-title">
      <h2 id="fiat-title" className="text-xl font-semibold">Provider sandbox funding</h2>
      <p>Choose an asset that accepts TRNSK and use “Fund this TRNSK purchase” to review currently offered currencies, payment methods and fees. INR/UPI are unavailable unless the runtime provider lookup and quote explicitly offer them. Razorpay test checkout is a separate prefunded settlement demonstration.</p>
    </section>
    <AccountGate wallet>
      <TransakFunding />
      <TransakOrders />
      <section className="space-y-3 rounded border p-5" aria-label="Wallet funding availability">
        <h2 className="text-xl font-semibold">Current demo wallet</h2>
        <p className="break-all">Destination wallet: {address}</p>
        <p>Network: Polygon Amoy testnet</p>
        <p>Current payment token: {profile?.symbol ?? "Checking…"}. Do not send real USDC or real INR for this demo.</p>
        <p>Gas balance: {data ? `${data.formatted} POL` : "Checking..."}</p>
        <p>You need Amoy test POL for approvals, purchases and bids. ERC-20 payment tokens cannot pay these fees.</p>
        <p>Transak sandbox quotes apply only to its test flow. A quote is not a completed funding or purchase transaction.</p>

      </section>
    </AccountGate>
    <p>Adding funds does not purchase or reserve an asset or place an auction bid. After funding, return to the marketplace, review the current price and sign the purchase or bid in your wallet.</p>
    <Link href="/marketplace" className="block underline">Return to marketplace</Link>
    <Link href="/auctions" className="block underline">Browse auctions</Link>
  </main>;
}
