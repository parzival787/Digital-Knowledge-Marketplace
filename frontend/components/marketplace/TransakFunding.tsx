"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";

export default function TransakFunding() {
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    api<{ routes: { transak_buy: { enabled: boolean } } }>("/api/capabilities")
      .then(value => setConfigured(value.routes.transak_buy.enabled)).catch(() => setError("Could not check Transak availability. Reload to retry."));
  }, []);
  async function start() {
    if (busy) return;
    setBusy(true); setError("");
    try {
      const session = await api<{ widget_url: string; environment: string; grants_access: boolean }>("/api/payments/transak/session", { method: "POST" });
      const url = new URL(session.widget_url);
      if (session.environment !== "staging" || session.grants_access !== false || url.origin !== "https://global-stg.transak.com") {
        throw new Error("Unexpected sandbox session. Please retry.");
      }
      window.location.assign(url.href);
    } catch (e) { setError(e instanceof Error ? e.message : "Could not open Transak sandbox."); }
    finally { setBusy(false); }
  }
  return <section className="space-y-3 rounded-xl border p-5" aria-labelledby="transak-title">
    <h2 id="transak-title" className="text-xl font-semibold">Try Transak test checkout</h2>
    <p>Test the provider’s supported payment methods and review its fees before confirming. UPI is not verified for this sandbox. Use only Transak’s documented test payment details.</p>
    <p className="rounded bg-amber-50 p-3">Sandbox only: selecting USDC on Polygon delivers TRNSK on Amoy. TRNSK can fund listings that accept TRNSK; legacy MockUSDC listings require MockUSDC. For a listing-bound quote, start funding from that asset’s marketplace card. Funding does not buy an asset or grant access.</p>
    <p>Your verified account wallet is the destination. DKM adds no buyer platform fee; its marketplace fee is deducted from seller proceeds.</p>
    {configured === false && <p role="status">Add the Transak staging credentials to the backend configuration and restart the backend to enable this test.</p>}
    {error && <p role="alert" className="text-red-700">{error}</p>}
    <button disabled={!configured || busy} onClick={start} className="rounded border px-4 py-2 disabled:opacity-50">
      {busy ? "Opening sandbox…" : "Open Transak sandbox"}
    </button>
    <a href="https://docs.transak.com/guides/sandbox-credentials" target="_blank" rel="noreferrer" className="block underline">Transak test payment instructions</a>
  </section>;
}
