"use client";
import { useEffect, useState } from "react";
import { formatUnits } from "viem";
import { api } from "@/lib/api/client";
import { useAuth } from "@/providers/AuthProvider";
type Sale = {market:string;tx_hash:string;log_index:number;args:{tokenId?:string};accounting:{token:string;seller_net:string;seller:string}|null};
type Quote = {id:string;quote:{fiatAmount:string;fiatCurrency:string;cryptoAmount:string;totalFee:string;fees:{name:string;amount:string}[]}};
export default function SalePayout({currency, enabled}:{currency:string;enabled:boolean}) {
  const {user}=useAuth();
  const [sales,setSales]=useState<Sale[]>([]),[methods,setMethods]=useState<{id:string;name:string}[]>([]);
  const [selected,setSelected]=useState(""),[method,setMethod]=useState(""),[quote,setQuote]=useState<Quote|null>(null);
  const [error,setError]=useState(""),[busy,setBusy]=useState(false);
  useEffect(()=>{let active=true;setQuote(null);setMethods([]);setMethod("");
    if(enabled&&currency!=="USDC") Promise.all([
      api<{events:Sale[]}>("/api/account/indexed-activity"),
      api<{fiat:{symbol:string;methods:{id:string;name:string;sell:boolean}[]}[]}>("/api/payments/transak/coverage")
    ]).then(([history,coverage])=>{if(active){setSales(history.events.filter(e=>e.accounting?.token.toLowerCase()==="0x0c86a754a29714c4fe9c6f1359fa7099ed174c0b"&&e.accounting.seller.toLowerCase()===user?.wallet_address?.toLowerCase()));setMethods(coverage.fiat.find(c=>c.symbol===currency)?.methods.filter(m=>m.sell)??[]);}})
      .catch(()=>{if(active)setError("Could not verify sale proceeds and payout coverage.");});
    return()=>{active=false;};
  },[currency,enabled,user?.wallet_address]);
  async function act(open:boolean){setBusy(true);setError("");try{
    if(open&&quote){const session=await api<{widget_url:string;environment:string}>(`/api/payments/transak/sale-payouts/${quote.id}/session`,{method:"POST"});const url=new URL(session.widget_url);if(session.environment!=="staging"||url.origin!=="https://global-stg.transak.com")throw new Error("Unexpected payout session.");window.location.assign(url.href);}
    else {const sale=sales[Number(selected)];if(selected===""||!sale)throw new Error("Select a verified sale.");setQuote(await api<Quote>("/api/payments/transak/sale-payouts/quote",{method:"POST",body:JSON.stringify({market:sale.market,transaction_hash:sale.tx_hash,log_index:sale.log_index,currency,payment_method:method})}));}
  }catch(e){setError(e instanceof Error?e.message:"Payout unavailable.");}finally{setBusy(false);}}
  return <section className="space-y-3 rounded border p-3"><h3 className="font-semibold">Withdraw verified TRNSK sale proceeds</h3>
    <p>Only verified seller proceeds qualify. Provider SELL status and outgoing token verification are separate; neither changes buyer access.</p>
    {!methods.length&&<p>No verified payout method for this saved currency. Choose another supported preference or keep your tokens.</p>}
    <label className="block">Sale<select value={selected} onChange={e=>{setSelected(e.target.value);setQuote(null);}} className="ml-2 border p-2"><option value="">Choose sale</option>{sales.map((s,i)=><option key={`${s.market}:${s.tx_hash}:${s.log_index}`} value={i}>Asset {s.args.tokenId} · {formatUnits(BigInt(s.accounting!.seller_net),18)} TRNSK</option>)}</select></label>
    <label className="block">Payout method<select value={method} onChange={e=>{setMethod(e.target.value);setQuote(null);}} className="ml-2 border p-2"><option value="">Choose method</option>{methods.map(m=><option key={m.id} value={m.id}>{m.name}</option>)}</select></label>
    <button disabled={!enabled||busy||selected===""||!method} onClick={()=>act(false)} className="rounded border p-2">Review withdrawal quote</button>
    {quote&&<div><p>Send {quote.quote.cryptoAmount} TRNSK. Provider payout quote: {quote.quote.fiatAmount} {quote.quote.fiatCurrency}; provider fees: {quote.quote.totalFee}.</p>{quote.quote.fees.map((f,i)=><p key={i}>{f.name}: {f.amount}</p>)}<p>Review within 60 seconds. Transak displays USDC for its TRNSK sandbox route. Use documented test payout details only.</p><button disabled={busy||!enabled} onClick={()=>act(true)} className="rounded border p-2">Accept quote and open withdrawal sandbox</button></div>}
    {error&&<p role="alert">{error}</p>}
  </section>;
}
