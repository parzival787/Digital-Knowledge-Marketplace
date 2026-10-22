"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
type Status = { status: string; checks: Record<string, boolean | string> };
export default function StatusPage() {
  const [health, setHealth] = useState<Status | null>(null);
  const [error, setError] = useState("");
  async function refresh() { setError(""); try { setHealth(await api<Status>("/health")); } catch { setError("Backend unavailable. Check that the service is running and retry."); } }
  useEffect(() => { void refresh(); }, []);
  return <main className="mx-auto max-w-4xl space-y-6 px-6 py-12"><h1 className="text-3xl font-bold">Services and payment options</h1><button onClick={refresh} className="rounded border px-4 py-2">Refresh status</button>{error && <p role="alert" className="text-red-700">{error}</p>}
    <div className="grid gap-4 sm:grid-cols-2">{[["Marketplace & Web3", "Browse assets, approve USDC and buy with a Polygon Amoy wallet.", "/marketplace"], ["Auctions", "Create auctions, bid, finalize and withdraw refundable bids.", "/auctions"], ["Analyze, upload & mint", "Analyze a document, encrypt its file for IPFS storage and mint a knowledge asset.", "/mint"], ["Search", "Search uploaded documents by topic, domain, price and quality.", "/search"]].map(([title, detail, href]) => <Link className="space-y-2 rounded-xl border p-5" key={href} href={href}><h2 className="font-semibold">{title}</h2><p className="text-sm">{detail}</p><span className="inline-block pt-3 text-blue-700">Open →</span></Link>)}</div>
    {health && <section className="rounded-xl border p-6"><h2 className="text-xl font-semibold">Backend: {health.status}</h2><dl className="mt-4 space-y-2">{Object.entries(health.checks).filter(([key]) => !key.endsWith("_error")).map(([key, value]) => <div key={key} className="flex justify-between gap-4"><dt>{key.replaceAll("_", " ")}</dt><dd>{value === true ? "Ready" : value === false ? "Unavailable" : value}</dd></div>)}</dl></section>}
  </main>;
}
