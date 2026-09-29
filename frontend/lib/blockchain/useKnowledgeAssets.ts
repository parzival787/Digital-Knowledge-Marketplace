"use client";

import {
  useReadContract,
  useWriteContract,
} from "wagmi";

import { knowledgeAssetContract, marketplaceContract } from "@/lib/blockchain/contracts";

export function useTotalMinted() {
  return useReadContract({
    address: knowledgeAssetContract.address,
    abi: knowledgeAssetContract.abi,
    functionName: "totalMinted",
  });
}

export function useKnowledgeAsset(tokenId: bigint) {
  return useReadContract({
    address: knowledgeAssetContract.address,
    abi: knowledgeAssetContract.abi,
    functionName: "getAsset",
    args: [tokenId],
  });
}

export function useAssetOwner(tokenId: bigint) {
  return useReadContract({
    address: knowledgeAssetContract.address,
    abi: knowledgeAssetContract.abi,
    functionName: "ownerOf",
    args: [tokenId],
  });
}

/* ============================================================
   MARKETPLACE
   ============================================================ */

export function useIsListed(tokenId: bigint) {
  return useReadContract({
    address: marketplaceContract.address,
    abi: marketplaceContract.abi,
    functionName: "isListed",
    args: [tokenId],
  });
}

/* ============================================================
   APPROVE NFT
   ============================================================ */

export function useApproveMarketplace() {
  return useWriteContract();
}

/* ============================================================
   LIST ASSET
   ============================================================ */

export function useListFixedPrice() {
  return useWriteContract();
}
