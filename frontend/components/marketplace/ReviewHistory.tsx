"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
type Review={id:number;token_id:number;rating:number;review_text:string;direction:string};
export default function ReviewHistory(){
  const [rows,setRows]=useState<Review[]>([]),[error,setError]=useState("");
  useEffect(()=>{api<{reviews:Review[]}>("/api/account/reviews").then(data=>setRows(data.reviews)).catch(()=>setError("Could not load your reviews."));},[]);
  return <section className="space-y-3 rounded-xl border p-6"><h2 className="text-xl font-semibold">Reviews given and received</h2><p>Latest 100 reviews associated with your account wallet or uploads.</p>{error&&<p role="alert">{error}</p>}{!rows.length&&!error&&<p>No reviews yet.</p>}{rows.map(r=><article key={r.id} className="border-t pt-3"><p>{r.direction==="given"?"Your review":"Review on your asset"} · {r.rating}/5</p><p>{r.review_text}</p><Link className="underline" href={`/marketplace#asset-${r.token_id}`}>Asset #{r.token_id} / review</Link></article>)}</section>;
}
