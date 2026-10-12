"use client";

import { useVerifiedWallet } from "@/providers/AuthProvider";
import { usePaymentCapabilities, marketRouteAvailable } from "@/lib/api/capabilities";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useAccount, usePublicClient, useReadContract, useSwitchChain, useWriteContract } from "wagmi";
import { useQueryClient } from "@tanstack/react-query";
import { formatUnits } from "viem";
import { polygonAmoy } from "viem/chains";
import { marketplaceContract, entitlementMarketplaceContracts } from "@/lib/blockchain/contracts";
import { paymentToken, paymentAmount } from "@/lib/blockchain/paymentToken";

import { checkGas, checkUnlisted, confirmedReceipt, PurchaseCheckError } from "@/lib/blockchain/purchaseSafety";

type Auction = readonly [bigint, bigint, bigint, `0x${string}`, `0x${string}`, boolean, boolean, number, number];

export default function AuctionPanel({ tokenId, auctionId, canCreate, price, marketAddress }: {
  tokenId: bigint; auctionId: bigint; canCreate: boolean; price: bigint; marketAddress?: `0x${string}`;
}) {
  const market = { ...marketplaceContract, address: marketAddress ?? marketplaceContract.address };
  const paymentCapabilities = usePaymentCapabilities();
  const profile = paymentCapabilities.data?.markets.find(value => value.address.toLowerCase() === market.address.toLowerCase());
  const mockUSDCContract = paymentToken(profile);
  const display = (value: bigint) => profile ? `${formatUnits(value, profile.decimals)} ${profile.symbol}` : "Checking token…";
  const auctionAvailable = !paymentCapabilities.isError && marketRouteAvailable(paymentCapabilities.data, "auction", market.address, mockUSDCContract.address);
  const newPaymentsAvailable = auctionAvailable && !paymentCapabilities.data?.markets.find(value => value.address.toLowerCase() === market.address.toLowerCase())?.paused;
  const verified = useVerifiedWallet();
  const { address, chainId } = useAccount();
  const client = usePublicClient({ chainId: polygonAmoy.id });
  const { switchChainAsync } = useSwitchChain();
  const { writeContractAsync } = useWriteContract();
  const cache = useQueryClient();
  const [lastAuctionId, setLastAuctionId] = useState(auctionId);
  const resolvedId = auctionId || lastAuctionId;
  const { data, isError } = useReadContract({ ...market, chainId: polygonAmoy.id,
    functionName: "auctions", args: [resolvedId], query: { enabled: resolvedId > 0n, refetchInterval: 10000 } });
  const { data: refund } = useReadContract({ ...market, chainId: polygonAmoy.id,
    functionName: "pendingRefunds", args: [address], query: { enabled: !!address, refetchInterval: 10000 } });
  const auction = data as Auction | undefined;
  const [bid, setBid] = useState("");
  const [hours, setHours] = useState("24");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [transactionHash, setTransactionHash] = useState<`0x${string}` | null>(null);
  const [now, setNow] = useState(0);
  const [reserve, setReserve] = useState(formatUnits(price, 6));
  const [reserveConfirmed, setReserveConfirmed] = useState(false);
  useEffect(() => { if (auctionId) setLastAuctionId(auctionId); }, [auctionId]);
  useEffect(() => {
    setNow(Math.floor(Date.now() / 1000));
    const timer = setInterval(() => setNow(Math.floor(Date.now() / 1000)), 1000);
    return () => clearInterval(timer);
  }, []);

  const minimum = auction ? (auction[2] > 0n ? auction[2] + 1n : auction[1]) : price;
  const ended = !!auction && now >= Number(auction[8]);
  const started = !!auction && now >= Number(auction[7]);
  const winner = !!address && auction?.[3].toLowerCase() === address.toLowerCase();
  const seller = !!address && auction?.[4].toLowerCase() === address.toLowerCase();
  const remaining = auction ? Math.max(0, Number(auction[8]) - now) : 0;

  async function transact(action: "bid" | "create" | "end" | "refund") {
    setError("");
    if (!auctionAvailable || !profile) { setError("Auction deployment could not be verified. Retry availability checks before signing."); return; }
    if ((action === "bid" || action === "create") && !newPaymentsAvailable) { setError("Marketplace is paused for new bids and auctions."); return; }
    if (!verified) { setError("Log in and verify your connected wallet in Account first."); return; }
    if (!address || !client) { setError("Connect your wallet first."); return; }
    setBusy(true);
    try {
      if (chainId !== polygonAmoy.id) { await switchChainAsync({ chainId: polygonAmoy.id }); }
      async function send(contract: typeof market | typeof mockUSDCContract, functionName: string, args: readonly unknown[]) {
        await checkGas(client!, contract, functionName, args, address!);
        const hash = await writeContractAsync({ ...contract, functionName, args, account: address, chainId: polygonAmoy.id });
        setTransactionHash(hash);
        setStatus("Waiting for transaction confirmation…");
        await confirmedReceipt(client!, hash);
      }
      setStatus("Confirm in your wallet…");
      if (action === "bid") {
        let amount: bigint;
        try { amount = paymentAmount(bid, profile.decimals); }
        catch (error) { throw new PurchaseCheckError((error as Error).message); }
        if (amount < minimum) throw new PurchaseCheckError(`Minimum bid is ${display(minimum)}.`);
        const balance = await client.readContract({ ...mockUSDCContract, functionName: "balanceOf", args: [address] }) as bigint;
        if (balance < amount) throw new PurchaseCheckError(`Insufficient ${profile.symbol} balance for this bid.`);
        const allowance = await client.readContract({ ...mockUSDCContract, functionName: "allowance", args: [address, market.address] }) as bigint;
        if (allowance < amount) { setStatus(`Approve ${profile.symbol} in your wallet…`); await send(mockUSDCContract, "approve", [market.address, amount]); }
        setStatus("Confirm your bid in your wallet…");
        await send(market, "placeBid", [resolvedId, amount]);
      } else if (action === "create") {
        if (!reserveConfirmed) throw new PurchaseCheckError("Confirm the reserve price and token first.");
        let reserveAmount: bigint;
        try { reserveAmount = paymentAmount(reserve, profile.decimals); }
        catch (error) { throw new PurchaseCheckError((error as Error).message); }
        await checkUnlisted(client, entitlementMarketplaceContracts, tokenId);
        const duration = Number(hours);
        if (!Number.isInteger(duration) || duration < 1 || duration > 720) throw new PurchaseCheckError("Choose a duration from 1 to 720 hours.");
        const block = await client.getBlock();
        await send(market, "createAuction", [tokenId, reserveAmount, block.timestamp, block.timestamp + BigInt(duration * 3600), []]);
      } else {
        await send(market, action === "end" ? "endAuction" : "withdrawRefund", action === "end" ? [resolvedId] : []);
      }
      await cache.invalidateQueries();
      setStatus(action === "bid" ? "Bid confirmed." : action === "create" ? "Auction created." : action === "end" ? "Auction finalized. The winner’s entitlement is recorded on-chain." : "Refund withdrawn.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      setError(err instanceof PurchaseCheckError ? err.message : /reject|denied/i.test(message) ? "Transaction cancelled in your wallet. You can retry." :
        "Transaction not verified. Check its status before retrying; a pending transaction may still complete.");
      setStatus("");
    } finally { setBusy(false); }
  }

  if (!resolvedId && !canCreate && !refund) return null;
  return <section className="mt-5 space-y-3 rounded-lg border p-4" aria-label="Auction">
    {!auctionAvailable && <p role="status">Auction availability could not be verified. Actions are disabled until the deployment is checked.</p>}
    {marketAddress && marketAddress !== marketplaceContract.address && <p className="break-all text-sm">Previous marketplace: {marketAddress}</p>}
    <h3 className="font-semibold">Auction{resolvedId > 0n ? ` #${resolvedId}` : ""}</h3>
    <p className="text-sm">Every auction transaction needs Amoy test POL for gas. Funding a wallet does not place or reserve a bid.</p>
    <Link className="block underline" href="/funding#crypto">Fund a bid using another cryptocurrency</Link>
    {isError && <p role="alert">Unable to load auction state.</p>}
    {!!resolvedId && !auction && !isError && <p>Loading auction…</p>}
    {auction && <>
      <Link className="block underline" href={`/marketplace#asset-${auction[0]}`}>View asset #{auction[0].toString()}</Link>
      <p>Starting price: {display(auction[1])}</p>
      <p>{auction[2] ? `Highest bid: ${display(auction[2])}` : "No bids yet"}</p>
      {auction[2] > 0n && <p className="break-all">{auction[6] ? "Winner" : "Highest bidder"}: {auction[3]} {winner && "(you)"}</p>}
      <p>Ends: {new Date(Number(auction[8]) * 1000).toLocaleString()}</p>
      <p>{auction[6] ? "Auction completed" : ended ? "Auction ended — ready to finalize" : !started ? "Bidding has not started" : `Time remaining: ${Math.floor(remaining / 3600)}h ${Math.floor(remaining % 3600 / 60)}m ${remaining % 60}s`}</p>
      {auction[5] && !ended && started && !seller && <>
        <label className="block">Your bid ({profile?.symbol})<input className="mt-1 w-full rounded border p-2" inputMode="decimal" value={bid} onChange={e => setBid(e.target.value)} placeholder={profile ? formatUnits(minimum, profile.decimals) : ""} /></label>
        <button className="rounded border px-3 py-2 disabled:opacity-50" disabled={busy || !address || !newPaymentsAvailable} onClick={() => transact("bid")}>Place bid</button>
      </>}
      {auction[5] && ended && <button className="rounded border px-3 py-2 disabled:opacity-50" disabled={busy || !address || !auctionAvailable} onClick={() => transact("end")}>Finalize auction</button>}
    </>}
    {!auctionId && canCreate && <>
      <p>Reference price: {formatUnits(price, 6)} USDC. No co-author royalties.</p>
      <label className="block">Reserve price ({profile?.symbol})<input className="w-full rounded border p-2" inputMode="decimal" value={reserve} onChange={event => { setReserve(event.target.value); setReserveConfirmed(false); }} /></label>
      <label className="block"><input type="checkbox" checked={reserveConfirmed} onChange={event => setReserveConfirmed(event.target.checked)} /> I confirm {reserve} {profile?.symbol} as the reserve price.</label>
      <label className="block">Duration (hours)<input className="mt-1 w-full rounded border p-2" type="number" min="1" max="720" value={hours} onChange={e => setHours(e.target.value)} /></label>
      <button className="rounded border px-3 py-2 disabled:opacity-50" disabled={busy || !newPaymentsAvailable || !reserveConfirmed} onClick={() => transact("create")}>Create auction</button>
    </>}
    {(refund as bigint | undefined ?? 0n) > 0n && <>
      <p>You have {display(refund as bigint)} in refundable bids across the marketplace.</p>
      <button className="rounded border px-3 py-2 disabled:opacity-50" disabled={busy || !auctionAvailable} onClick={() => transact("refund")}>Withdraw bid refund</button>
    </>}
    {!address && <p>Connect your wallet to bid or finalize.</p>}
    {transactionHash && <a className="block underline" target="_blank" rel="noreferrer" href={`https://amoy.polygonscan.com/tx/${transactionHash}`}>Check auction transaction status</a>}
    <p role="status">{status}</p>
    {error && <p className="text-red-600" role="alert">{error}</p>}
  </section>;
}
