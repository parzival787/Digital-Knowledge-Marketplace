"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
type Payout = {id:string;currency:string;order_id:string|null;state:string;error:string|null;checked_at:string|null;receipt:{status:string;fiat_amount:string|null;fiat_currency:string;provider_fee:string|null}|null};
export default function PayoutHistory() {
  const [rows,setRows]=useState<Payout[]>([]),[error,setError]=useState(""),[busy,setBusy]=useState(false);
  async function load(){setRows((await api<{payouts:Payout[]}>("/api/payments/transak/payouts")).payouts);}
  useEffect(()=>{load().catch(()=>setError("Could not load payout history."));},[]);
  async function refresh(id:string,order_id:string){setBusy(true);setError("");try{await api(`/api/payments/transak/payouts/${id}/refresh`,{method:"POST",body:JSON.stringify({order_id})});await load();}catch(e){setError(e instanceof Error?e.message:"Verification unavailable.");}finally{setBusy(false);}}
  return <section className="space-y-4 rounded-xl border p-6"><h2 className="text-xl font-semibold">Seller payout history — sandbox</h2>
    <p>Latest 100 withdrawal sessions. Session creation is not a completed payout. Provider status never changes buyer access.</p>
    {error&&<p role="alert">{error}</p>}{!rows.length&&<p>No saved withdrawal sessions.</p>}
    {rows.map(row=><article key={row.id} className="space-y-2 border-t pt-3"><p>Requested currency: {row.currency} · {row.state.replaceAll("_"," ")}</p>
      {row.receipt&&<p>Last accepted provider status: {row.receipt.status}. Provider fiat amount: {row.receipt.fiat_amount??"Not supplied"} {row.receipt.fiat_currency}; fee: {row.receipt.provider_fee??"Not supplied"}.</p>}
      {row.state==="review_required"&&<p role="alert">Conflicting evidence requires operator review; payout completion is not confirmed.</p>}
      {row.error&&<p role="alert">{row.error}</p>}{row.checked_at&&<p>Last checked: {new Date(row.checked_at).toLocaleString()}</p>}
      <form onSubmit={e=>{e.preventDefault();void refresh(row.id,String(new FormData(e.currentTarget).get("order")));}} className="flex flex-wrap gap-3"><label>Transak SELL order ID<input name="order" required defaultValue={row.order_id??""} readOnly={!!row.order_id} className="ml-2 rounded border p-2" /></label><button disabled={busy} className="rounded border p-2">Verify provider status</button></form>
    </article>)}
  </section>;
}
