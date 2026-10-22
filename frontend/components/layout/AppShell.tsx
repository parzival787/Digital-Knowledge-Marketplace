"use client";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";
import Navbar from "./Navbar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const entryPage = ["/", "/login", "/signup"].includes(pathname);
  useEffect(() => {
    if (loading) return;
    if (!user && !entryPage) router.replace("/login");
    if (user && entryPage) router.replace("/dashboard");
  }, [user, loading, entryPage, router]);
  // Never mount application pages or wallet controls before session verification.
  if (loading || (!user && !entryPage) || (user && entryPage))
    return <main className="grid min-h-screen place-items-center bg-slate-50"><p role="status" className="text-slate-600">Opening your workspace...</p></main>;
  return user ? <div className="workspace min-h-screen"><Navbar />{children}</div> : <>{children}</>;
}
