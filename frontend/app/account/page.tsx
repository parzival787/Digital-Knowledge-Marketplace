"use client";
import Link from "next/link";
import { useState } from "react";
import { useAccount, useSignMessage } from "wagmi";
import { AccountGate, useAuth, useVerifiedWallet } from "@/providers/AuthProvider";
import { api } from "@/lib/api/client";
import WalletButton from "@/components/wallet/WalletButton";

export default function AccountPage() {
  const { user, refresh, logout } = useAuth();
  const { address } = useAccount();
  const verified = useVerifiedWallet();
  const { signMessageAsync } = useSignMessage();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function verify() {
    if (!address) return;
    setBusy(true); setError("");
    try {
      const { message } = await api<{ message: string }>("/api/auth/wallet/challenge", { method: "POST" });
      const signature = await signMessageAsync({ message, account: address });
      await api("/api/auth/wallet/verify", { method: "POST", body: JSON.stringify({ address, signature }) });
      await refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "Wallet verification failed."); }
    finally { setBusy(false); }
  }
  return <main className="mx-auto max-w-3xl space-y-6 px-6 py-12"><h1 className="text-3xl font-bold">Your account</h1><AccountGate><section className="space-y-5 rounded-xl border p-6"><h2 className="text-xl font-semibold">{user?.username}</h2><p>Account sessions expire after 12 hours. Log out when using a shared device.</p><h3 className="font-semibold">Verified wallet</h3><p className="break-all">{user?.wallet_address || "No wallet linked yet"}</p><WalletButton />{verified ? <p className="text-green-700">Your connected wallet is verified.</p> : user?.wallet_address ? <p>Reconnect the verified wallet above to use your assets and checkout.</p> : <><p>Link one wallet to this account. The signature proves you control it and does not spend funds.</p><button disabled={!address || busy} onClick={verify} className="rounded-lg bg-blue-600 px-4 py-2 text-white disabled:opacity-50">{busy ? "Waiting for signature…" : "Verify connected wallet"}</button></>}
      {error && <p role="alert" className="text-red-700">{error}</p>}<div className="flex gap-5"><Link href="/dashboard" className="underline">Open dashboard</Link><button className="underline" onClick={() => logout().catch(() => setError("Logout failed. Retry."))}>Log out</button></div></section></AccountGate></main>;
}
