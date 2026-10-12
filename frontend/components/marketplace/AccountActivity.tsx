"use client";
import Link from "next/link";
import { useState } from "react";
import { formatUnits } from "viem";
import { api } from "@/lib/api/client";
import { usePaymentCapabilities } from "@/lib/api/capabilities";

type Activity = { activity: { token_id: number; kind: string; amount_base_units: string; block: number; transaction_hash: string; log_index: number; payment_route: string; marketplace: string }[]; from_block: number; to_block: number; next_before_block: number | null };
export default function AccountActivity() {
  const { data: capabilities } = usePaymentCapabilities();
  const display = (market: string, amount: bigint) => {
    const profile = capabilities?.markets.find(value => value.address.toLowerCase() === market.toLowerCase());
    return profile ? `${formatUnits(amount, profile.decimals)} ${profile.symbol}` : `${amount} base units (token unverified)`;
  };
  const [data, setData] = useState<Activity | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [block, setBlock] = useState("");
  async function load(before?: number) { setBusy(true); setError(""); try { setData(await api(`/api/account/activity${before === undefined ? "" : `?before_block=${before}`}`)); } catch (err) { setError(err instanceof Error ? err.message : "Could not load history."); } finally { setBusy(false); } }
  return <section className="space-y-4"><h2 className="text-2xl font-semibold">On-chain purchases and sales</h2><p className="text-sm text-slate-600">Fixed-price transactions for your verified wallet across the current and configured previous marketplaces. Page size follows the RPC provider limit (currently 10 blocks). Sale amounts are gross; they do not deduct royalties or platform fees. Auction history is available on the Auctions page.</p>
    <form className="flex flex-wrap items-end gap-3" onSubmit={event => { event.preventDefault(); void load(block ? Number(block) : undefined); }}><label>End block (optional)<input className="ml-2 rounded border p-2" type="number" min="0" step="1" value={block} onChange={event => setBlock(event.target.value)} /></label><button disabled={busy} className="rounded border p-2">{busy ? "Loading…" : "Load history"}</button></form>
    {error && <p role="alert" className="text-red-700">{error}</p>}{data && <><p className="text-sm">Blocks {data.from_block}–{data.to_block}. Totals below apply only to this page.</p>
      {[...new Set(data.activity.map(item => item.marketplace.toLowerCase()))].map(market => <p key={market} className="break-all">Gross sales ({market}): {display(market, data.activity.filter(item => item.kind === "sale" && item.marketplace.toLowerCase() === market).reduce((sum, item) => sum + BigInt(item.amount_base_units), 0n))}</p>)}
      {!data.activity.length && <p>No fixed-price activity in this block range.</p>}{data.activity.map(item => <article className="space-y-2 rounded border p-4" key={`${item.marketplace}:${item.transaction_hash}:${item.log_index}`}><Link href={`/marketplace#asset-${item.token_id}`} className="underline">Asset #{item.token_id}</Link><p className="break-all text-xs">Marketplace: {item.marketplace}</p><p>{item.kind === "sale" ? "Sale" : "Purchase"} · {display(item.marketplace, BigInt(item.amount_base_units))} · {item.payment_route}</p><a href={`https://amoy.polygonscan.com/tx/${item.transaction_hash}`} target="_blank" rel="noreferrer" className="underline">View blockchain transaction</a></article>)}{data.next_before_block !== null && <button disabled={busy} className="rounded border p-2" onClick={() => load(data.next_before_block!)}>Earlier blocks</button>}</>}
  </section>;
}
