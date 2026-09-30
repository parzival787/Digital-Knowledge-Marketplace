"use client";
import Link from "next/link";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useAccount } from "wagmi";
import { api } from "@/lib/api/client";

export type User = { id: number; username: string; wallet_address: string | null };
const AuthContext = createContext<{ user: User | null; loading: boolean; refresh: () => Promise<void>; logout: () => Promise<void> }>({ user: null, loading: true, refresh: async () => {}, logout: async () => {} });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => {
    try { setUser(await api<User>("/api/auth/me")); } catch { setUser(null); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    void refresh();
    const check = () => { void refresh(); };
    window.addEventListener("focus", check);
    return () => window.removeEventListener("focus", check);
  }, [refresh]);
  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    setUser(null);
    window.location.assign("/");
  }
  return <AuthContext.Provider value={{ user, loading, refresh, logout }}>{children}</AuthContext.Provider>;
}
export const useAuth = () => useContext(AuthContext);
export function useVerifiedWallet() {
  const { user } = useAuth();
  const { address } = useAccount();
  return !!user?.wallet_address && !!address && user.wallet_address.toLowerCase() === address.toLowerCase();
}
export function AccountGate({ children, wallet = false }: { children: React.ReactNode; wallet?: boolean }) {
  const { user, loading } = useAuth();
  const verified = useVerifiedWallet();
  if (loading) return <p className="p-6" role="status">Checking your session…</p>;
  if (!user) return <div className="rounded-xl border bg-slate-50 p-6"><h2 className="text-xl font-semibold">Your account, your workspace</h2><p className="my-3">Log in to manage uploads, purchases and your wallet.</p><Link className="underline" href="/login">Log in</Link> or <Link className="underline" href="/signup">create an account</Link>.</div>;
  if (wallet && !verified) return <div className="rounded-xl border p-6"><p>Connect and verify your account wallet to continue. If you switched wallets, reconnect the wallet linked to this account.</p><Link className="mt-3 inline-block underline" href="/account">Manage wallet verification</Link></div>;
  return <>{children}</>;
}
