"use client";
import Link from "next/link";
import { useAccount, useBalance } from "wagmi";
import { polygonAmoy } from "viem/chains";
import { AccountGate } from "@/providers/AuthProvider";

export default function FundingPage() {
  const { address } = useAccount();
  const { data } = useBalance({ address, chainId: polygonAmoy.id });
  return <main className="mx-auto max-w-2xl space-y-6 px-6 py-12">
    <h1 className="text-3xl font-bold">Add USDC</h1>
    <p>Choose how to fund your wallet. Marketplace purchases are priced in USDC; POL pays the network fee.</p>
    <section className="space-y-2 rounded-xl border p-5" aria-labelledby="fees-title">
      <h2 id="fees-title" className="text-xl font-semibold">What you will pay</h2>
      <p>The asset price plus external payment, conversion and network charges, including applicable taxes on those charges. A live quote must show the total before you confirm.</p>
      <p>DKM’s platform fee comes out of the seller’s asset proceeds. It is not an extra charge to you.</p>
      <p className="text-sm text-slate-600">Provider charges are currently unavailable. Costs already included in a provider’s rate or total must not be added twice. Network fees paid separately by your wallet will be shown separately.</p>
    </section>
    <section id="crypto" className="space-y-3 rounded-xl border p-5" aria-labelledby="crypto-title">
      <h2 id="crypto-title" className="text-xl font-semibold">Use another cryptocurrency</h2>
      <p>Have ETH or another supported token? The planned swap and bridge option will convert it into USDC in your verified wallet before you buy.</p>
      <ol className="list-decimal space-y-2 pl-5"><li>Select your source network and token.</li><li>Review the amount, fees, minimum USDC received and gas funding.</li><li>Confirm the conversion in your wallet, then return to purchase or bid.</li></ol>
      <p role="status" className="rounded bg-amber-50 p-3">Unavailable on this demo: Polygon Amoy and MockUSDC are not supported by the selected swap and bridge integration target. Do not send real crypto to fund this demo.</p>
      <button disabled aria-describedby="crypto-unavailable" className="rounded border px-4 py-2 opacity-50">Find a swap / bridge route</button>
      <p id="crypto-unavailable" className="text-sm text-slate-600">Requires a supported production deployment and an enabled route integration. No transfer will be started here.</p>
      <p className="text-sm text-slate-600">Only tokens and networks with an available route can be supported. Source-network fees may still require its native token. Destination POL funding must be included or checked before purchase.</p>
    </section>
    <section id="fiat" className="space-y-3 rounded-xl border p-5" aria-labelledby="fiat-title">
      <h2 id="fiat-title" className="text-xl font-semibold">Buy USDC with INR</h2>
      <p role="status">INR wallet funding is unavailable. A provider approved for Indian customers and INR payments has not been configured.</p>
    </section>
    <AccountGate wallet>
      <section className="space-y-3 rounded border p-5" aria-label="Wallet funding availability">
        <h2 className="text-xl font-semibold">Current demo wallet</h2>
        <p className="break-all">Destination wallet: {address}</p>
        <p>Network: Polygon Amoy testnet</p>
        <p>Asset: MockUSDC test token. Do not send real USDC or real INR for this demo.</p>
        <p>Gas balance: {data ? `${data.formatted} POL` : "Checking..."}</p>
        <p>You need Amoy test POL for approvals, purchases and bids. MockUSDC alone cannot pay these fees.</p>
        <p>No provider quote is available, so no INR amount, provider fees, received USDC, expiry or refund terms can be offered.</p>
        <button disabled className="rounded border px-4 py-2 opacity-50" aria-describedby="funding-disabled">Continue to provider</button>
        <p id="funding-disabled" className="text-sm">Unavailable until provider and network support are verified.</p>
      </section>
    </AccountGate>
    <p>Adding funds does not purchase or reserve an asset or place an auction bid. After funding, return to the marketplace, review the current price and sign the purchase or bid in your wallet.</p>
    <Link href="/marketplace" className="block underline">Return to marketplace</Link>
    <Link href="/auctions" className="block underline">Browse auctions</Link>
  </main>;
}
