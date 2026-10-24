"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AccountGate, useAuth } from "@/providers/AuthProvider";
import { api } from "@/lib/api/client";
import AccountActivity from "@/components/marketplace/AccountActivity";
import IndexedActivity from "@/components/marketplace/IndexedActivity";
import ReviewHistory from "@/components/marketplace/ReviewHistory";
import Positions from "@/components/marketplace/Positions";
type Asset = { vector_id: string; title: string; token_id: number | null; price_usdc: number };
function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState<{ assets: Asset[] } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  async function refresh() { setData(await api("/api/account/dashboard")); }
  useEffect(() => { let active = true; api<{ assets: Asset[] }>("/api/account/dashboard").then(value => { if (active) setData(value); }).catch(() => { if (active) setError("Could not load your dashboard. Please retry."); }); return () => { active = false; }; }, [user?.id]);
  async function run(action: () => Promise<unknown>) { setBusy(true); setError(""); setNotice(""); try { await action(); await refresh(); } catch (err) { setError(err instanceof Error ? err.message : "Request failed."); } finally { setBusy(false); } }
  return <div className="space-y-8"><div className="flex flex-wrap gap-5"><Link className="underline" href="/mint">Create asset</Link><Link className="underline" href="/marketplace">Browse marketplace</Link><Link className="underline" href="/account">Manage verified wallet</Link><button disabled={busy} className="underline" onClick={() => run(async () => {})}>Refresh</button></div>{notice && <p role="status">{notice}</p>}{error && <p role="alert" className="text-red-700">{error}</p>}{!data && !error && <p role="status">Loading your workspace…</p>}
    <section className="space-y-4"><h2 className="text-2xl font-semibold">Your uploads</h2>{data?.assets.length === 0 && <p>No uploads yet. Create your first knowledge asset.</p>}{data?.assets.map(asset => <article key={asset.vector_id} className="space-y-3 rounded-xl border p-5"><h3 className="font-semibold">{asset.title || "Untitled upload"}</h3><p>{asset.price_usdc} USDC</p>{asset.token_id ? <Link href={`/marketplace?asset=${asset.token_id}#asset-${asset.token_id}`} className="underline">Manage asset #{asset.token_id}</Link> : <><Link className="block underline" href={`/mint?upload=${asset.vector_id}`}>Resume minting — no code needed</Link><p className="text-sm text-slate-600">Uploading saves your file. Minting is a separate wallet transaction. If it failed or was rejected, resume here without uploading again.</p><button disabled={busy || !user?.wallet_address} className="rounded border p-2 disabled:opacity-50" onClick={() => run(async () => { const result = await api<{token_id: number | null}>(`/api/assets/${asset.vector_id}/recover-mint`, {method: "POST"}); setNotice(result.token_id ? `Mint found and linked: asset #${result.token_id}.` : "No completed mint found. Resume minting this upload. If MetaMask still shows a pending transaction, wait for it first."); })}>Check for completed mint</button><details><summary className="cursor-pointer text-sm">Advanced: link a known token ID</summary><p className="my-2 text-sm">This is the asset number from a successful mint, not an email or verification code. A failed mint has no token ID.</p><form className="flex flex-wrap items-end gap-3" onSubmit={e => { e.preventDefault(); const token = new FormData(e.currentTarget).get("token"); void run(() => api(`/api/assets/${asset.vector_id}/link-token`, { method: "POST", body: JSON.stringify({ token_id: Number(token) }) })); }}><label>Already minted? Link token ID<input className="ml-3 rounded border p-2" name="token" type="number" required min="1" step="1" /></label><button disabled={busy || !user?.wallet_address} className="rounded border p-2">Verify and link mint</button><p className="w-full text-sm text-slate-500">The token must match this upload and your verified creator wallet.</p></form></details></>}</article>)}</section>
    {user?.wallet_address && <AccountActivity key={user.id} />}
    {user?.wallet_address && <Positions key={`positions-${user.id}`} />}
    <ReviewHistory />
    <IndexedActivity />
  </div>;
}
export default function DashboardPage() { return <main className="mx-auto max-w-5xl space-y-8 px-6 py-12"><h1 className="text-3xl font-bold">Your dashboard</h1><AccountGate><Dashboard /></AccountGate></main>; }
