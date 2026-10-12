"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";

type Receipt = {
  order_id: string; status: string; fiat_currency: string; fiat_amount: string | null;
  amount_paid: string | null; provider_fee: string | null; crypto_amount: string | null;
  transaction_hash: string | null; checked_at?: string;
  verification_state?: string; observed_status?: string; refresh_error?: string | null;
  funding_state?: string; chain_delivery_state?: string; asset_token_id?: string;
};
export default function TransakOrders() {
  const [orders, setOrders] = useState<Receipt[]>([]);
  const [id, setId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function load() {
    const result = await api<{ orders: Receipt[] }>("/api/payments/transak/orders");
    setOrders(result.orders);
  }
  useEffect(() => { void load().catch(() => setError("Could not load your sandbox history.")); }, []);
  async function refresh(orderId: string) {
    setBusy(true); setError("");
    try {
      await api("/api/payments/transak/orders/refresh", { method: "POST", body: JSON.stringify({ order_id: orderId.trim() }) });
      await load(); setId("");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not verify the sandbox order."); }
    finally { setBusy(false); }
  }
  return <section className="space-y-3 rounded-xl border p-5" aria-labelledby="transak-orders-title">
    <h2 id="transak-orders-title" className="text-xl font-semibold">Your Transak sandbox orders</h2>
    <p>After checkout, copy its order ID here. We verify it with Transak and save its status for your account. This does not purchase a knowledge asset.</p>
    <p className="text-sm">Saved orders are rechecked periodically while the backend is running. Refresh this view to see the latest saved evidence.</p>
    <form onSubmit={event => { event.preventDefault(); void refresh(id); }} className="space-y-2">
      <label htmlFor="transak-order-id" className="block">Transak order ID</label>
      <input id="transak-order-id" value={id} onChange={event => setId(event.target.value)} required maxLength={36}
        pattern="[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        className="w-full rounded border p-2" />
      <button disabled={busy || !id.trim()} className="rounded border px-4 py-2 disabled:opacity-50">Verify sandbox order</button>
    </form>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {orders.length === 0 && <p>No verified sandbox orders saved yet.</p>}
    {orders.map(order => <article key={order.order_id} className="space-y-2 border-t pt-3">
      <p className="break-all">Order: {order.order_id}</p>
      <p>Provider status: {order.status}</p>
      {order.funding_state && <p>Asset #{order.asset_token_id} funding: {order.funding_state.replaceAll("_", " ")}. Blockchain delivery: {order.chain_delivery_state?.replaceAll("_", " ")}. A separate marketplace purchase is required for access.</p>}
      {order.verification_state === "review_required" && <p role="alert" className="text-amber-800">Provider evidence conflicts with a previous result. Review required; last observed status: {order.observed_status}. Do not treat this as a completed marketplace payment.</p>}
      {order.refresh_error && <p role="status">{order.refresh_error}</p>}
      <p>Quoted amount: {order.fiat_amount ?? "Unavailable"} {order.fiat_currency}</p>
      <p>Amount paid: {order.amount_paid ?? "Unavailable"} {order.fiat_currency}</p>
      <p>Provider fees reported: {order.provider_fee ?? "Unavailable"} {order.fiat_currency} — do not add these again to the provider total.</p>
      <p>Provider-reported test token amount: {order.crypto_amount ?? "Unavailable"}</p>
      {order.transaction_hash && <a className="block underline" target="_blank" rel="noreferrer"
        href={`https://amoy.polygonscan.com/tx/${order.transaction_hash}`}>Inspect provider-reported test transaction</a>}
      <p className="text-sm">Staging only. Provider status and transaction details are not independent blockchain verification or marketplace access.</p>
      {order.checked_at && <p className="text-sm">Last verified: {new Date(order.checked_at).toLocaleString()}</p>}
      <button disabled={busy} onClick={() => void refresh(order.order_id)} className="rounded border px-3 py-1 disabled:opacity-50">Refresh status</button>
    </article>)}
  </section>;
}
