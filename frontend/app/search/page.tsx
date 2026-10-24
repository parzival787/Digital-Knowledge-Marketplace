"use client";
import Link from "next/link";
import { useState } from "react";
import { Search, ArrowRight, SlidersHorizontal } from "lucide-react";
import { searchAssets, SearchResult } from "@/lib/api/backend";

const domains = ["science", "finance", "healthcare", "technology", "social", "agriculture", "environment", "other"];
export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [domain, setDomain] = useState("");
  const [price, setPrice] = useState("");
  const [quality, setQuality] = useState("40");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [searched, setSearched] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return <main className="mx-auto max-w-6xl px-6 py-12">
    <p className="text-sm font-semibold uppercase tracking-widest text-blue-700">Knowledge library</p>
    <h1 className="mt-3 text-4xl font-bold tracking-tight">Find your next idea.</h1>
    <p className="mt-4 max-w-2xl text-slate-600">Describe a topic, question or dataset. Explore published assets by meaning, not just matching words.</p>
    <form className="my-8 rounded-2xl border bg-white p-5 shadow-sm sm:p-6" onSubmit={async e => {
      e.preventDefault(); if (busy || !query.trim()) return;
      setBusy(true); setError(""); setResults(null); setSearched(query.trim());
      try { setResults((await searchAssets(query.trim(), domain, price === "" ? undefined : Number(price), Number(quality) / 100)).results); }
      catch (err) { setError(err instanceof Error ? err.message : "Search failed. Please retry."); }
      finally { setBusy(false); }
    }}>
      <label htmlFor="knowledge-query" className="sr-only">What would you like to explore?</label>
      <div className="flex flex-col gap-3 sm:flex-row"><div className="relative flex-1"><Search aria-hidden className="absolute left-4 top-4 h-5 w-5 text-slate-400" /><input id="knowledge-query" required maxLength={2000} value={query} onChange={e => setQuery(e.target.value)} className="w-full rounded-xl border bg-slate-50 py-3.5 pl-12 pr-4" placeholder="e.g. crop yields and rainfall in India" /></div><button disabled={busy || !query.trim()} className="rounded-xl bg-blue-700 px-7 py-3 font-semibold text-white hover:bg-blue-800 disabled:opacity-50">{busy ? "Searching…" : "Search"}</button></div>
      <details className="mt-5"><summary className="w-fit cursor-pointer text-sm font-medium text-slate-600"><SlidersHorizontal aria-hidden className="mr-2 inline h-4 w-4" />Refine your search</summary><fieldset disabled={busy} className="mt-4 grid gap-4 sm:grid-cols-3"><legend className="sr-only">Search filters</legend><label className="text-sm">Topic<select value={domain} onChange={e => setDomain(e.target.value)} className="mt-2 w-full rounded-lg border p-2.5"><option value="">All topics</option>{domains.map(value => <option value={value} key={value}>{value[0].toUpperCase() + value.slice(1)}</option>)}</select></label><label className="text-sm">Maximum catalog price (USDC)<input type="number" min="0" max="1000000" step="0.01" value={price} onChange={e => setPrice(e.target.value)} placeholder="Any price" className="mt-2 w-full rounded-lg border p-2.5" /></label><label className="text-sm">Minimum AI assessment (out of 100)<input type="number" min="40" max="100" required value={quality} onChange={e => setQuality(e.target.value)} className="mt-2 w-full rounded-lg border p-2.5" /></label></fieldset></details>
    </form>
    {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-5 text-red-800">{error}</p>}
    <div role="status" aria-live="polite" className="mb-5 text-sm text-slate-600">{busy ? "Finding relevant assets…" : results ? `${results.length} ${results.length === 1 ? "asset" : "assets"} for “${searched}”` : ""}</div>
    {results?.length === 0 && <div className="rounded-2xl border border-dashed p-10 text-center"><h2 className="text-xl font-semibold">No published assets found</h2><p className="mt-2 text-slate-600">Try a different topic or remove filters. Your unfinished uploads are in Dashboard.</p><Link className="mt-4 inline-block text-blue-700 underline" href="/dashboard">Open dashboard</Link></div>}
    <div className="grid gap-5 sm:grid-cols-2">{results?.map(result => <article key={result.token_id} className="flex flex-col rounded-2xl border bg-white p-6 shadow-sm transition-shadow hover:shadow-md"><span className="w-fit rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold capitalize text-blue-800">{result.domain}</span><h2 className="mt-4 text-xl font-semibold leading-snug">{result.title || "Untitled asset"}</h2><p className="mt-3 flex-1 text-sm leading-6 text-slate-600">{result.summary || "Open this asset to read its description and access options."}</p><div className="mt-4 flex flex-wrap gap-2">{result.tags.slice(0, 4).map(tag => <span key={tag} className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">{tag}</span>)}</div><div className="mt-6 flex items-center justify-between gap-4 border-t pt-4"><div><p className="font-semibold">{result.price_usdc} USDC</p><p className="text-xs text-slate-500">Catalog price · final terms on asset</p></div><Link href={`/marketplace?asset=${result.token_id}#asset-${result.token_id}`} className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-800">View asset<ArrowRight aria-hidden className="h-4 w-4" /></Link></div></article>)}</div>
  </main>;
}
