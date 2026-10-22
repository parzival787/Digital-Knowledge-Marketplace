"use client";

import {
  useAccount,
  usePublicClient,
  useReadContract,
  useWriteContract,
} from "wagmi";
import { checkGas } from "@/lib/blockchain/purchaseSafety";
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
  const client = usePublicClient({ chainId: polygonAmoy.id });
  const { address: account } = useAccount();
  const nftApproval = useWriteContract();
  const listingWrite = useWriteContract();
  const purchaseWrite = useWriteContract();

  async function approveNFT(tokenId: bigint) {
    if (!client || !account) throw new Error("Connect your Amoy wallet first.");
    const fees = await checkGas(client, knowledgeAssetContract, "approve", [marketplaceContract.address, tokenId], account);
    return nftApproval.writeContractAsync({
      ...fees, account,
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

  async function listFixedPrice(
    tokenId: bigint,
    priceUSDC: bigint,
    recipients: {
      wallet: string;
      shareBps: number;
    }[]
  ) {
    if (!client || !account) throw new Error("Connect your Amoy wallet first.");
    const fees = await checkGas(client, marketplaceContract, "listFixedPrice", [tokenId, priceUSDC, recipients], account);
    return listingWrite.writeContractAsync({
      ...fees, account,
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

  async function buyAsset(listingId: bigint, account: `0x${string}`) {
  if (!client) throw new Error("Connect your Amoy wallet first.");
  const fees = await checkGas(client, marketplaceContract, "buyAsset", [listingId], account);
  return purchaseWrite.writeContractAsync({
    ...fees,
    account,
    chainId: polygonAmoy.id,
    address: marketplaceContract.address,
    abi: marketplaceContract.abi,
    functionName: "buyAsset",
    args: [listingId],
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
export function useUSDCWrite(tokenAddress: `0x${string}`) {
  const client = usePublicClient({ chainId: polygonAmoy.id });
  const usdcApproval = useWriteContract();

  async function approveMarketplace(amount: bigint, account: `0x${string}`) {
    if (!client) throw new Error("Connect your Amoy wallet first.");
    const fees = await checkGas(client, { address: tokenAddress, abi: mockUSDCContract.abi }, "approve", [marketplaceContract.address, amount], account);
    return usdcApproval.writeContractAsync({
      ...fees,
      account,
      chainId: polygonAmoy.id,
      address: tokenAddress,
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
