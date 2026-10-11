"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
type Item={market:string;token_id:string;id?:string;amount?:string;active?:boolean;state?:string;role?:string;purchase_count?:string};
type Snapshot={block:number;page:number;has_more:boolean;entitlements:Item[];listings:Item[];auctions:Item[];refunds:{market:string;amount:string}[]};
export default function Positions(){
  const [data,setData]=useState<Snapshot|null>(null),[page,setPage]=useState(0),[error,setError]=useState("");
  useEffect(()=>{let active=true;setData(null);setError("");api<Snapshot>(`/api/account/positions?page=${page}`).then(value=>{if(active)setData(value);}).catch(()=>{if(active)setError("Could not verify current positions. Reload to retry.");});return()=>{active=false;};},[page]);
  return <section className="space-y-4"><h2 className="text-2xl font-semibold">Your licenses and marketplace positions</h2>
    <p>Current and previous marketplaces, checked directly on the blockchain. Each page scans 10 asset, listing and auction IDs. Earlier bids appear in confirmed marketplace history. Amounts are token base units.</p>
    {error&&<p role="alert">{error}</p>}{!data&&!error&&<p role="status">Checking your wallet’s positions…</p>}
    {data&&<><p>Confirmed block {data.block} · Page {page+1}</p>{([['entitlements','Purchase licenses'],['listings','Your fixed listings'],['auctions','Your auctions and highest bids']] as const).map(([key,label])=><div key={key}><h3 className="font-semibold">{label}</h3>{!data[key].length&&<p>No matching positions on this page.</p>}{data[key].map(row=><article className="rounded border p-3" key={`${row.market}-${row.id||row.token_id}`}><Link className="underline" href={key==='auctions'?'/auctions':`/marketplace#asset-${row.token_id}`}>Asset #{row.token_id}</Link><p>{row.state|| (key==='listings'?(row.active?'Active':'Inactive'):`${row.purchase_count} purchase(s)`) } {row.role} {row.amount&&`· ${row.amount} base units`}</p><p className="break-all text-xs">Marketplace: {row.market}</p></article>)}</div>)}
      <h3 className="font-semibold">Refundable auction balances</h3>{data.refunds.map(row=><p className="break-all" key={row.market}>{row.amount} base units · {row.market}</p>)}<Link className="underline" href="/auctions">Manage auctions and withdraw refunds</Link>
      <div className="flex gap-4"><button disabled={page===0} onClick={()=>setPage(page-1)}>Previous page</button><button disabled={!data.has_more} onClick={()=>setPage(page+1)}>Next page</button></div></>}
  </section>;
}
