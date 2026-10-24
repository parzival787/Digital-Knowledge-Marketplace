"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
type History={enabled:boolean;records:{id:string;token_id:number;state:string;reversal_status:number;tx_hash:string|null;error:string|null}[]};
export default function RecordingHistory(){
  const [data,setData]=useState<History|null>(null),[error,setError]=useState("");
  useEffect(()=>{api<History>("/api/payments/recordings").then(setData).catch(()=>setError("Could not load blockchain audit status."));},[]);
  return <section className="space-y-3 rounded-xl border p-6"><h2 className="text-xl font-semibold">Blockchain audit records</h2>
    <p>Audit evidence does not grant access or move money. Marketplace entitlement controls downloads.</p>
    {error&&<p role="alert">{error}</p>}{data&&!data.enabled&&<p>Recording is disabled pending an approved registry deployment.</p>}
    {data?.records.length===0&&<p>No verified purchase/payout evidence has been queued for recording.</p>}
    {data?.records.map(row=><article key={row.id}><p>Asset #{row.token_id} · {row.reversal_status?"Reversal":"Payment"} · {row.state.replaceAll("_"," ")}</p>{row.error&&<p role="alert">{row.error}</p>}{row.tx_hash&&<a className="underline" href={`https://amoy.polygonscan.com/tx/${row.tx_hash}`} target="_blank" rel="noreferrer">View audit transaction</a>}</article>)}
  </section>;
}
