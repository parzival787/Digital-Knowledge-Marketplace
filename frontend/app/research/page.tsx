"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";

type Results = {
  pricing: {dataset:string;summary:Record<string,number>;samples:{asset_id:string;qaoa_price:number|null;classical_price:number;exact_price:number}[]} | null;
  embeddings: {dataset:string;training:string;summary:Record<string,Record<string,number>>;initial_loss:number;best_loss:number;training_seconds:number;qubits:number;output_dimensions:number} | null;
};
export default function ResearchPage() {
  const [data,setData]=useState<Results|null>(null),[error,setError]=useState("");
  useEffect(()=>{let active=true;api<Results>("/api/research/results").then(value=>{if(active)setData(value);}).catch(()=>{if(active)setError("Could not load research results. Retry after the backend is available.");});return()=>{active=false;};},[]);
  return <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
    <h1 className="text-3xl font-bold">Quantum research experiments</h1>
    <p>Measured QAOA pricing and trained VQC embedding experiments run on a local classical quantum-circuit simulator. These are not quantum hardware results or evidence of quantum advantage.</p>
    <p className="rounded border bg-amber-50 p-4">Research results do not change listing prices, spend funds or replace the marketplace search model.</p>
    {error && <p role="alert">{error}</p>}{!data&&!error&&<p role="status">Loading measured results…</p>}
    <section className="space-y-3 rounded border p-5"><h2 className="text-2xl font-semibold">QAOA pricing</h2>
      {!data?.pricing ? <p>No completed local pricing benchmark is available.</p> : <>
        <p>{data.pricing.dataset}. Demand curves are assumptions, not observed sales.</p>
        <p>Assets evaluated: {data.pricing.summary.assets}. Mean sampled-price revenue gap from the exhaustive optimum: {(data.pricing.summary.mean_qaoa_relative_gap*100).toFixed(2)}%.</p>
        <p>Exact optimal prices: QAOA {data.pricing.summary.qaoa_exact_price_matches}; classical optimizer {data.pricing.summary.classical_exact_price_matches}.</p>
        <p>Mean simulator time per asset: {data.pricing.summary.mean_qaoa_seconds.toFixed(3)} seconds; classical optimizer: {(data.pricing.summary.mean_classical_seconds*1000).toFixed(3)} ms.</p>
        <p>Seven qubits, two alternating cost/mixer layers, up to 80 optimizer evaluations and 2,048 sampled states per asset. The table shows eight of the 64 synthetic cases.</p>
        <div className="overflow-x-auto"><table className="w-full text-left"><caption className="sr-only">Synthetic pricing comparison in whole USDC units</caption><thead><tr><th>Case</th><th>QAOA</th><th>Classical</th><th>Exact optimum</th></tr></thead><tbody>{data.pricing.samples.map(row=><tr key={row.asset_id}><td className="py-2">{row.asset_id}</td><td>{row.qaoa_price??"No feasible sample"}</td><td>{row.classical_price}</td><td>{row.exact_price}</td></tr>)}</tbody></table></div>
      </>}
    </section>
    <section className="space-y-3 rounded border p-5"><h2 className="text-2xl font-semibold">VQC embeddings</h2>
      {!data?.embeddings ? <p>No completed local VQC benchmark is available.</p> : <>
        <p>{data.embeddings.dataset}.</p><p>{data.embeddings.training}.</p>
        <p>384-dimensional embeddings are compressed to four components, passed through a four-qubit trainable circuit, then expanded to 384 dimensions.</p>
        <div className="overflow-x-auto"><table className="w-full text-left"><caption className="mb-2 text-left">NDCG@10 - higher is better</caption><thead><tr><th>Split</th><th>Original</th><th>Classical compression</th><th>Untrained circuit</th><th>Trained VQC</th></tr></thead><tbody>{Object.entries(data.embeddings.summary).map(([split,values])=><tr key={split}><td className="py-2">{split}</td>{["original","classical","untrained","trained"].map(key=><td key={key}>{values[key].toFixed(4)}</td>)}</tr>)}</tbody></table></div>
        <p>Training loss: {data.embeddings.initial_loss.toFixed(4)} to {data.embeddings.best_loss.toFixed(4)}. Training runtime: {data.embeddings.training_seconds.toFixed(2)} seconds.</p>
        <p>The authored corpus and topic-based labels are a controlled demonstration. Query topics overlap training-document topics; this does not measure unseen-topic or real-world retrieval performance.</p>
      </>}
    </section>
    <p>Full methods, seeds, parameter arrays and per-case results are retained in the project’s research_results directory.</p>
  </main>;
}
