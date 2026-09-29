"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api/client";
import { useAuth } from "@/providers/AuthProvider";

export default function AuthForm({ signup = false }: { signup?: boolean }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const { refresh } = useAuth();
  const router = useRouter();
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setError("");
    if (signup && password !== confirm) { setError("Passwords do not match."); return; }
    setBusy(true);
    try {
      await api(`/api/auth/${signup ? "signup" : "login"}`, { method: "POST", body: JSON.stringify({ username, password }) });
      await refresh(); router.replace("/account");
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to sign in."); }
    finally { setBusy(false); }
  }
  return <main className="mx-auto grid max-w-5xl gap-10 px-6 py-16 md:grid-cols-2">
    <section className="rounded-2xl bg-slate-950 p-8 text-white"><p className="text-sm uppercase tracking-widest text-blue-300">DKM / Your workspace</p><h1 className="mt-6 text-4xl font-bold">{signup ? "Start sharing knowledge." : "Welcome back."}</h1><p className="mt-6 text-slate-300">Keep your uploads and payment history in your own account. Link your wallet by signing a verification message.</p><p className="mt-6 text-sm text-slate-400">Your password signs you into DKM. Your wallet separately authorizes blockchain transactions.</p></section>
    <form onSubmit={submit} className="space-y-5 rounded-2xl border p-8">
      <h2 className="text-2xl font-semibold">{signup ? "Create an account" : "Log in"}</h2>
      <label className="block">Username<input className="mt-2 w-full rounded-lg border p-3" autoComplete="username" required minLength={3} maxLength={40} pattern="[a-zA-Z0-9_]{3,40}" value={username} onChange={e => setUsername(e.target.value)} /></label>
      <p className="text-xs text-slate-500">3–40 letters, numbers or underscores.</p>
      <label className="block">Password<input type="password" className="mt-2 w-full rounded-lg border p-3" autoComplete={signup ? "new-password" : "current-password"} required minLength={12} maxLength={128} value={password} onChange={e => setPassword(e.target.value)} /></label>
      {signup && <><p className="text-xs text-slate-500">Use at least 12 characters. Save it securely; password recovery is not configured.</p><label className="block">Confirm password<input type="password" autoComplete="new-password" required className="mt-2 w-full rounded-lg border p-3" value={confirm} onChange={e => setConfirm(e.target.value)} /></label></>}
      {error && <p role="alert" className="text-red-700">{error}</p>}
      <button disabled={busy} className="w-full rounded-lg bg-blue-600 p-3 font-semibold text-white disabled:opacity-50">{busy ? "Please wait…" : signup ? "Sign up" : "Log in"}</button>
      <p className="text-sm">{signup ? "Already registered?" : "New to DKM?"} <Link className="text-blue-700 underline" href={signup ? "/login" : "/signup"}>{signup ? "Log in" : "Create an account"}</Link></p>
    </form>
  </main>;
}
