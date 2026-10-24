import type { PublicClient } from "viem";

// Amoy RPCs reject tips below 25 gwei, even when their estimate is lower.
const MIN_PRIORITY_FEE = 25_000_000_000n;

export async function amoyFees(client: Pick<PublicClient, "getChainId" | "getBlock" | "estimateFeesPerGas">) {
  if (await client.getChainId() !== 80002) throw new Error("Switch to Polygon Amoy before signing.");
  const [block, estimate] = await Promise.all([
    client.getBlock({ blockTag: "latest" }),
    client.estimateFeesPerGas({ type: "eip1559", chain: null }),
  ]);
  if (block.baseFeePerGas == null) throw new Error("Amoy base fee is unavailable. Retry before signing.");
  const maxPriorityFeePerGas = estimate.maxPriorityFeePerGas > MIN_PRIORITY_FEE
    ? estimate.maxPriorityFeePerGas : MIN_PRIORITY_FEE;
  const bufferedFee = block.baseFeePerGas * 2n + maxPriorityFeePerGas;
  return {
    maxPriorityFeePerGas,
    maxFeePerGas: estimate.maxFeePerGas > bufferedFee ? estimate.maxFeePerGas : bufferedFee,
  };
}
