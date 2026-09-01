"use client";

import Link from "next/link";
import WalletButton from "@/components/wallet/WalletButton";

export default function Navbar() {
  return (
    <header className="border-b">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">

        <Link
          href="/"
          className="text-xl font-bold"
        >
          Knowledge Marketplace
        </Link>

        <nav className="hidden items-center gap-6 md:flex">

          <Link
            href="/marketplace"
            className="text-sm font-medium hover:underline"
          >
            Marketplace
          </Link>

          <Link
            href="/auctions"
            className="text-sm font-medium hover:underline"
          >
            Auctions
          </Link>

          <Link
            href="/mint"
            className="text-sm font-medium hover:underline"
          >
            Mint
          </Link>

          <Link
            href="/dashboard"
            className="text-sm font-medium hover:underline"
          >
            Dashboard
          </Link>

        </nav>

        <WalletButton />

      </div>
    </header>
  );
}