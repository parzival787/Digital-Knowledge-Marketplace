"use client";
import Link from "next/link";
import { useState } from "react";
import { useReadContract } from "wagmi";
import { marketplaceContract } from "@/lib/blockchain/contracts";
import AuctionPanel from "@/components/marketplace/AuctionPanel";

export default function AuctionsPage() {
  const [page, setPage] = useState(0);
  const { data, isLoading, isError } = useReadContract({ ...marketplaceContract, chainId: 80002, functionName: "totalAuctionsCreated", query: { refetchInterval: 10000 } });
  const total = Number(data || 0);
  const ids = Array.from({ length: Math.min(12, Math.max(0, total - page * 12)) }, (_, i) => BigInt(total - page * 12 - i));
  return <main className="mx-auto max-w-5xl space-y-6 px-6 py-12"><h1 className="text-3xl font-bold">Auctions</h1><p>Browse current and completed auctions, place bids, finalize ended auctions and withdraw refundable bids.</p><p><Link className="underline" href="/marketplace">Create an auction from an asset you own in Marketplace.</Link> <Link className="underline" href="/account">Verify your wallet</Link> before taking part.</p>{isLoading && <p role="status">Loading auctions…</p>}{isError && <p role="alert">Unable to load auctions. Check your connection and retry.</p>}{!isLoading && !isError && total === 0 && <p className="rounded-xl border p-6">No auctions have been created yet.</p>}<div className="grid gap-4 md:grid-cols-2">{ids.map(id => <AuctionPanel key={id.toString()} tokenId={0n} auctionId={id} price={0n} canCreate={false} />)}</div>{total > 12 && <div className="flex items-center gap-4"><button className="rounded border p-2" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page + 1}</span><button className="rounded border p-2" disabled={(page + 1) * 12 >= total} onClick={() => setPage(page + 1)}>Next</button></div>}</main>;
}
