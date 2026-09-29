"use client";

import {
  useReadContract,
  useWriteContract,
} from "wagmi";
import { polygonAmoy } from "viem/chains";

import {
  marketplaceContract,
  mockUSDCContract,
  knowledgeAssetContract,
} from "@/lib/blockchain/contracts";

/**
 * Check whether a KnowledgeAsset is currently listed.
 */
export function useIsListed(tokenId: bigint) {
  return useReadContract({
    chainId: polygonAmoy.id,
    address: marketplaceContract.address,
    abi: marketplaceContract.abi,
    functionName: "isListed",
    args: [tokenId],
  });
}

/**
 * Get the marketplace listing ID associated with a token.
 */
export function useTokenToListing(tokenId: bigint) {
  return useReadContract({
    chainId: polygonAmoy.id,
    address: marketplaceContract.address,
    abi: marketplaceContract.abi,
    functionName: "tokenToListing",
    args: [tokenId],
  });
}

/**
 * Get complete listing information.
 */
export function useListing(listingId: bigint) {
  return useReadContract({
    chainId: polygonAmoy.id,
    address: marketplaceContract.address,
    abi: marketplaceContract.abi,
    functionName: "listings",
    args: [listingId],
    query: {
      enabled: listingId > 0n,
    },
  });
}

/**
 * Marketplace write operations.
 *
 * Each operation has its own transaction hash/state.
 * This prevents a purchase transaction from overwriting
 * the existing listing transaction state.
 */
export function useMarketplaceWrite() {
  const nftApproval = useWriteContract();
  const listingWrite = useWriteContract();
  const purchaseWrite = useWriteContract();

  function approveNFT(tokenId: bigint) {
    nftApproval.writeContract({
      chainId: polygonAmoy.id,
      address: knowledgeAssetContract.address,
      abi: knowledgeAssetContract.abi,
      functionName: "approve",
      args: [
        marketplaceContract.address,
        tokenId,
      ],
    });
  }

  function listFixedPrice(
    tokenId: bigint,
    priceUSDC: bigint,
    recipients: {
      wallet: string;
      shareBps: number;
    }[]
  ) {
    listingWrite.writeContract({
      chainId: polygonAmoy.id,
      address: marketplaceContract.address,
      abi: marketplaceContract.abi,
      functionName: "listFixedPrice",
      args: [
        tokenId,
        priceUSDC,
        recipients,
      ],
    });
  }

  function buyAsset(listingId: bigint, account: `0x${string}`) {
  return purchaseWrite.writeContractAsync({
    account,
    chainId: polygonAmoy.id,
    address: marketplaceContract.address,
    abi: marketplaceContract.abi,
    functionName: "buyAsset",
    args: [listingId],
    gas: 500_000n,
  });
}

  return {
    approveNFT,
    nftApprovalHash: nftApproval.data,
    isNFTApprovalPending: nftApproval.isPending,
    nftApprovalError: nftApproval.error,

    listFixedPrice,
    listingHash: listingWrite.data,
    isListingPending: listingWrite.isPending,
    listingError: listingWrite.error,

    buyAsset,
    purchaseHash: purchaseWrite.data,
    isPurchasePending: purchaseWrite.isPending,
    purchaseError: purchaseWrite.error,
  };
}

/**
 * MockUSDC approval for marketplace purchases.
 */
export function useUSDCWrite() {
  const usdcApproval = useWriteContract();

  function approveMarketplace(amount: bigint, account: `0x${string}`) {
    return usdcApproval.writeContractAsync({
      account,
      chainId: polygonAmoy.id,
      address: mockUSDCContract.address,
      abi: mockUSDCContract.abi,
      functionName: "approve",
      args: [
        marketplaceContract.address,
        amount,
      ],
    });
  }

  return {
    approveMarketplace,
    hash: usdcApproval.data,
    isPending: usdcApproval.isPending,
    error: usdcApproval.error,
  };
}

export {
  marketplaceContract,
  mockUSDCContract,
};
