"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import WalletButton from "@/components/wallet/WalletButton";
import { useAuth } from "@/providers/AuthProvider";
export default function Navbar() {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  if (loading || !user || ["/", "/signup", "/login"].includes(pathname)) return null;
  return <header className="border-b bg-white"><div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4"><Link href="/dashboard" className="text-xl font-bold">Knowledge Marketplace</Link><WalletButton /><nav aria-label="Main navigation" className="flex w-full flex-wrap items-center gap-x-6 gap-y-3 text-sm">
    {[["/marketplace", "Marketplace"], ["/auctions", "Auctions"], ["/funding", "Add USDC"], ["/search", "Search"], ["/mint", "Create asset"], ["/dashboard", "Dashboard"], ["/status", "Service status"]].map(([href, label]) => <Link key={href} href={href} className="hover:underline">{label}</Link>)}
    <div className="ml-auto flex gap-4">{loading ? <span>Checking session…</span> : user ? <Link className="font-semibold text-blue-700" href="/account">{user.username} / Account</Link> : <><Link href="/login">Log in</Link><Link className="font-semibold text-blue-700" href="/signup">Sign up</Link></>}</div>
  </nav></div></header>;
}
