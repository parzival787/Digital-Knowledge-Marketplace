import { erc20Abi, parseUnits, formatUnits, zeroAddress, type Abi } from "viem";
import type { MarketProfile } from "@/lib/api/capabilities";

export function paymentToken(profile: MarketProfile | undefined) {
  return { address: (profile?.token_address ?? zeroAddress) as `0x${string}`, abi: erc20Abi as Abi };
}

export function formatTokenAmount(profile: MarketProfile | undefined, value: string) {
  return profile ? `${formatUnits(BigInt(value), profile.decimals)} ${profile.symbol}` : `${value} base units (token unverified)`;
}

export function paymentAmount(value: string, decimals: number) {
  if (!Number.isInteger(decimals) || decimals < 0 || decimals > 77 ||
      !/^\d+(\.\d+)?$/.test(value) || (value.split(".")[1]?.length ?? 0) > decimals)
    throw new Error(`Enter an amount with at most ${decimals} decimal places.`);
  const amount = parseUnits(value, decimals);
  if (amount <= 0n || amount >= 2n ** 256n) throw new Error("Amount is outside the payment token range.");
  return amount;
}
