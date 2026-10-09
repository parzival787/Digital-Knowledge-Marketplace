import type { Address, Hash, PublicClient } from "viem";

type Contract = { address: Address; abi: readonly unknown[] };
type Client = Pick<PublicClient, "readContract" | "getBlockNumber" | "getBalance" | "estimateContractGas" | "estimateFeesPerGas" | "waitForTransactionReceipt" | "getBlock" | "getTransactionReceipt">;

export class PurchaseCheckError extends Error {}

export async function checkListing(client: Client, market: Contract, registry: Contract, token: bigint, buyer: Address, expectedId: bigint, expectedPrice: bigint, legacyMarkets: readonly Contract[] = []) {
  const blockNumber = await client.getBlockNumber({ cacheTime: 0 });
  const id = await client.readContract({ ...market, functionName: "tokenToListing", args: [token], blockNumber }) as bigint;
  if (!id || id !== expectedId) throw new PurchaseCheckError("The listing changed. Refresh the asset and review its price before buying.");
  const [listing, asset, purchased] = await Promise.all([
    client.readContract({ ...market, functionName: "listings", args: [id], blockNumber }),
    client.readContract({ ...registry, functionName: "getAsset", args: [token], blockNumber }),
    client.readContract({ ...market, functionName: "hasPurchased", args: [token, buyer], blockNumber }),
  ]);
  const row = listing as readonly [bigint, bigint, Address, number, boolean];
  if (!row[4] || row[3] !== 0 || row[0] !== token || !(asset as readonly unknown[])[6])
    throw new PurchaseCheckError("This asset is no longer available at a fixed price.");
  if (row[1] !== expectedPrice || row[1] <= 0n)
    throw new PurchaseCheckError("The price changed. Refresh the asset and review the new price before buying.");
  const legacyPurchases = await Promise.all(legacyMarkets.map(previous => client.readContract({
    ...previous, functionName: "hasPurchased", args: [token, buyer], blockNumber,
  })));
  if (purchased || legacyPurchases.some(Boolean) || row[2].toLowerCase() === buyer.toLowerCase())
    throw new PurchaseCheckError("Your wallet already owns or has access to this asset.");
}

export async function checkGas(client: Client, contract: Contract, functionName: string, args: readonly unknown[], account: Address) {
  const [gas, fees, balance] = await Promise.all([
    client.estimateContractGas({ ...contract, functionName, args, account }),
    client.estimateFeesPerGas(), client.getBalance({ address: account }),
  ]);
  const fee = fees.maxFeePerGas ?? fees.gasPrice;
  if (fee === undefined) throw new PurchaseCheckError("Could not estimate network fees. Retry before signing.");
  if (balance < (gas * fee * 120n + 99n) / 100n)
    throw new PurchaseCheckError("Insufficient POL for the estimated network fee. Add Amoy test POL to this wallet and retry. USDC cannot pay gas.");
}

export async function confirmedReceipt(client: Client, hash: Hash) {
  const receipt = await client.waitForTransactionReceipt({ hash, confirmations: 2 });
  if (receipt.transactionHash.toLowerCase() !== hash.toLowerCase()) throw new PurchaseCheckError("Transaction was replaced. Check your wallet history and access before retrying.");
  const [block, current, height] = await Promise.all([
    client.getBlock({ blockNumber: receipt.blockNumber }),
    client.getTransactionReceipt({ hash: receipt.transactionHash }), client.getBlockNumber({ cacheTime: 0 }),
  ]);
  if (current.status !== "success" || receipt.status !== "success") throw new PurchaseCheckError("Transaction reverted. Refresh before retrying.");
  if (block.hash !== receipt.blockHash || current.blockHash !== receipt.blockHash || height < receipt.blockNumber + 1n)
    throw new PurchaseCheckError("Transaction confirmation changed. Check its status before sending another transaction.");
  return current;
}
