"use client";

import { useReadContract } from "wagmi";

import { knowledgeAssetContract } from "@/lib/blockchain/contracts";

export default function BlockchainTest() {
  const {
    data,
    isLoading,
    isError,
    error,
  } = useReadContract({
    ...knowledgeAssetContract,
    functionName: "totalMinted",
  });

  if (isLoading) {
    return (
      <div className="mt-8 text-center">
        Reading blockchain...
      </div>
    );
  }

  if (isError) {
    console.error("KnowledgeAsset read error:", error);

    return (
      <div className="mt-8 text-center text-red-500">
        Failed to read KnowledgeAsset contract.
      </div>
    );
  }

  return (
    <div className="mt-8 text-center">
      <p className="text-lg font-semibold">
        Total Knowledge Assets Minted
      </p>

      <p className="mt-2 text-2xl font-bold">
        {data?.toString() ?? "0"}
      </p>
    </div>
  );
}