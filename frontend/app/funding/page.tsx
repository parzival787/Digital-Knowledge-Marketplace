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
    <p role="status" className="rounded border bg-amber-50 p-4">INR wallet funding is unavailable. A provider approved for Indian customers and INR payments has not been configured.</p>
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
