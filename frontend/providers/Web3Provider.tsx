"use client";

import { useState } from "react";
import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";

import {
  RainbowKitProvider,
} from "@rainbow-me/rainbowkit";

import {
  WagmiProvider,
} from "wagmi";

import { config } from "@/lib/blockchain/wagmi";

export default function Web3Provider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [queryClient] = useState(
    () => new QueryClient()
  );

  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider>
          {children}
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}