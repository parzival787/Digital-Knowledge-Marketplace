"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
type History={notice:string;coverage:{market:string;deployment_block:number;next_block:number;state:string;error:string|null}[];totals:{token:string;gross:string;fee:string;royalties:string;net:string}[];events:{market:string;kind:string;block:number;tx_hash:string;log_index:number;args:Record<string,string>;accounting:{gross:string;platform_fee:string;royalties:string;seller_net:string}|null}[]};
export default function IndexedActivity(){
  const [data,setData]=useState<History|null>(null),[error,setError]=useState("");
  async function refresh(){try{setData(await api<History>("/api/account/indexed-activity"));setError("");}catch{setError("Could not load indexed history.");}}
  useEffect(()=>{void refresh();},[]);
  return <section className="space-y-4"><h2 className="text-2xl font-semibold">Confirmed marketplace history</h2><button className="underline" onClick={refresh}>Refresh indexed history</button>{error&&<p role="alert">{error}</p>}
    {data&&<><p>{data.notice}</p>{data.coverage.map(c=><p key={c.market} className="break-all text-sm">Market {c.market}: {c.state}, blocks {c.deployment_block}–{c.next_block-1}. {c.error}</p>)}
      {!data.coverage.length&&<p>History is awaiting its first successful synchronization.</p>}
      {data.totals.map(t=><div key={t.token} className="rounded border p-4"><p className="break-all">Seller proceeds for token {t.token} (integer base units)</p><p>Gross: {t.gross}; platform fee: {t.fee}; royalties: {t.royalties}; net: {t.net}.</p></div>)}
      <p>Latest 200 matching events. Bid deposits are not counted as sales.</p>
      {data.events.map(e=><article key={`${e.market}-${e.tx_hash}-${e.log_index}`} className="rounded border p-3"><p>{e.kind} · {e.args.tokenId?`Asset #${e.args.tokenId}`:"Refund / listing"} · Block {e.block}</p>{e.args.amount&&<p>Amount: {e.args.amount} base units</p>}<a className="underline" href={`https://amoy.polygonscan.com/tx/${e.tx_hash}`} target="_blank" rel="noreferrer">View transaction</a></article>)}
    </>}
  </section>;
}
