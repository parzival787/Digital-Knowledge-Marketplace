"use client";
import Link from "next/link";
import { useState } from "react";
import { searchAssets, SearchResult } from "@/lib/api/backend";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [domain, setDomain] = useState("");
  const [price, setPrice] = useState("");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return <main className="mx-auto max-w-5xl px-6 py-12"><h1 className="text-3xl font-bold">Find knowledge</h1><p className="mt-3 text-slate-600">Describe what you need. Search ranks uploaded documents by relevance and related topics.</p><form className="my-8 space-y-4 rounded-xl border p-6" onSubmit={async e => { e.preventDefault(); setBusy(true); setError(""); try { setResults((await searchAssets(query, domain, price === "" ? undefined : Number(price))).results); } catch (err) { setError(err instanceof Error ? err.message : "Search failed."); } finally { setBusy(false); } }}>
    <label className="block">Search query<input required maxLength={2000} value={query} onChange={e => setQuery(e.target.value)} className="mt-2 w-full rounded border p-3" placeholder="For example, machine learning datasets for healthcare" /></label><div className="grid gap-4 sm:grid-cols-2"><label>Domain (optional)<input value={domain} maxLength={100} onChange={e => setDomain(e.target.value)} className="mt-2 w-full rounded border p-2" placeholder="e.g. technology" /></label><label>Maximum price (USDC)<input type="number" min="0" max="1000000" step="1" value={price} onChange={e => setPrice(e.target.value)} className="mt-2 w-full rounded border p-2" /></label></div><button disabled={busy} className="rounded bg-blue-600 px-5 py-2 text-white disabled:opacity-50">{busy ? "Searching…" : "Search assets"}</button></form>
    {error && <p role="alert" className="text-red-700">{error}</p>}{results?.length === 0 && <p>No matching assets. Try a broader query or remove filters.</p>}<div className="grid gap-4 sm:grid-cols-2">{results?.map(result => <article key={result.vector_id} className="space-y-3 rounded-xl border p-5"><h2 className="text-xl font-semibold">{result.title || "Untitled asset"}</h2><p>{result.domain} · {result.price_usdc} USDC</p><p className="text-sm">{result.tags.join(", ")}</p><p className="text-sm">Relevance: {((result.final_score ?? result.score) * 100).toFixed(0)}%</p>{result.token_id ? <Link href={`/marketplace#asset-${result.token_id}`} className="text-blue-700 underline">View asset #{result.token_id} and purchase options</Link> : <p className="text-sm text-slate-500">Not linked to an on-chain token yet.</p>}</article>)}</div>
  </main>;
}
