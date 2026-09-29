"use client";
import { useState } from "react";

import { useKnowledgeAsset, useTotalMinted } from "@/lib/blockchain/useKnowledgeAssets";
import AssetCard from "@/components/marketplace/AssetCard";
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
  saleMode,
}: {
  tokenId: bigint;
  saleMode: string;
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
    saleMode={saleMode}
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

export default function MarketplacePage({ searchParams }: { searchParams?: { mode?: string } }) {
  const [saleMode, setSaleMode] = useState(searchParams?.mode === "auction" ? "auction" : "all");
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
        <div className="mt-10">
          <div className="mb-6 flex gap-3" aria-label="Sale mode">
            {[["all", "All"], ["fixed", "Fixed Price"], ["auction", "Auctions"]].map(([value, label]) => <button key={value} aria-pressed={saleMode === value} onClick={() => setSaleMode(value)} className={`rounded border px-4 py-2 ${saleMode === value ? "bg-black text-white" : ""}`}>{label}</button>)}
          </div>
          <div className="peer grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from(
            { length: total },
            (_, index) => {
              const tokenId = BigInt(index + 1);

              return (
                <AssetItem
                  saleMode={saleMode}
                  key={tokenId.toString()}
                  tokenId={tokenId}
                />
              );
            }
          )}
          </div>
          <p className="hidden rounded border p-6 peer-empty:block">No assets match this sale mode.</p>
        </div>
      )}

    </main>
  );
}
