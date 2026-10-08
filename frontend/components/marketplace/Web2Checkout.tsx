"use client";

import { api as backendApi } from "@/lib/api/client";
import { useAuth } from "@/providers/AuthProvider";
import Script from "next/script";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

type Order = {
  order_id: string; status: string; amount_usdc: number; provider_order_id: string | null;
  fiat_amount: number | null; fiat_currency: string | null; exchange_rate: string | null;
  checkout_key: string | null; settlement_tx_hash: string | null; error: string | null;
  provider_payment_id: string | null; recovery_status: string | null; refund_id: string | null;
};
type Confirmation = { razorpay_payment_id: string; razorpay_order_id: string; razorpay_signature: string };
type CheckoutOptions = {
  key: string; order_id: string; amount: number; currency: string; name: string;
  description: string; handler: (result: Confirmation) => void; modal: { ondismiss: () => void };
};
declare global { interface Window { Razorpay?: new (options: CheckoutOptions) => { open(): void }; } }


const labels: Record<string, string> = {
  CREATED: "Preparing payment", PENDING: "Awaiting payment", PROVIDER_CONFIRMED: "Payment verified — awaiting blockchain settlement",
  SETTLEMENT_PENDING: "Blockchain settlement pending", SETTLED: "Settled — checking entitlement",
  ENTITLEMENT_GRANTED: "Purchase entitlement verified", FAILED: "Payment failed",
};

async function request(path: string, body?: object): Promise<Order> {
  const result = await backendApi<{order: Order}>(`/api/payments/${path}`, {
    method: body ? "POST" : "GET", body: body ? JSON.stringify(body) : undefined,
  });
  return result.order;
}

export default function Web2Checkout({ tokenId, buyer, canStart }: { tokenId: bigint; buyer: `0x${string}`; canStart: boolean }) {
  const { user } = useAuth();
  const [capability, setCapability] = useState<{fiat_configured: boolean; fiat_message: string} | null>(null);
  useEffect(() => { backendApi<{fiat_configured: boolean; fiat_message: string}>("/api/capabilities").then(setCapability).catch(() => setError("Could not check payment availability.")); }, []);
  const [order, setOrder] = useState<Order | null>(null);
  const [method, setMethod] = useState("upi");
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [restoring, setRestoring] = useState(true);
  const cache = useQueryClient();


  useEffect(() => {
    let current = true;
    setRestoring(true); setOrder(null);
    backendApi<{order: Order | null}>(`/api/assets/${tokenId}/payment`).then(value => {
      if (current) { setOrder(value.order); setRestoring(false); }
    }).catch(() => { if (current) setError("Could not restore your payment status. Retry before creating another payment."); });
    return () => { current = false; };
  }, [tokenId, user?.id]);

  useEffect(() => {
    if (!order || order.recovery_status || ["FAILED", "ENTITLEMENT_GRANTED"].includes(order.status)) return;
    let current = true;
    const timer = setTimeout(async () => {
      try {
        const latest = await request(order.order_id);
        const value = !latest.recovery_status && ["PROVIDER_CONFIRMED", "SETTLEMENT_PENDING", "SETTLED"].includes(latest.status)
          ? await request(`${latest.order_id}/settle`, {}) : latest;
        if (current) { setOrder(value); if (value.status === "ENTITLEMENT_GRANTED") await cache.invalidateQueries(); }
      } catch { if (current) setError("Could not refresh payment status. Use Check status to retry."); }
    }, 5000);
    return () => { current = false; clearTimeout(timer); };
  }, [order, cache]);

  async function checkout() {
    setBusy(true); setError("");
    try {
      if (!ready || !window.Razorpay) throw new Error("Checkout is still loading. Try again shortly.");
      const value = order?.status === "PENDING" ? await request(order.order_id) : await request("create", {
        token_id: Number(tokenId), buyer_address: buyer, payment_method: method,
      });
      setOrder(value);
      // A new or resumed server order must be shown before opening the payment UI.
      if (order?.order_id !== value.order_id) { setBusy(false); return; }
      if (value.recovery_status || value.provider_payment_id || value.status !== "PENDING" || !value.checkout_key || !value.provider_order_id || !value.fiat_amount || !value.fiat_currency) {
        throw new Error(value.error || "Checkout is unavailable for this order.");
      }
      if (order && (order.fiat_amount !== value.fiat_amount || order.fiat_currency !== value.fiat_currency
          || order.amount_usdc !== value.amount_usdc || order.exchange_rate !== value.exchange_rate
          || order.provider_order_id !== value.provider_order_id || order.checkout_key !== value.checkout_key)) {
        throw new Error("Payment details changed. Review the updated total before continuing.");
      }
      new window.Razorpay({ key: value.checkout_key, order_id: value.provider_order_id,
        amount: value.fiat_amount, currency: value.fiat_currency, name: "DKM — Test payment",
        description: `Knowledge asset #${tokenId}`, modal: { ondismiss: () => { setBusy(false); setError("Checkout closed. You can resume this order."); } },
        handler: async result => {
          try { setOrder(await request(`${value.order_id}/confirm`, result)); }
          catch (err) { setError(err instanceof Error ? err.message : "Verification failed. Check status before paying again."); }
          finally { setBusy(false); }
        },
      }).open();
    } catch (err) { setError(err instanceof Error ? err.message : "Checkout unavailable."); setBusy(false); }
  }

  async function refresh() {

    setBusy(true); setError("");
    try {
      const saved = await backendApi<{order: Order | null}>(`/api/assets/${tokenId}/payment`);
      const value = saved.order;
      setRestoring(false);
      if (!value) { setOrder(null); return; }
      const id = value.order_id;
      setOrder(!value.recovery_status && (["PROVIDER_CONFIRMED", "SETTLEMENT_PENDING", "SETTLED"].includes(value.status) || value.status === "FAILED" && !!value.provider_payment_id)
        ? await request(`${id}/settle`, {}) : value);
    } catch (err) { setError(err instanceof Error ? err.message : "Status unavailable."); }
    finally { setBusy(false); }
  }

  if (!canStart && !order) return null;
  return <section className="mt-4 space-y-3 rounded border p-3" aria-label="UPI and card checkout">
    {capability?.fiat_configured && <Script src="https://checkout.razorpay.com/v1/checkout.js" onReady={() => setReady(true)} onError={() => setError("Unable to load checkout. Check your connection.")} />}
    <h3 className="font-semibold">UPI / Card — Test mode</h3>
    <p className="text-sm text-slate-600">Razorpay test checkout. No real INR is charged; settlement uses test USDC.</p>
    <p>{capability?.fiat_message || "Checking payment availability…"}</p>
    <label className="block">Payment method <select className="rounded border p-2" value={method} onChange={e => setMethod(e.target.value)} disabled={!!order}>
      <option value="upi">UPI</option><option value="card">Card</option>
    </select></label>
    <p className="text-sm">DKM’s platform fee is deducted from the seller’s asset proceeds. It is not added to your bill.</p>
    {!!order?.fiat_amount && <div className="space-y-2 rounded bg-slate-50 p-3" aria-label="Test payment breakdown">
      <p>Asset price: {order.amount_usdc} USDC</p>
      <p>Test exchange rate: ₹{order.exchange_rate} per USDC</p>
      <p>Additional DKM fee charged to you: ₹0</p>
      <p>External conversion, payment and network charges are not quoted in this test checkout. Production charges remain unavailable.</p>
      <p className="font-semibold">Total test payment: {(order.fiat_amount / 100).toFixed(2)} {order.fiat_currency}</p>
      <p className="text-sm">This is a fixed test amount, not a live conversion quote. No real INR is charged.</p>
    </div>}
    {canStart && !order?.recovery_status && (!order || order.status === "PENDING" || order.status === "FAILED" && !order.provider_payment_id) && <button className="rounded border px-3 py-2 disabled:opacity-50" disabled={busy || !ready || restoring || !capability?.fiat_configured} onClick={checkout}>{order?.status === "PENDING" ? "Continue to test payment" : "Review test payment"}</button>}
    {order && <>
      <p role="status">{order.recovery_status === "REFUNDED" ? "Full refund verified" : order.recovery_status === "REVIEW_REQUIRED" ? "Payment under review — do not pay again" : labels[order.status] || order.status}</p>
      <p className="break-all text-xs">Order: {order.order_id}</p>
      {order.refund_id && <p className="break-all text-xs">Refund: {order.refund_id}</p>}
      {order.settlement_tx_hash && <a className="block break-all text-sm underline" href={`https://amoy.polygonscan.com/tx/${order.settlement_tx_hash}`} target="_blank" rel="noreferrer">View settlement transaction</a>}
      {order.error && <p role="alert">{order.error}</p>}
    </>}
    <button className="rounded border px-3 py-2 disabled:opacity-50" disabled={busy} onClick={refresh}>Check status / Retry settlement</button>
    {error && <p className="text-red-600" role="alert">{error}</p>}
  </section>;
}
