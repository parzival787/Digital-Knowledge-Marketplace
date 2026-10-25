"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";

type ReviewPage = { count: number; average: number | null; next_offset: number | null; reviews: { id: number; rating: number; review_text: string; created_at: string }[] };
export default function Reviews({ tokenId, canReview }: { tokenId: bigint; canReview: boolean }) {
  const [page, setPage] = useState<ReviewPage | null>(null);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  useEffect(() => { let active = true; setPage(null); setError(""); api<ReviewPage>(`/api/assets/${tokenId}/reviews?offset=${offset}`).then(data => { if (active) setPage(data); }).catch(() => { if (active) setError("Could not load reviews. Reopen details to retry."); }); return () => { active = false; }; }, [tokenId, offset]);
  return <section className="mt-6 space-y-3 border-t pt-4"><h4 className="font-semibold">Purchaser reviews</h4>
    {page ? <><p>{page.count ? `${page.average?.toFixed(1)} / 5 · ${page.count} reviews` : "No reviews yet."}</p>{page.reviews.map(review => <article key={review.id} className="rounded border bg-white p-3"><p>{review.rating} / 5 · {new Date(review.created_at).toLocaleDateString()}</p><p className="whitespace-pre-wrap">{review.review_text}</p></article>)}<div className="flex gap-4">{offset > 0 && <button type="button" className="underline" onClick={() => setOffset(Math.max(0, offset - 20))}>Previous reviews</button>}{page.next_offset !== null && <button type="button" className="underline" onClick={() => setOffset(page.next_offset!)}>More reviews</button>}</div></> : !error && <p role="status">Loading reviews…</p>}
    {canReview ? <form className="space-y-3" onSubmit={async event => { event.preventDefault(); const form = new FormData(event.currentTarget); setBusy(true); setSaved(false); setError(""); try { await api(`/api/assets/${tokenId}/reviews`, { method: "POST", body: JSON.stringify({ rating: Number(form.get("rating")), review_text: form.get("review_text") }) }); const updated = await api<ReviewPage>(`/api/assets/${tokenId}/reviews`); setPage(updated); setOffset(0); setSaved(true); } catch (err) { setError(err instanceof Error ? err.message : "Could not save review."); } finally { setBusy(false); } }}><label className="block">Your rating<select name="rating" defaultValue="5" className="ml-3 rounded border p-2">{[5,4,3,2,1].map(value => <option key={value} value={value}>{value} / 5</option>)}</select></label><label className="block">Your review<textarea name="review_text" maxLength={2000} className="mt-2 w-full rounded border p-2" /></label><button disabled={busy} className="rounded border bg-white p-2">{busy ? "Saving…" : "Save / Update my review"}</button>{saved && <p role="status">Your review is saved.</p>}</form> : <p className="text-sm text-slate-600">Verified purchasers can leave one review per asset.</p>}
    {error && <p role="alert" className="text-red-700">{error}</p>}
  </section>;
}
