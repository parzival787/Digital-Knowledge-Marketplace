"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAccount, usePublicClient, useSwitchChain, useWriteContract } from "wagmi";
import { parseEventLogs, parseUnits } from "viem";
import { polygonAmoy } from "viem/chains";
import { knowledgeAssetContract } from "@/lib/blockchain/contracts";
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
      setUpload(saved); setPrice(String(saved.price_usdc));
      setAnalysis({success: true, metadata: {title: saved.title, quality_score: saved.quality}});
      if (saved.token_id) { setToken(String(saved.token_id)); setLinked(true); }
      setStatus(saved.token_id ? "This upload is already minted and linked." : "Upload restored. If you already minted it, use Dashboard to link the existing token instead of minting again.");
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
    setLinked(true); setStatus("Asset minted and linked to your account. You can now list it in the marketplace.");
  }
  async function mint() {
    if (!address || !client || !upload || !analysis || tx || linked) return;
    if (chainId !== polygonAmoy.id) await switchChainAsync({ chainId: polygonAmoy.id });
    setStatus("Confirm mint in your wallet…");
    const hash = await writeContractAsync({ ...knowledgeAssetContract, functionName: "mint", account: address, chainId: polygonAmoy.id,
      args: [upload.file_cid, upload.metadata_cid, parseUnits(price, 6), BigInt(license), BigInt(Math.round((analysis.metadata.quality_score || 0) * 100))] });
    setTx(hash); setStatus("Waiting for mint confirmation…");
    await finishMint(hash);
  }
  async function finishMint(hash: string) {
    if (!client) return;
    const receipt = await client.waitForTransactionReceipt({ hash: hash as `0x${string}` });
    if (receipt.status !== "success") { setTx(null); throw new Error("Mint reverted. You can retry."); }
    const events = parseEventLogs({ abi: [{ type: "event", name: "Transfer", inputs: [{name:"from",type:"address",indexed:true},{name:"to",type:"address",indexed:true},{name:"tokenId",type:"uint256",indexed:true}] }] as const, eventName: "Transfer", logs: receipt.logs.filter(log => log.address.toLowerCase() === knowledgeAssetContract.address.toLowerCase()) });
    const event = events.find(e => e.args.from === "0x0000000000000000000000000000000000000000" && e.args.to.toLowerCase() === address?.toLowerCase());
    if (!event) throw new Error("Mint receipt could not be linked. Use your upload in Dashboard to retry linking.");
    const id = event.args.tokenId.toString(); setToken(id); setStatus("Mint confirmed. Linking your upload…"); await link(id);
  }
  return <div className="mt-8 space-y-6">
    <section className="space-y-4 rounded-xl border p-6"><h2 className="text-xl font-semibold">1. Analyze your document</h2><label className="block">Document (up to 20 MB)<input type="file" accept=".pdf,.txt,.csv" disabled={busy || !!upload} className="mt-2 block w-full rounded border p-2" onChange={e => { setFile(e.target.files?.[0] || null); setAnalysis(null); }} /></label><button disabled={!file || busy || !!upload} className="rounded border px-4 py-2 disabled:opacity-50" onClick={() => run(async () => { if (!file) return; setStatus("Analyzing document…"); const result = await analyzeAsset(file); setAnalysis(result); setPrice(String(result.metadata.recommended_price_usdc || 5)); setStatus("Analysis ready. Review settings before uploading."); })}>Analyze document</button></section>
    {analysis && <section className="space-y-4 rounded-xl border p-6"><h2 className="text-xl font-semibold">2. Review and upload</h2><h3 className="font-semibold">{analysis.metadata.title}</h3><p>{analysis.metadata.summary}</p><p>{analysis.metadata.domain} · Quality {Math.round((analysis.metadata.quality_score || 0) * 100)}/100</p><p>{analysis.metadata.tags?.join(", ")}</p><label className="block">Price (whole USDC)<input type="number" min="1" max="100" step="1" disabled={!!upload || busy} value={price} onChange={e => setPrice(e.target.value)} className="mt-2 w-full rounded border p-2" /></label><label className="block">License<select value={license} disabled={!!tx || busy} onChange={e => setLicense(e.target.value)} className="mt-2 w-full rounded border p-2"><option value="0">Open Access</option><option value="1">Single Use</option><option value="2">Commercial</option></select></label><p className="text-sm text-amber-800">Uploads go to public IPFS. Do not upload private or confidential files; anyone with the file address can retrieve them.</p><button disabled={busy || !!upload} className="rounded border px-4 py-2 disabled:opacity-50" onClick={() => run(async () => { if (!file) return; if (!Number.isInteger(Number(price)) || Number(price) < 1 || Number(price) > 100) throw new Error("Choose a whole USDC price from 1 to 100."); setStatus("Uploading file and metadata…"); setUpload(await uploadAssetToIPFS(file, { ...analysis.metadata, recommended_price_usdc: Number(price) })); setStatus("Upload saved to your account. Ready to mint."); })}>Upload to public IPFS</button></section>}
    {upload && <section className="space-y-4 rounded-xl border p-6"><h2 className="text-xl font-semibold">3. Mint and link</h2><p className="break-all">File: {upload.file_cid}</p><p>Your upload is saved in Dashboard even if you leave this page.</p>{!tx && !linked && <button disabled={busy} onClick={() => run(mint)} className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50">Mint on Polygon Amoy</button>}{tx && <a className="block underline" href={`https://amoy.polygonscan.com/tx/${tx}`} target="_blank" rel="noreferrer">View mint transaction</a>}{tx && !linked && <button disabled={busy} onClick={() => run(() => token ? link(token) : finishMint(tx))} className="rounded border px-4 py-2">Check mint / Retry linking</button>}{linked && <Link className="block underline" href={`/marketplace#asset-${token}`}>List your asset for sale or auction</Link>}</section>}
    {status && <p role="status">{status}</p>}{error && <p className="break-words text-red-700" role="alert">{error}</p>}
  </div>;
}
export default function MintPage({ searchParams }: { searchParams?: { upload?: string } }) { return <main className="mx-auto max-w-3xl px-6 py-12"><h1 className="mb-6 text-3xl font-bold">Create knowledge asset</h1><AccountGate wallet><MintFlow resume={searchParams?.upload} /></AccountGate></main>; }
