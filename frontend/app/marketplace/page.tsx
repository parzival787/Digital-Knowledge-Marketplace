"use client";

import { useKnowledgeAsset, useTotalMinted } from "@/lib/blockchain/useKnowledgeAssets";
import AssetCard from "@/components/marketplace/AssetCard";
console.log("========== ASSET CARD DEBUG ==========");
console.log("AssetCard value:", AssetCard);
console.log("AssetCard typeof:", typeof AssetCard);
console.log("AssetCard is function:", typeof AssetCard === "function");
type KnowledgeAssetData = {
  ipfsCID: string;
  metadataCID: string;
  priceUSDC: bigint;
  creator: string;
  license: number | bigint;
  qualityScore: number | bigint;
  active: boolean;
  mintedAt: number | bigint;
};


function AssetItem({
  tokenId,
}: {
  tokenId: bigint;
}) {
  const {
    data: asset,
    isLoading,
    isError,
    error,
  } = useKnowledgeAsset(tokenId);

  if (isLoading) {
    return (
      <div className="rounded-xl border p-6">
        Loading Asset #{tokenId.toString()}...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-200 p-6 text-red-500">
        <p>
          Failed to load Asset #{tokenId.toString()}
        </p>

        <p className="mt-3 text-sm whitespace-pre-wrap">
          {error?.message || "Unknown error"}
        </p>
      </div>
    );
  }

  if (!asset) {
    return (
      <div className="rounded-xl border p-6">
        Asset #{tokenId.toString()} not found.
      </div>
    );
  }

  const assetData = asset as KnowledgeAssetData;

  return (
  <AssetCard
    tokenId={tokenId}
    asset={{
      ipfsCID: assetData.ipfsCID,
      metadataCID: assetData.metadataCID,
      priceUSDC: assetData.priceUSDC,
      seller: assetData.creator,
      license: Number(assetData.license),
      qualityScore: BigInt(assetData.qualityScore),
      mintedAt: BigInt(assetData.mintedAt),
      active: assetData.active,
    }}
  />
);
}

export default function MarketplacePage() {
  const {
    data: totalMinted,
    isLoading,
    isError,
  } = useTotalMinted();

  if (isLoading) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-12">
        Loading marketplace...
      </main>
    );
  }

  if (isError) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-12">
        <p className="text-red-500">
          Failed to read KnowledgeAsset contract.
        </p>
      </main>
    );
  }

  const total = Number(totalMinted ?? 0n);

  return (
    <main className="mx-auto max-w-7xl px-6 py-12">

      <div>
        <h1 className="text-3xl font-bold">
          Knowledge Marketplace
        </h1>

        <p className="mt-2 text-muted-foreground">
          Discover knowledge assets stored on-chain.
        </p>
      </div>

      {total === 0 ? (
        <div className="mt-10 rounded-xl border p-10 text-center">
          <p className="text-lg font-medium">
            No knowledge assets found.
          </p>
        </div>
      ) : (
        <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from(
            { length: total },
            (_, index) => {
              const tokenId = BigInt(index + 1);

              return (
                <AssetItem
                  key={tokenId.toString()}
                  tokenId={tokenId}
                />
              );
            }
          )}
        </div>
      )}

    </main>
  );
}