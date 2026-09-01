"use client";

import { useEffect, useState } from "react";

import {
  useAccount,
  useWaitForTransactionReceipt,
} from "wagmi";

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
  return (Number(value) / 1_000_000).toFixed(2);
}

export default function AssetCard({
  tokenId,
  asset,
}: {
  tokenId: bigint;
  asset: Asset;
}) {
  const [showDetails, setShowDetails] = useState(false);

  const [metadata, setMetadata] = useState<any>(null);
  const [loadingMetadata, setLoadingMetadata] = useState(false);
  const [metadataError, setMetadataError] = useState("");

  const [listingError, setListingError] = useState("");
  const [buyError, setBuyError] = useState("");
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

  const { address: connectedAddress } = useAccount();

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
    refetch: refetchListing,
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
    nftApprovalError,

    listFixedPrice,
    listingHash,
    isListingPending,
    listingError: marketplaceListingError,

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
  } = useUSDCWrite();

  /*
   * ============================================================
   * TRANSACTION RECEIPTS
   * ============================================================
   */

  const {
    isLoading: isUSDCApprovalConfirming,
    isSuccess: isUSDCApprovalConfirmed,
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
      const gatewayUrl =
        `https://ipfs.io/ipfs/${asset.metadataCID}`;

      const response = await fetch(gatewayUrl);

      if (!response.ok) {
        throw new Error(
          `Failed to fetch metadata. HTTP ${response.status}`
        );
      }

      const data = await response.json();

      setMetadata(data);
    } catch (error) {
      console.error("Metadata fetch error:", error);

      setMetadataError(
        error instanceof Error
          ? error.message
          : "Unable to load metadata from IPFS."
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

  function handleApprove() {
    if (!connectedAddress) {
      setListingError(
        "Please connect your wallet first."
      );
      return;
    }

    setListingError("");

    approveNFT(tokenId);
  }

  /*
   * ============================================================
   * LIST ASSET
   * ============================================================
   */

  function handleList() {
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

  listFixedPrice(
    tokenId,
    asset.priceUSDC,
    recipients
  );
}

  /*
   * ============================================================
   * BUY ASSET
   * ============================================================
   */

  function handleBuy() {
    setBuyError("");

    if (!connectedAddress) {
      setBuyError(
        "Please connect your wallet first."
      );
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

    const purchasePrice = marketplacePrice;
    setBuyStep("approving");

    approveMarketplace(purchasePrice);
  }

  /*
   * ============================================================
   * MARKETPLACE PRICE
   * ============================================================
   */

  const listingData = listing as any;

  const marketplacePrice =
    listingData?.price !== undefined
      ? BigInt(listingData.price)
      : asset.priceUSDC;

  /*
   * ============================================================
   * USDC APPROVAL EFFECT
   * ============================================================
   */

  useEffect(() => {
    if (
      buyStep !== "approving" ||
      !isUSDCApprovalConfirmed ||
      listingId === undefined
    ) {
      return;
    }

    setBuyStep("buying");

    buyAsset(
      BigInt(listingId as bigint)
    );
  }, [
    buyStep,
    isUSDCApprovalConfirmed,
    listingId,
    buyAsset,
  ]);

  /*
   * ============================================================
   * PURCHASE CONFIRMATION EFFECT
   * ============================================================
   */

  useEffect(() => {
    if (
      buyStep !== "buying" ||
      !isPurchaseConfirmed
    ) {
      return;
    }

    setBuyStep("idle");

    refetchListing();
  }, [
    buyStep,
    isPurchaseConfirmed,
    refetchListing,
  ]);

  /*
   * ============================================================
   * RETURN
   * ============================================================
   */

  return (
    <div className="rounded-xl border p-6 shadow-sm">

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
            IPFS CID:
          </span>{" "}

          <span className="break-all">
            {asset.ipfsCID}
          </span>
        </div>

        <div>
          <span className="font-medium">
            Metadata CID:
          </span>{" "}

          <span className="break-all">
            {asset.metadataCID}
          </span>
        </div>

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
            {asset.seller}
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
            Quality Score:
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

      {!isListed && (
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

    <button
      type="button"
      onClick={handleList}
      disabled={
        isListingPending ||
        isListingConfirming
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

      {isListed && (
        <div className="mt-6 space-y-3">

          <div className="rounded-md border bg-gray-50 p-3 text-sm">
            <span className="font-medium">
              Purchase Price:
            </span>{" "}
            {formatUSDC(marketplacePrice)} USDC
          </div>

          <button
            type="button"
            onClick={handleBuy}
            disabled={
              buyStep !== "idle" ||
              isUSDCApprovePending ||
              isUSDCApprovalConfirming ||
              isPurchasePending ||
              isPurchaseConfirming
            }
            className="w-full rounded-md bg-black px-4 py-2 font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {buyStep === "approving" &&
            isUSDCApprovePending
              ? "Confirm USDC approval..."
              : buyStep === "approving" &&
                isUSDCApprovalConfirming
              ? "Approving USDC..."
              : buyStep === "buying" &&
                isPurchasePending
              ? "Confirm purchase in wallet..."
              : buyStep === "buying" &&
                isPurchaseConfirming
              ? "Purchasing Asset..."
              : `Buy for ${formatUSDC(
                  marketplacePrice
                )} USDC`}
          </button>

          {buyError && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              {buyError}
            </div>
          )}

          {usdcError && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              {usdcError.message}
            </div>
          )}

          {purchaseError && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              {purchaseError.message}
            </div>
          )}

        </div>
      )}

      {/* ======================================================
          LISTING TRANSACTION HASH
      ====================================================== */}

      {listingHash && (
        <div className="mt-3 break-all text-xs text-gray-500">
          Marketplace transaction:
          <br />
          {listingHash}
        </div>
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
            Metadata
          </h3>

          {loadingMetadata && (
            <p className="mt-3 text-sm">
              Loading metadata from IPFS...
            </p>
          )}

          {metadataError && (
            <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              {metadataError}
            </div>
          )}

          {metadata && (
            <pre className="mt-3 overflow-auto rounded-md bg-white p-3 text-xs">
              {JSON.stringify(
                metadata,
                null,
                2
              )}
            </pre>
          )}

        </div>
      )}

    </div>
  );
}
