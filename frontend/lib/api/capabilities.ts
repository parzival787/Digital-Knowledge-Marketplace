"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

export type PaymentRoute = { enabled: boolean; state: string; message: string; purpose: string; sandbox_only: boolean };
export type Capabilities = {
  version: number; chain_id: number;
  markets: { address: string; token_address: string; paused: boolean }[];
  routes: Record<string, PaymentRoute>;
};
export function usePaymentCapabilities() {
  return useQuery({ queryKey: ["payment-capabilities"], queryFn: () => api<Capabilities>("/api/capabilities"),
    staleTime: 15000, refetchInterval: 30000, retry: false });
}
export function marketRouteAvailable(data: Capabilities | undefined, route: "fixed_price" | "auction", market: string, token: string) {
  return !!data && data.chain_id === 80002 && !!data.routes[route]?.enabled &&
    data.markets.some(value => value.address.toLowerCase() === market.toLowerCase() &&
      value.token_address.toLowerCase() === token.toLowerCase() && (route === "auction" || !value.paused));
}
