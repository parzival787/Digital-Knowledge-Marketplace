"use client";

import Link from "next/link";
import { useVerifiedWallet } from "@/providers/AuthProvider";
import { api, downloadAsset } from "@/lib/api/client";
import { acceptPurchaseQuote, type PurchaseQuote } from "@/lib/api/quotes";
import PurchaseQuoteSummary from "./PurchaseQuoteSummary";
import { useEffect, useState } from "react";
import { formatUnits } from "viem";
import { paymentToken, paymentAmount } from "@/lib/blockchain/paymentToken";

import {
  useAccount,
  useWaitForTransactionReceipt,
  useReadContract,
  useReadContracts,
  useSwitchChain,
  usePublicClient,
  useWriteContract,
} from "wagmi";
import { useQueryClient } from "@tanstack/react-query";
import { polygonAmoy } from "viem/chains";
import AuctionPanel from "./AuctionPanel";
import { usePaymentCapabilities, marketRouteAvailable } from "@/lib/api/capabilities";
import LegacyListing from "./LegacyListing";
import Reviews from "./Reviews";
import { checkListing, checkUnlisted, checkGas, confirmedReceipt, PurchaseCheckError } from "@/lib/blockchain/purchaseSafety";
import { marketplaceContract, knowledgeAssetContract, marketsForToken } from "@/lib/blockchain/contracts";

import {
  useIsListed,
  useTokenToListing,
  useListing,
  useMarketplaceWrite,
  useUSDCWrite,
} from "@/lib/blockchain/useMarketplace";

import {
  useAssetOwner,
  // keep all your existing imports
} from "@/lib/blockchain/useKnowledgeAssets";

type Asset = {
  ipfsCID: string;
  metadataCID: string;
  priceUSDC: bigint;
  seller: string;
  license: number;
  qualityScore: bigint;
  mintedAt: bigint;
  active: boolean;
};

function licenseName(license: number) {
  switch (license) {
    case 0:
      return "Open Access";
    case 1:
      return "Single Use";
    case 2:
      return "Commercial";
    default:
      return "Unknown";
  }
}

function formatUSDC(value: bigint) {
  return formatUnits(value, 6);
}

export default function AssetCard({
  tokenId,
  asset,
  saleMode = "all",
}: {
  tokenId: bigint;
  asset: Asset;
  saleMode?: string;
}) {
  const verified = useVerifiedWallet();
  const paymentCapabilities = usePaymentCapabilities();
  const profile = paymentCapabilities.data?.markets.find(m => m.address.toLowerCase() === marketplaceContract.address.toLowerCase());
  const mockUSDCContract = paymentToken(profile);
  const formatPayment = (value: bigint) => profile ? `${formatUnits(value, profile.decimals)} ${profile.symbol}` : "Checking payment token…";
  const [listingPrice, setListingPrice] = useState(formatUSDC(asset.priceUSDC));
  const [priceConfirmed, setPriceConfirmed] = useState(false);
  const purchaseAvailable = !paymentCapabilities.isError && marketRouteAvailable(paymentCapabilities.data, "fixed_price", marketplaceContract.address, mockUSDCContract.address);
  const { writeContractAsync } = useWriteContract();
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState("");
  const [access, setAccess] = useState<{access_granted: boolean; file_url: string | null; download_path: string | null; storage_notice: string} | null>(null);
  const [accessError, setAccessError] = useState("");
  const [showDetails, setShowDetails] = useState(false);

  const [metadata, setMetadata] = useState<Record<string, unknown> | null>(null);
  const [loadingMetadata, setLoadingMetadata] = useState(false);
  const [metadataError, setMetadataError] = useState("");

  const [listingError, setListingError] = useState("");
  const [buyError, setBuyError] = useState("");
  const [purchaseQuote, setPurchaseQuote] = useState<PurchaseQuote | null>(null);
  const [royaltiesEnabled, setRoyaltiesEnabled] = useState(false);

 const [royaltyRecipients, setRoyaltyRecipients] = useState<
  {
    wallet: string;
    shareBps: number;
  }[]
  >([]);

  const [buyStep, setBuyStep] = useState<
    "idle" | "approving" | "buying"
  >("idle");

  const { address: connectedAddress, chainId } = useAccount();
  const { switchChain, switchChainAsync } = useSwitchChain();
  const cache = useQueryClient();
  const publicClient = usePublicClient({ chainId: polygonAmoy.id });
  const { data: auctionIdData } = useReadContract({ ...marketplaceContract,
    chainId: polygonAmoy.id, functionName: "tokenToAuction", args: [tokenId], query: { refetchInterval: 10000 } });
  const auctionId = (auctionIdData as bigint | undefined) ?? 0n;
  const { data: purchases, isError: purchaseLookupFailed, isPending: purchaseLookupPending } = useReadContracts({
    allowFailure: false,
    contracts: marketsForToken(tokenId).map(market => ({ ...market,
      chainId: polygonAmoy.id, functionName: "hasPurchased", args: [tokenId, connectedAddress] })),
    query: { enabled: !!connectedAddress, refetchInterval: 10000 },
  });
  const purchased = purchases?.some(Boolean);


  const {
  data: assetOwner,
  isLoading: loadingOwner,
} = useAssetOwner(tokenId);

 const isOwner =
  !!connectedAddress &&
  !!assetOwner &&
  connectedAddress.toLowerCase() ===
    assetOwner.toString().toLowerCase();
  
  /*
   * ============================================================
   * MARKETPLACE READS
   * ============================================================
   */

  const {
    data: isListed,
    isLoading: isListingLoading,
  } = useIsListed(tokenId);

  const {
    data: listingId,
  } = useTokenToListing(tokenId);

  const {
    data: listing,
  } = useListing(
    listingId !== undefined
      ? BigInt(listingId as bigint)
      : 0n
  );

  /*
   * ============================================================
   * MARKETPLACE WRITES
   * ============================================================
   */

  const {
    approveNFT,
    nftApprovalHash,
    isNFTApprovalPending,

    listFixedPrice,
    listingHash,
    isListingPending,

    buyAsset,
    purchaseHash,
    isPurchasePending,
    purchaseError,
  } = useMarketplaceWrite();

  /*
   * ============================================================
   * USDC WRITE
   * ============================================================
   */

  const {
    approveMarketplace,
    hash: usdcApproveHash,
    isPending: isUSDCApprovePending,
    error: usdcError,
  } = useUSDCWrite(mockUSDCContract.address);

  /*
   * ============================================================
   * TRANSACTION RECEIPTS
   * ============================================================
   */

  const {
    isLoading: isUSDCApprovalConfirming,
  } = useWaitForTransactionReceipt({
    hash: usdcApproveHash,
  });

  const {
    isLoading: isNFTApprovalConfirming,
  } = useWaitForTransactionReceipt({
    hash: nftApprovalHash,
  });

  const {
    isLoading: isListingConfirming,
    isSuccess: isListingConfirmed,
  } = useWaitForTransactionReceipt({
    hash: listingHash,
  });

  const {
    isLoading: isPurchaseConfirming,
    isSuccess: isPurchaseConfirmed,
  } = useWaitForTransactionReceipt({
    hash: purchaseHash,
  });

  /*
   * ============================================================
   * IPFS METADATA
   * ============================================================
   */

  async function handleViewDetails() {
    if (showDetails) {
      setShowDetails(false);
      return;
    }

    setShowDetails(true);

    if (metadata) {
      return;
    }

    setLoadingMetadata(true);
    setMetadataError("");

    try {
      const data = await api<Record<string, unknown>>(`/api/assets/${tokenId}/details`);

      if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("Asset information is unavailable.");
      setMetadata(data);
    } catch (error) {
      setMetadataError(
        error instanceof Error
          ? "Could not load the description. Please try again shortly."
          : "Could not load the description."
      );
    } finally {
      setLoadingMetadata(false);
    }
  }

  /*
   * ============================================================
   * APPROVE NFT FOR MARKETPLACE
   * ============================================================
   */

  async function handleApprove() {
    if (!verified) { setListingError("Log in and verify your connected wallet in Account first."); return; }
    if (!connectedAddress) {
      setListingError(
        "Please connect your wallet first."
      );
      return;
    }

    setListingError("");

    try { await approveNFT(tokenId); } catch (error) { setListingError(error instanceof Error ? error.message : "Approval failed."); }
  }

  /*
   * ============================================================
   * LIST ASSET
   * ============================================================
   */

  async function handleList() {
  if (!verified) { setListingError("Log in and verify your connected wallet in Account first."); return; }
  if (chainId !== polygonAmoy.id) {
    setListingError("Switch to Polygon Amoy before listing.");
    return;
  }
  if (!connectedAddress) {
    setListingError("Please connect your wallet first.");
    return;
  }

  setListingError("");

  const recipients = royaltiesEnabled
    ? royaltyRecipients
    : [];

  if (royaltiesEnabled) {
    if (recipients.length === 0) {
      setListingError(
        "Add at least one royalty recipient or disable royalties."
      );
      return;
    }

    const seller = connectedAddress.toLowerCase();

    const sellerIncluded = recipients.some(
      (recipient) =>
        recipient.wallet.toLowerCase() === seller
    );

    if (sellerIncluded) {
      setListingError(
        "The asset owner cannot be a royalty recipient."
      );
      return;
    }

    const duplicateAddresses = new Set(
      recipients.map((recipient) =>
        recipient.wallet.toLowerCase()
      )
    );

    if (
      duplicateAddresses.size !==
      recipients.length
    ) {
      setListingError(
        "Royalty recipients cannot contain duplicate addresses."
      );
      return;
    }

    const totalBps = recipients.reduce(
      (total, recipient) =>
        total + recipient.shareBps,
      0
    );

    if (totalBps <= 0) {
      setListingError(
        "Royalty shares must be greater than 0."
      );
      return;
    }

    if (totalBps > 2000) {
      setListingError(
        "Total royalty share cannot exceed 20%."
      );
      return;
    }
  }

  try {
    if (!profile || !publicClient || !priceConfirmed) throw new Error("Confirm the listing price and payment token first.");
    const amount = paymentAmount(listingPrice, profile.decimals);
    await checkUnlisted(publicClient, marketsForToken(tokenId), tokenId);
    await listFixedPrice(tokenId, amount, recipients);
  } catch (error) { setListingError(error instanceof Error ? error.message : "Could not verify listing terms."); }
}

  /*
   * ============================================================
   * BUY ASSET
   * ============================================================
   */

  async function handleBuy() {
    if (!purchaseAvailable) { setBuyError("Payment route could not be verified. Check payment availability before retrying."); return; }
    if (!verified) { setBuyError("Log in and verify your connected wallet in Account first."); return; }
    setBuyError("");

    if (!connectedAddress) {
      setBuyError(
        "Please connect your wallet first."
      );
      return;
    }

    if (chainId !== polygonAmoy.id) {
      setBuyError("Switch to Polygon Amoy before purchasing.");
      return;
    }

    if (!isListed) {
      setBuyError(
        "This asset is no longer listed for sale."
      );
      return;
    }

    if (listingId === undefined) {
      setBuyError(
        "Marketplace listing could not be found."
      );
      return;
    }

    if (!publicClient || marketplacePrice <= 0n) return;
    try {
      setBuyStep("approving");
      if (!purchaseQuote) {
        setPurchaseQuote(await api<PurchaseQuote>(`/api/purchase-quotes/asset/${tokenId}`, { method: "POST" }));
        return;
      }
      const decimals = await publicClient.readContract({ ...mockUSDCContract, functionName: "decimals" }) as number;
      const expected = { buyer: connectedAddress, market: marketplaceContract.address, token: mockUSDCContract.address, decimals,
        tokenId, listingId: BigInt(listingId as bigint), amount: marketplacePrice };
      try { await acceptPurchaseQuote(purchaseQuote, expected); }
      catch (error) { setPurchaseQuote(null); throw new PurchaseCheckError(error instanceof Error ? error.message : "Review a new quote."); }
      await checkListing(publicClient, marketplaceContract, knowledgeAssetContract, tokenId, connectedAddress, BigInt(listingId as bigint), marketplacePrice, marketsForToken(tokenId).slice(1));
      const balance = await publicClient.readContract({ ...mockUSDCContract, functionName: "balanceOf", args: [connectedAddress] }) as bigint;
      if (balance < marketplacePrice) throw new PurchaseCheckError(`Insufficient ${profile?.symbol ?? "payment token"}. Fund your Amoy wallet before buying.`);
      const allowance = await publicClient.readContract({ ...mockUSDCContract, functionName: "allowance", args: [connectedAddress, marketplaceContract.address] }) as bigint;
      if (allowance < marketplacePrice) {
        await checkGas(publicClient, mockUSDCContract, "approve", [marketplaceContract.address, marketplacePrice], connectedAddress);
        const approvalHash = await approveMarketplace(marketplacePrice, connectedAddress);
        await confirmedReceipt(publicClient, approvalHash);
      }
      setBuyStep("buying");
      await checkGas(publicClient, marketplaceContract, "buyAsset", [BigInt(listingId as bigint)], connectedAddress);
      try { await acceptPurchaseQuote(purchaseQuote, expected); }
      catch (error) { setPurchaseQuote(null); throw new PurchaseCheckError(error instanceof Error ? error.message : "Review a new quote."); }
      await checkListing(publicClient, marketplaceContract, knowledgeAssetContract, tokenId, connectedAddress, BigInt(listingId as bigint), marketplacePrice, marketsForToken(tokenId).slice(1));
      const hash = await buyAsset(BigInt(listingId as bigint), connectedAddress);
      await confirmedReceipt(publicClient, hash);
      const entitled = await publicClient.readContract({ ...marketplaceContract, functionName: "hasPurchased", args: [tokenId, connectedAddress] });
      if (!entitled) throw new PurchaseCheckError("Transaction confirmed but access is not verified. Check status before paying again.");
      await cache.invalidateQueries();
    } catch (error) {
      setBuyError(error instanceof PurchaseCheckError ? error.message : "Purchase not verified. Check your wallet transaction history and access before retrying; a pending transaction may still complete.");
    } finally {
      setBuyStep("idle");
    }
  }

  /*
   * ============================================================
   * MARKETPLACE PRICE
   * ============================================================
   */

  // Solidity's public mapping getter returns six separate values (a tuple).
  const listingData = listing as readonly [bigint, bigint, string, number, boolean, number] | undefined;
  const marketplacePrice = listingData?.[1] ?? 0n;

  useEffect(() => {
    if (isListingConfirmed || isPurchaseConfirmed) void cache.invalidateQueries();
  }, [isListingConfirmed, isPurchaseConfirmed, cache]);

  useEffect(() => {
    if (usdcError || purchaseError) {
      setBuyStep("idle");
      setBuyError("Transaction failed or was cancelled. Check your balances and retry.");
    }
  }, [usdcError, purchaseError]);

  /*
   * ============================================================
   * USDC APPROVAL EFFECT
   * ============================================================
   */


  /*
   * ============================================================
   * PURCHASE CONFIRMATION EFFECT
   * ============================================================
   */

  /*
   * ============================================================
   * RETURN
   * ============================================================
   */

  if (saleMode === "auction" && !auctionId) return null;
  if (saleMode === "fixed" && !isListed) return null;

  return (
    <div id={`asset-${tokenId}`} className="rounded-2xl border bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
      {!verified && <p className="mb-4 text-sm"><Link href="/account" className="text-blue-700 underline">Log in and verify your wallet</Link> to create listings, bid or pay.</p>}

      {/* ======================================================
          HEADER
      ====================================================== */}

      <div className="flex items-center justify-between">

        <h2 className="text-xl font-bold">
          Knowledge Asset #{tokenId.toString()}
        </h2>

        <span
          className={
            asset.active
              ? "rounded-full px-3 py-1 text-xs bg-green-100 text-green-700"
              : "rounded-full px-3 py-1 text-xs bg-gray-100 text-gray-600"
          }
        >
          {asset.active
            ? "Active"
            : "Inactive"}
        </span>

      </div>

      {/* ======================================================
          ASSET INFORMATION
      ====================================================== */}
    <div>
  <span className="font-medium">
    Ownership:
  </span>{" "}
  {loadingOwner ? (
    <span className="text-gray-500">
      Checking...
    </span>
  ) : isOwner ? (
    <span className="font-medium text-green-600">
      You own this asset
    </span>
  ) : (
    <span className="text-gray-600">
      Not owned by you
    </span>
  )}
 </div>
      
      
      <div className="mt-6 space-y-3 text-sm">

        <div>
          <span className="font-medium">
            Price:
          </span>{" "}

          {formatUSDC(asset.priceUSDC)} USDC
        </div>

        <div>
          <span className="font-medium">
            Original Creator:
          </span>{" "}

          <span className="break-all">
            {asset.seller.slice(0, 6)}…{asset.seller.slice(-4)}
          </span>
        </div>

        <div>
          <span className="font-medium">
            License:
          </span>{" "}

          {licenseName(asset.license)}
        </div>

        <div>
          <span className="font-medium">
            AI assessment:
          </span>{" "}

          {asset.qualityScore.toString()}/100
        </div>

        {/* ====================================================
            MARKETPLACE STATUS
        ==================================================== */}

        <div>
          <span className="font-medium">
            Marketplace:
          </span>{" "}

          {isListingLoading ? (
            "Checking..."
          ) : auctionId ? (
            <span className="font-medium">Auction</span>
          ) : isListed ? (
            <span className="font-medium text-green-600">
              Listed
            </span>
          ) : (
            <span className="text-gray-600">
              Not Listed
            </span>
          )}
        </div>
      </div>

      {/* ======================================================
          SELL / LIST CONTROLS
      ====================================================== */}

      {!isListed && !auctionId && isOwner && asset.active && (
  <div className="mt-6 space-y-3">

    {/* APPROVE NFT */}

    <button
      type="button"
      onClick={handleApprove}
      disabled={
        isNFTApprovalPending ||
        isNFTApprovalConfirming
      }
      className="w-full rounded-md border px-4 py-2 font-medium hover:bg-gray-50 disabled:opacity-50"
    >
      {isNFTApprovalPending
        ? "Confirm approval in wallet..."
        : isNFTApprovalConfirming
        ? "Approving NFT..."
        : "Approve NFT"}
    </button>

    {/* ROYALTY SETTINGS */}

    <div className="rounded-lg border p-4">

      <h3 className="font-semibold">
        Royalty Settings
      </h3>

      <label className="mt-3 flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={royaltiesEnabled}
          onChange={(e) => {
            setRoyaltiesEnabled(e.target.checked);

            if (!e.target.checked) {
              setRoyaltyRecipients([]);
            }
          }}
        />

        Enable royalties for co-authors
      </label>

      {royaltiesEnabled && (
        <div className="mt-4 space-y-3">

          {royaltyRecipients.map(
            (recipient, index) => (
              <div
                key={index}
                className="rounded-md border p-3"
              >

                <div className="flex gap-2">

                  <input
                    type="text"
                    placeholder="Co-author wallet address"
                    value={recipient.wallet}
                    onChange={(e) => {
                      const updated = [
                        ...royaltyRecipients,
                      ];

                      updated[index] = {
                        ...updated[index],
                        wallet: e.target.value,
                      };

                      setRoyaltyRecipients(updated);
                    }}
                    className="flex-1 rounded-md border px-3 py-2 text-sm"
                  />

                  <input
                    type="number"
                    min="1"
                    max="2000"
                    placeholder="BPS"
                    value={recipient.shareBps || ""}
                    onChange={(e) => {
                      const updated = [
                        ...royaltyRecipients,
                      ];

                      updated[index] = {
                        ...updated[index],
                        shareBps:
                          Number(e.target.value) || 0,
                      };

                      setRoyaltyRecipients(updated);
                    }}
                    className="w-24 rounded-md border px-3 py-2 text-sm"
                  />

                  <button
                    type="button"
                    onClick={() => {
                      setRoyaltyRecipients(
                        royaltyRecipients.filter(
                          (_, i) => i !== index
                        )
                      );
                    }}
                    className="rounded-md border px-3 py-2 text-sm text-red-600"
                  >
                    Remove
                  </button>

                </div>

                <p className="mt-2 text-xs text-gray-500">
                  {(recipient.shareBps / 100).toFixed(2)}% royalty
                </p>

              </div>
            )
          )}

          <button
            type="button"
            onClick={() => {
              setRoyaltyRecipients([
                ...royaltyRecipients,
                {
                  wallet: "",
                  shareBps: 0,
                },
              ]);
            }}
            className="rounded-md border px-3 py-2 text-sm font-medium"
          >
            + Add Co-author
          </button>

          <div className="rounded-md bg-gray-50 p-3 text-sm">
            <div>
              Total co-author royalty:{" "}
              <span className="font-medium">
                {(
                  royaltyRecipients.reduce(
                    (total, recipient) =>
                      total + recipient.shareBps,
                    0
                  ) / 100
                ).toFixed(2)}
                %
              </span>
            </div>

            <div className="mt-1 text-xs text-gray-500">
              Maximum allowed: 20%
            </div>
          </div>

        </div>
      )}

    </div>

    {/* LIST */}
    <label className="block">Listing price ({profile?.symbol ?? "checking token"})<input className="w-full rounded border p-2" inputMode="decimal" value={listingPrice} onChange={event => { setListingPrice(event.target.value); setPriceConfirmed(false); }} /></label>
    <p className="text-sm">Reference price: {formatUSDC(asset.priceUSDC)} USDC. The listing uses the token shown above; no currency conversion is implied.</p>
    <label className="block"><input type="checkbox" checked={priceConfirmed} onChange={event => setPriceConfirmed(event.target.checked)} /> I confirm {listingPrice} {profile?.symbol} as my listing price.</label>

    <button
      type="button"
      onClick={handleList}
      disabled={
        isListingPending ||
        isListingConfirming || !profile || !priceConfirmed
      }
      className="w-full rounded-md bg-black px-4 py-2 font-medium text-white hover:bg-gray-800 disabled:opacity-50"
    >
      {isListingPending
        ? "Confirm listing in wallet..."
        : isListingConfirming
        ? "Listing Asset..."
        : "List Asset for Sale"}
    </button>

    {listingError && (
      <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">
        {listingError}
      </div>
    )}

  </div>
)}

      {/* ======================================================
          BUY CONTROLS
      ====================================================== */}

      {isOwner && !!isListed && <div className="mt-4 space-y-2"><button disabled={cancelling || !verified} className="rounded border p-2 disabled:opacity-50" onClick={async () => {
        if (!verified || !connectedAddress || !publicClient || !listingId) return;
        setCancelling(true); setCancelError("");
        try {
          if (chainId !== polygonAmoy.id) await switchChainAsync({ chainId: polygonAmoy.id });
          const fees = await checkGas(publicClient, marketplaceContract, "cancelListing", [listingId], connectedAddress);
          const hash = await writeContractAsync({ ...fees, ...marketplaceContract, account: connectedAddress, chainId: polygonAmoy.id, functionName: "cancelListing", args: [listingId] });
          await confirmedReceipt(publicClient, hash);
          await cache.invalidateQueries();
        } catch (error) { setCancelError(error instanceof Error ? error.message : "Cancellation failed or was rejected. Check your network and retry."); }
        finally { setCancelling(false); }
      }}>{cancelling ? "Cancelling listing…" : "Cancel listing"}</button>{cancelError && <p role="alert" className="text-red-700">{cancelError}</p>}</div>}

      {!!isListed && !isOwner && (
        <div className="mt-6 space-y-3">

          <div className="rounded-md border bg-gray-50 p-3 text-sm">
            <span className="font-medium">
              Purchase Price:
            </span>{" "}
            {formatPayment(marketplacePrice)}
          </div>
          {!purchaseAvailable && <p role="status">Wallet purchases are temporarily unavailable. Please retry when the network connection is restored.</p>}
          {purchaseQuote && <PurchaseQuoteSummary quote={purchaseQuote} />}

          <button
            type="button"
            onClick={handleBuy}
            disabled={
              !purchaseAvailable ||
              buyStep !== "idle" ||
              isUSDCApprovePending ||
              isUSDCApprovalConfirming ||
              isPurchasePending ||
              isPurchaseConfirming || purchaseLookupFailed || purchaseLookupPending || !listingData || marketplacePrice <= 0n || !asset.active || !!purchased
            }
            className="w-full rounded-md bg-black px-4 py-2 font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {buyStep === "approving" &&
            isUSDCApprovePending
              ? `Confirm ${profile?.symbol ?? "token"} approval...`
              : buyStep === "approving" &&
                isUSDCApprovalConfirming
              ? `Approving ${profile?.symbol ?? "token"}...`
              : buyStep === "buying" &&
                isPurchasePending
              ? "Confirm purchase in wallet..."
              : buyStep === "buying" &&
                isPurchaseConfirming
              ? "Purchasing Asset..."
              : `${purchaseQuote ? "Accept quote and buy" : "Review purchase"} - ${formatPayment(
                  marketplacePrice
                )}`}
          </button>

          <p className="text-sm">You need Amoy test POL for gas, including token approval and purchase. No asset is reserved while you fund your wallet or approve tokens.</p>
          {buyError && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              {buyError}
            </div>
          )}

          {usdcError && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              Approval was not verified. Check your wallet transaction history before retrying.
            </div>
          )}

          {purchaseError && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              Purchase failed or was cancelled. Check your balances and retry.
            </div>
          )}


        </div>
      )}

      {connectedAddress && chainId !== polygonAmoy.id && <button className="mt-4 rounded border p-2" onClick={() => switchChain({ chainId: polygonAmoy.id })}>Switch to Polygon Amoy</button>}
      {purchaseHash && <a className="mt-4 block break-all underline" href={`https://amoy.polygonscan.com/tx/${purchaseHash}`} target="_blank" rel="noreferrer">Check purchase transaction status</a>}
      {isOwner && marketsForToken(tokenId).slice(1).map(market => <LegacyListing key={market.address} tokenId={tokenId} marketAddress={market.address} />)}
      {purchaseLookupFailed && <p role="alert">Could not verify existing purchase access. Retry before paying.</p>}
      {purchased === true && <p className="mt-4 text-green-700" role="status">Purchase entitlement verified on-chain.</p>}
      {verified && <section className="mt-4 space-y-2"><button className="rounded border p-2" onClick={async () => { setAccessError(""); try { setAccess(await api(`/api/assets/${tokenId}/access`)); } catch (err) { setAccessError(err instanceof Error ? err.message : "Access check failed."); } }}>Check my access</button>{access && <><p>{access.access_granted ? "Your license access is verified." : "No active purchase entitlement for your wallet."}</p>{access.download_path && <button className="block text-blue-700 underline" onClick={async () => { setAccessError(""); try { await downloadAsset(access.download_path!); } catch (err) { setAccessError(err instanceof Error ? err.message : "Download failed."); } }}>Download protected file</button>}{access.file_url && <a className="block text-blue-700 underline" target="_blank" rel="noreferrer" href={access.file_url}>Open asset file</a>}<p className="text-xs text-slate-500">{access.storage_notice}</p></>}{accessError && <p role="alert">{accessError}</p>}</section>}
      <AuctionPanel tokenId={tokenId} auctionId={auctionId} price={asset.priceUSDC} canCreate={isOwner && !isListed && asset.active} />

      {/* ======================================================
          LISTING TRANSACTION HASH
      ====================================================== */}

      {listingHash && (
        <a className="mt-3 block text-sm text-blue-700 underline" href={`https://amoy.polygonscan.com/tx/${listingHash}`} target="_blank" rel="noreferrer">View listing confirmation</a>
      )}

      {/* ======================================================
          METADATA
      ====================================================== */}

      <button
        type="button"
        onClick={handleViewDetails}
        className="mt-6 w-full rounded-md border px-4 py-2 font-medium hover:bg-gray-50"
      >
        {showDetails
          ? "Hide Details"
          : "View Details"}
      </button>

      {showDetails && (
        <div className="mt-6 rounded-lg border bg-gray-50 p-4">

          <h3 className="font-semibold">
            About this asset
          </h3>

          {loadingMetadata && (
            <p className="mt-3 text-sm">
              Loading asset information...
            </p>
          )}

          {metadataError && (
            <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              {metadataError}
            </div>
          )}

          <Reviews tokenId={tokenId} canReview={verified && purchased === true && !isOwner} />
          {metadata && (
            <div className="mt-4 space-y-4 text-sm">
              <h4 className="text-lg font-semibold">{typeof metadata.title === "string" && metadata.title.trim() ? metadata.title : "Knowledge asset"}</h4>
              <p className="whitespace-pre-line">{typeof metadata.summary === "string" && metadata.summary.trim() ? metadata.summary : typeof metadata.description === "string" ? metadata.description : "The creator has not provided a description yet."}</p>
              {typeof metadata.domain === "string" && <p><span className="font-medium">Topic:</span> {metadata.domain}</p>}
              {Array.isArray(metadata.tags) && <div className="flex flex-wrap gap-2">{metadata.tags.filter((tag): tag is string => typeof tag === "string").slice(0, 12).map((tag, index) => <span key={index} className="rounded-full bg-white px-3 py-1">{tag}</span>)}</div>}
              <p><span className="font-medium">License:</span> {licenseName(asset.license)}</p>
              <p><span className="font-medium">AI assessment:</span> {asset.qualityScore.toString()}/100</p>
            </div>
          )}

        </div>
      )}

    </div>
  );
}
