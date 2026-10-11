"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AccountGate, useAuth } from "@/providers/AuthProvider";
import { api } from "@/lib/api/client";
import AccountActivity from "@/components/marketplace/AccountActivity";
import PayoutHistory from "@/components/marketplace/PayoutHistory";
import RecordingHistory from "@/components/marketplace/RecordingHistory";
import IndexedActivity from "@/components/marketplace/IndexedActivity";
import TransakOrders from "@/components/marketplace/TransakOrders";
import SellerPayout from "@/components/marketplace/SellerPayout";
import ReviewHistory from "@/components/marketplace/ReviewHistory";
import Positions from "@/components/marketplace/Positions";

type Asset = { vector_id: string; title: string; token_id: number | null; price_usdc: number };
type Order = { order_id: string; token_id: number; payment_method: string; amount_usdc: number; status: string; error: string | null; settlement_tx_hash: string | null; provider_payment_id: string | null; recovery_status: string | null };
function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState<{ assets: Asset[]; orders: Order[] } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function refresh() { setData(await api("/api/account/dashboard")); }
  useEffect(() => { let active = true; api<{ assets: Asset[]; orders: Order[] }>("/api/account/dashboard").then(value => { if (active) setData(value); }).catch(() => { if (active) setError("Could not load your dashboard. Please retry."); }); return () => { active = false; }; }, [user?.id]);
  async function run(action: () => Promise<unknown>) { setBusy(true); setError(""); try { await action(); await refresh(); } catch (err) { setError(err instanceof Error ? err.message : "Request failed."); } finally { setBusy(false); } }
  return <div className="space-y-8"><div className="flex flex-wrap gap-5"><Link className="underline" href="/mint">Create asset</Link><Link className="underline" href="/marketplace">Browse marketplace</Link><Link className="underline" href="/account">Manage verified wallet</Link><button disabled={busy} className="underline" onClick={() => run(async () => {})}>Refresh</button></div>{error && <p role="alert" className="text-red-700">{error}</p>}{!data && !error && <p role="status">Loading your workspace…</p>}
    <section className="space-y-4"><h2 className="text-2xl font-semibold">Your uploads</h2>{data?.assets.length === 0 && <p>No uploads yet. Create your first knowledge asset.</p>}{data?.assets.map(asset => <article key={asset.vector_id} className="space-y-3 rounded-xl border p-5"><h3 className="font-semibold">{asset.title || "Untitled upload"}</h3><p>{asset.price_usdc} USDC</p>{asset.token_id ? <Link href={`/marketplace#asset-${asset.token_id}`} className="underline">Manage asset #{asset.token_id}</Link> : <><Link className="block underline" href={`/mint?upload=${asset.vector_id}`}>Continue minting this upload</Link><form className="flex flex-wrap items-end gap-3" onSubmit={e => { e.preventDefault(); const token = new FormData(e.currentTarget).get("token"); void run(() => api(`/api/assets/${asset.vector_id}/link-token`, { method: "POST", body: JSON.stringify({ token_id: Number(token) }) })); }}><label>Already minted? Link token ID<input className="ml-3 rounded border p-2" name="token" type="number" required min="1" step="1" /></label><button disabled={busy || !user?.wallet_address} className="rounded border p-2">Verify and link mint</button><p className="w-full text-sm text-slate-500">The token must match this upload and your verified creator wallet.</p></form></>}</article>)}</section>
    <section className="space-y-4"><h2 className="text-2xl font-semibold">Your Web2 payment history</h2><p className="text-sm text-slate-600">Showing your latest 100 orders. Web3 purchases and auction entitlements can be checked on each marketplace asset using your wallet.</p>{data?.orders.length === 0 && <p>No payment orders yet.</p>}{data?.orders.map(order => <article key={order.order_id} className="space-y-3 rounded-xl border p-5"><h3 className="font-semibold">Asset #{order.token_id} · {order.amount_usdc} USDC · {order.payment_method}</h3><p>{order.recovery_status === "REFUNDED" ? "Full refund verified" : order.recovery_status === "REVIEW_REQUIRED" ? "Payment under review — do not pay again" : order.status.replaceAll("_", " ")}</p><p className="break-all text-xs">Order: {order.order_id}</p>{order.error && <p role="alert" className="text-red-700">{order.error}</p>}{order.settlement_tx_hash && <a className="block underline" target="_blank" rel="noreferrer" href={`https://amoy.polygonscan.com/tx/${order.settlement_tx_hash}`}>View settlement transaction</a>}<Link className="inline-block underline" href={`/marketplace#asset-${order.token_id}`}>View asset / Resume checkout</Link>{!order.recovery_status && (["PROVIDER_CONFIRMED", "SETTLEMENT_PENDING", "SETTLED"].includes(order.status) || order.status === "FAILED" && order.provider_payment_id) && order.payment_method !== "mock" && <button disabled={busy} className="ml-4 rounded border p-2" onClick={() => run(() => api(`/api/payments/${order.order_id}/settle`, { method: "POST" }))}>Check / Retry settlement</button>}</article>)}</section>
    {user?.wallet_address && <AccountActivity key={user.id} />}
    {user?.wallet_address && <Positions key={`positions-${user.id}`} />}
    <PayoutHistory />
    <TransakOrders />
    <SellerPayout />
    <ReviewHistory />
    <RecordingHistory />
    <IndexedActivity />
  </div>;
}
export default function DashboardPage() { return <main className="mx-auto max-w-5xl space-y-8 px-6 py-12"><h1 className="text-3xl font-bold">Your dashboard</h1><AccountGate><Dashboard /></AccountGate></main>; }
