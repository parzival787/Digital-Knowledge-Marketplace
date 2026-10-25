"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import { formatUnits } from "viem";

type Coverage = { fiat: { symbol: string; methods: { id: string; name: string; buy: boolean }[] }[] };
type Funding = { id: string; terms: { buyer_token_total_base_units: string }; quote: {
  fiatCurrency: string; fiatAmount: string; cryptoAmount: string; totalFee: string;
  fetched_at: number; freshness_seconds: number; fees: { name: string; amount: string }[];
} };

export default function AssetFunding({ tokenId }: { tokenId: bigint }) {
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [currency, setCurrency] = useState("");
  const [method, setMethod] = useState("");
  const [funding, setFunding] = useState<Funding | null>(null);
  const [orderId, setOrderId] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { let active = true;
    api<Coverage>("/api/payments/transak/coverage").then(value => { if (active) setCoverage(value); })
      .catch(() => { if (active) setError("Provider payment methods could not be verified."); });
    return () => { active = false; };
  }, []);
  async function run(action: "quote" | "session" | "verify") {
    setBusy(true); setError("");
    try {
      if (action === "quote") {
        setFunding(await api<Funding>("/api/payments/transak/asset-funding", {method:"POST",body:JSON.stringify({token_id:tokenId.toString(),fiat_currency:currency,payment_method:method})}));
      } else if (action === "session" && funding) {
        const value = await api<{widget_url:string}>(`/api/payments/transak/asset-funding/${funding.id}/session`,{method:"POST"});
        const url = new URL(value.widget_url);
        if (url.origin !== "https://global-stg.transak.com") throw new Error("Unexpected provider checkout.");
        window.location.assign(url.href);
      } else if (action === "verify") {
        setStatus("");
        const receipt = await api<{funding_id?:string;funding_state?:string;asset_token_id?:string}>("/api/payments/transak/orders/refresh",{method:"POST",body:JSON.stringify({order_id:orderId.trim()})});
        if (String(receipt.asset_token_id) !== tokenId.toString()) throw new Error("Order does not fund this asset.");
        if (funding && receipt.funding_id !== funding.id) throw new Error("Order belongs to another funding session.");
        setStatus(receipt.funding_state === "wallet_funded" ? "Wallet funded. Review the asset price, then approve tokens and buy separately." :
          receipt.funding_state === "review_required" ? "Provider evidence needs review. Do not pay again." : "Provider checked; blockchain delivery is not verified yet. No asset access granted.");
      }
    } catch (err) { setError(err instanceof Error ? err.message : "Funding unavailable."); }
    finally { setBusy(false); }
  }
  return <section className="space-y-3 rounded border p-3" aria-label="Fund this purchase">
    <h3 className="font-semibold">Fund this TRNSK purchase</h3>
    <p>Transak staging requests USDC on Polygon and delivers TRNSK on Amoy. This funds your wallet; it does not buy or reserve the asset. Amoy test POL is still required for wallet gas.</p>
    <label className="block">Pay currency<select className="ml-2 rounded border p-2" value={currency} onChange={e=>{setCurrency(e.target.value);setMethod("");setFunding(null);}}><option value="">Choose supported currency</option>{coverage?.fiat.filter(c=>c.methods.some(m=>m.buy)).map(c=><option key={c.symbol}>{c.symbol}</option>)}</select></label>
    <label className="block">Payment method<select className="ml-2 rounded border p-2" value={method} onChange={e=>{setMethod(e.target.value);setFunding(null);}}><option value="">Choose supported method</option>{coverage?.fiat.find(c=>c.symbol===currency)?.methods.filter(m=>m.buy).map(m=><option key={m.id} value={m.id}>{m.name}</option>)}</select></label>
    <p>UPI is available only when explicitly offered for your selected currency. Provider eligibility is checked again before opening checkout.</p>
    <button className="rounded border p-2 disabled:opacity-50" disabled={busy||!method} onClick={()=>run("quote")}>Get funding quote</button>
    {funding&&<div className="space-y-2 rounded bg-slate-50 p-3"><p>Listing needs {formatUnits(BigInt(funding.terms.buyer_token_total_base_units),18)} TRNSK.</p>
      <p>Total: {funding.quote.fiatAmount} {funding.quote.fiatCurrency}. Expected staging output: {funding.quote.cryptoAmount} TRNSK.</p>
      <p>Provider fees included: {funding.quote.totalFee} {funding.quote.fiatCurrency}.</p>{funding.quote.fees.map((fee,i)=><p key={i}>{fee.name}: {fee.amount}</p>)}
      <p>No additional DKM buyer fee. DKM’s seller deduction is shown in the separate purchase review. Provider output may change; actual token delivery is verified before reporting funding.</p>
      <p>Quote freshness: {funding.quote.freshness_seconds} seconds. Final provider terms appear in hosted checkout.</p>
      <button className="rounded border p-2" disabled={busy} onClick={()=>run("session")}>Accept funding quote and open sandbox</button></div>}
    <label className="block">Provider order ID after checkout<input className="w-full rounded border p-2" value={orderId} onChange={e=>setOrderId(e.target.value)} /></label>
    <button className="rounded border p-2" disabled={busy||!orderId.trim()} onClick={()=>run("verify")}>Verify provider and blockchain delivery</button>
    {status&&<p role="status">{status}</p>}{error&&<p role="alert">{error}</p>}
  </section>;
}
