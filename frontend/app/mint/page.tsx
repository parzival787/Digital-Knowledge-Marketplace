"use client";
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAccount, usePublicClient, useSwitchChain, useWriteContract } from "wagmi";
import { parseEventLogs, parseUnits } from "viem";
import { polygonAmoy } from "viem/chains";
import { knowledgeAssetContract } from "@/lib/blockchain/contracts";
import { checkGas } from "@/lib/blockchain/purchaseSafety";
import { analyzeAsset, uploadAssetToIPFS, AnalyzeResponse, UploadIPFSResponse } from "@/lib/api/backend";
import { api } from "@/lib/api/client";
import { AccountGate } from "@/providers/AuthProvider";

function MintFlow({ resume }: { resume?: string }) {
  const { address, chainId } = useAccount();
  const client = usePublicClient({ chainId: polygonAmoy.id });
  const { switchChainAsync } = useSwitchChain();
  const { writeContractAsync } = useWriteContract();
  const [file, setFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [upload, setUpload] = useState<UploadIPFSResponse | null>(null);
  const [price, setPrice] = useState("5");
  const [license, setLicense] = useState("0");
  const [token, setToken] = useState<string | null>(null);
  const [tx, setTx] = useState<string | null>(null);
  const [linked, setLinked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    if (!resume) return;
    let active = true;
    setBusy(true);
    api<{assets: {vector_id: string; file_cid: string; metadata_cid: string; title: string; quality: number; price_usdc: number; token_id: number | null}[]}>("/api/account/dashboard").then(data => {
      if (!active) return;
      const saved = data.assets.find(a => a.vector_id === resume);
      if (!saved) throw new Error("Upload not found in your account.");
      setUpload(saved);
      const pending = localStorage.getItem(`dkm:mint:${knowledgeAssetContract.address}:${saved.vector_id}`);
      if (pending && /^0x[0-9a-fA-F]{64}$/.test(pending)) setTx(pending);
      setPrice(String(saved.price_usdc));
      setAnalysis({success: true, metadata: {title: saved.title, quality_score: saved.quality}});
      if (saved.token_id) { setToken(String(saved.token_id)); setLinked(true); }
      setStatus(saved.token_id ? "This upload is already minted and linked." : "Upload restored. No code is needed. Your saved file is ready; completed mints are checked before retrying.");
    }).catch(err => { if (active) setError(err instanceof Error ? err.message : "Could not restore upload."); }).finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [resume]);
  async function run(action: () => Promise<void>) {
    setBusy(true); setError("");
    try { await action(); } catch (err) { setError(err instanceof Error ? err.message : "Operation failed. Retry."); }
    finally { setBusy(false); }
  }
  async function link(id: string) {
    if (!upload) return;
    await api(`/api/assets/${upload.vector_id}/link-token`, { method: "POST", body: JSON.stringify({ token_id: Number(id) }) });
    localStorage.removeItem(`dkm:mint:${knowledgeAssetContract.address}:${upload.vector_id}`);
    setLinked(true); setStatus("Asset minted and linked to your account. You can now list it in the marketplace.");
  }
  async function mint() {
    if (!address || !client || !upload || !analysis || tx || linked) return;
    if (chainId !== polygonAmoy.id) await switchChainAsync({ chainId: polygonAmoy.id });
    setStatus("Checking whether this upload is already minted…");
    const recovered = await api<{token_id: number | null}>(`/api/assets/${upload.vector_id}/recover-mint`, { method: "POST" });
    if (recovered.token_id) { setToken(String(recovered.token_id)); setLinked(true); setStatus("Completed mint found and linked. No second mint was needed."); return; }
    setStatus("Confirm mint in your wallet…");
    const args = [upload.file_cid, upload.metadata_cid, parseUnits(price, 6), BigInt(license), BigInt(Math.round((upload.quality_score ?? analysis.metadata.quality_score ?? 0) * 100))];
    const fees = await checkGas(client, knowledgeAssetContract, "mint", args, address);
    const hash = await writeContractAsync({ ...knowledgeAssetContract, ...fees, functionName: "mint", account: address, chainId: polygonAmoy.id, args });
    setTx(hash);
    localStorage.setItem(`dkm:mint:${knowledgeAssetContract.address}:${upload.vector_id}`, hash);
    setStatus("Waiting for mint confirmation…");
    await finishMint(hash);
  }
  async function finishMint(hash: string) {
    if (!client) return;
    const receipt = await client.waitForTransactionReceipt({ hash: hash as `0x${string}` });
    if (receipt.status !== "success") { if (upload) localStorage.removeItem(`dkm:mint:${knowledgeAssetContract.address}:${upload.vector_id}`); setTx(null); throw new Error("Mint reverted. You can retry."); }
    const events = parseEventLogs({ abi: [{ type: "event", name: "Transfer", inputs: [{name:"from",type:"address",indexed:true},{name:"to",type:"address",indexed:true},{name:"tokenId",type:"uint256",indexed:true}] }] as const, eventName: "Transfer", logs: receipt.logs.filter(log => log.address.toLowerCase() === knowledgeAssetContract.address.toLowerCase()) });
    const event = events.find(e => e.args.from === "0x0000000000000000000000000000000000000000" && e.args.to.toLowerCase() === address?.toLowerCase());
    if (!event) throw new Error("Mint receipt could not be linked. Use your upload in Dashboard to retry linking.");
    const id = event.args.tokenId.toString(); setToken(id); setStatus("Mint confirmed. Linking your upload…"); await link(id);
  }
  return <div className="mt-8 space-y-6">
    <section className="space-y-4 rounded-xl border p-6"><h2 className="text-xl font-semibold">1. Analyze your document</h2><label className="block">Document (up to 20 MB)<input type="file" accept=".pdf,.txt,.csv" disabled={busy || !!upload} className="mt-2 block w-full rounded border p-2" onChange={e => { setFile(e.target.files?.[0] || null); setAnalysis(null); }} /></label><button disabled={!file || busy || !!upload} className="rounded border px-4 py-2 disabled:opacity-50" onClick={() => run(async () => { if (!file) return; setStatus("Analyzing document…"); const result = await analyzeAsset(file); setAnalysis(result); setPrice(String(result.metadata.recommended_price_usdc || 5)); setStatus("Analysis ready. Review settings before uploading."); })}>Analyze document</button></section>
    {analysis && <section className="space-y-4 rounded-xl border p-6"><h2 className="text-xl font-semibold">2. Review and upload</h2><h3 className="font-semibold">{analysis.metadata.title}</h3><p>{analysis.metadata.summary}</p><p>{analysis.metadata.domain} · AI assessment {Math.round((analysis.metadata.quality_score || 0) * 100)}/100</p><p>{analysis.metadata.tags?.join(", ")}</p>{analysis.metadata.quality_breakdown && <details className="rounded-xl border bg-slate-50 p-4"><summary className="cursor-pointer font-medium">How this assessment was scored</summary><p className="mt-3 text-sm text-slate-600">{analysis.metadata.quality_scope} Each criterion contributes equally. This is an AI estimate, not a certification.</p><div className="mt-4 grid gap-4 sm:grid-cols-2">{Object.entries(analysis.metadata.quality_breakdown).map(([name, item]) => <div key={name}><h4 className="font-semibold capitalize">{name} · {item.score}/4</h4><p className="mt-1 text-sm">{item.reason}</p>{item.quote && <blockquote className="mt-2 border-l-2 pl-3 text-sm text-slate-500">{item.quote}</blockquote>}</div>)}</div></details>}<p className="text-sm text-slate-500">Choose your own price. The starting value is not a market valuation. Upload verifies the document assessment again.</p><label className="block">Price (USDC)<input type="number" min="0.01" max="100" step="0.01" disabled={!!upload || busy} value={price} onChange={e => setPrice(e.target.value)} className="mt-2 w-full rounded border p-2" /></label><label className="block">License<select value={license} disabled={!!tx || busy} onChange={e => setLicense(e.target.value)} className="mt-2 w-full rounded border p-2"><option value="0">Open Access</option><option value="1">Single Use</option><option value="2">Commercial</option></select></label><p className="text-sm text-amber-800">Files are encrypted before storage. Verified buyers and the creator can download through DKM. The title, summary and tags remain public; keep sensitive information out of those fields.</p><button disabled={busy || !!upload} className="rounded border px-4 py-2 disabled:opacity-50" onClick={() => run(async () => { if (!file) return; if (!/^\d+(\.\d{1,2})?$/.test(price) || Number(price) < 0.01 || Number(price) > 100) throw new Error("Choose a price from 0.01 to 100 USDC, with at most two decimal places."); setStatus("Uploading file and metadata…"); setUpload(await uploadAssetToIPFS(file, { ...analysis.metadata, recommended_price_usdc: Number(price) })); setStatus("Upload saved to your account. Ready to mint."); })}>Upload protected file</button></section>}
    {upload && <section className="space-y-4 rounded-xl border p-6"><h2 className="text-xl font-semibold">3. Mint and link</h2><p>Protected file uploaded successfully.</p><p>Your upload is saved in Dashboard even if you leave this page.</p>{!tx && !linked && <button disabled={busy} onClick={() => run(mint)} className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50">Mint on Polygon Amoy</button>}{tx && <a className="block underline" href={`https://amoy.polygonscan.com/tx/${tx}`} target="_blank" rel="noreferrer">View mint transaction</a>}{tx && !linked && <button disabled={busy} onClick={() => run(() => token ? link(token) : finishMint(tx))} className="rounded border px-4 py-2">Check mint / Retry linking</button>}{linked && <Link className="block underline" href={`/marketplace?asset=${token}#asset-${token}`}>List your asset for sale or auction</Link>}</section>}
    {status && <p role="status">{status}</p>}{error && <p className="break-words text-red-700" role="alert">{error}</p>}
  </div>;
}
function MintContent() { const searchParams = useSearchParams(); return <main className="mx-auto max-w-3xl px-6 py-12"><h1 className="mb-6 text-3xl font-bold">Create knowledge asset</h1><AccountGate wallet><MintFlow resume={searchParams.get("upload") || undefined} /></AccountGate></main>; }

export default function MintPage() { return <Suspense fallback={<p role="status">Loading saved upload…</p>}><MintContent /></Suspense>; }
