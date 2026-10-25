"use client";
import { useState } from "react";
import { useAccount, usePublicClient, useReadContract, useSwitchChain, useWriteContract } from "wagmi";
import { useQueryClient } from "@tanstack/react-query";
import { useVerifiedWallet } from "@/providers/AuthProvider";
import { marketplaceContract } from "@/lib/blockchain/contracts";
import { checkGas, confirmedReceipt } from "@/lib/blockchain/purchaseSafety";

export default function LegacyListing({ tokenId, marketAddress }: { tokenId: bigint; marketAddress: `0x${string}` }) {
  const market = { ...marketplaceContract, address: marketAddress };
  const { address, chainId } = useAccount();
  const verified = useVerifiedWallet();
  const client = usePublicClient({ chainId: 80002 });
  const { switchChainAsync } = useSwitchChain();
  const { writeContractAsync } = useWriteContract();
  const cache = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [hash, setHash] = useState<`0x${string}` | null>(null);
  const listing = useReadContract({ ...market, chainId: 80002, functionName: "tokenToListing", args: [tokenId] });
  const id = (listing.data as bigint | undefined) ?? 0n;
  const details = useReadContract({ ...market, chainId: 80002, functionName: "listings", args: [id], query: { enabled: id > 0n } });
  const row = details.data as readonly [bigint, bigint, `0x${string}`, number, boolean] | undefined;
  async function cancel() {
    if (!verified || !address || !client || !row || row[2].toLowerCase() !== address.toLowerCase()) return;
    setBusy(true); setStatus("");
    try {
      if (chainId !== 80002) await switchChainAsync({ chainId: 80002 });
      const fees = await checkGas(client, market, "cancelListing", [id], address);
      const tx = await writeContractAsync({ ...fees, ...market, chainId: 80002, functionName: "cancelListing", args: [id], account: address });
      setHash(tx);
      await confirmedReceipt(client, tx);
      await cache.invalidateQueries();
      setStatus("Previous listing cancelled. You can now review relisting on the current marketplace.");
    } catch (error) { setStatus(error instanceof Error ? error.message : "Cancellation not verified. Check the transaction before retrying."); }
    finally { setBusy(false); }
  }
  if (listing.isError || details.isError) return <p role="alert">Could not check a previous listing. Retry before relisting.</p>;
  if (!row?.[4] || row[2].toLowerCase() !== address?.toLowerCase()) return null;
  return <section className="mt-4 space-y-2 rounded border p-3" aria-label="Previous marketplace listing">
    <p className="break-all">Active listing on previous marketplace: {marketAddress}</p>
    <p>Cancel this listing before relisting. Existing buyer access is retained.</p>
    <button className="rounded border p-2" disabled={busy || !verified} onClick={cancel}>Cancel previous listing</button>
    <p role="status">{status}</p>
    {hash && <a className="underline" href={`https://amoy.polygonscan.com/tx/${hash}`} target="_blank" rel="noreferrer">Check cancellation transaction</a>}
  </section>;
}
