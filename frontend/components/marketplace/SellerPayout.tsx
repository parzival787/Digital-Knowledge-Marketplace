"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import { useVerifiedWallet } from "@/providers/AuthProvider";

export default function SellerPayout() {
  const verified = useVerifiedWallet();
  const [currency, setCurrency] = useState("USDC");
  const [saved, setSaved] = useState<string | null>(null);
  const [configured, setConfigured] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([
      api<{ currency: string }>("/api/payments/transak/payout-preference"),
      api<{ configured: boolean }>("/api/payments/transak/status"),
    ]).then(([preference, status]) => {
      setCurrency(preference.currency); setSaved(preference.currency); setConfigured(status.configured);
    }).catch(() => setError("Could not load payout settings. Reload before changing them."));
  }, []);
  async function save() {
    setBusy(true); setError(""); setMessage("");
    try {
      const result = await api<{ currency: string }>("/api/payments/transak/payout-preference",
        { method: "PUT", body: JSON.stringify({ currency }) });
      setSaved(result.currency);
      setMessage("Preference saved. Automatic conversion and bank payouts are not enabled.");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not save preference."); }
    finally { setBusy(false); }
  }
  async function withdraw() {
    setBusy(true); setError(""); setMessage("");
    try {
      const session = await api<{ widget_url: string; environment: string; automatic_payout_enabled: boolean }>(
        "/api/payments/transak/payout-session", { method: "POST" });
      const url = new URL(session.widget_url);
      if (session.environment !== "staging" || session.automatic_payout_enabled !== false || url.origin !== "https://global-stg.transak.com") {
        throw new Error("Unexpected withdrawal session.");
      }
      window.location.assign(url.href);
    } catch (e) { setError(e instanceof Error ? e.message : "Could not open test withdrawal."); }
    finally { setBusy(false); }
  }
  return <section className="space-y-4 rounded-xl border p-6" aria-labelledby="seller-payout-title">
    <h2 id="seller-payout-title" className="text-xl font-semibold">Seller payout preference</h2>
    <p>Choose the currency you would like to receive. Current marketplace sales still pay the configured on-chain token. Saving a preference does not convert proceeds or change listing prices.</p>
    <label className="block" htmlFor="payout-currency">Preferred currency</label>
    <select id="payout-currency" value={currency} disabled={saved === null || busy} onChange={event => setCurrency(event.target.value)} className="rounded border p-2">
      <option value="USDC">USDC — wallet</option><option value="USD">USD — US dollar</option>
      <option value="EUR">EUR — euro</option><option value="INR">INR — Indian rupee</option>
      <option value="IDR">IDR — Indonesian rupiah</option>
    </select>
    <button onClick={save} disabled={saved === null || busy || currency === saved} className="ml-3 rounded border px-4 py-2 disabled:opacity-50">Save preference</button>
    <p>Fiat withdrawals depend on your country, account eligibility and provider support. The provider handles bank details and displays available payout methods, fees and the amount received.</p>
    <p className="rounded bg-amber-50 p-3">Sandbox withdrawal is a separate test. Use Transak test tokens and documented test payout details only. DKM MockUSDC is not accepted by Transak. No automatic payout or blockchain purchase record is created here.</p>
    <button onClick={withdraw} disabled={!configured || !verified || busy || saved === null || saved === "USDC" || currency !== saved}
      className="rounded border px-4 py-2 disabled:opacity-50">Open Transak withdrawal sandbox</button>
    {!verified && <p>Connect your verified account wallet to try a sandbox withdrawal.</p>}
    {message && <p role="status">{message}</p>}{error && <p role="alert" className="text-red-700">{error}</p>}
  </section>;
}
