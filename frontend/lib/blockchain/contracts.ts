import KnowledgeAssetArtifact from "@/contracts/abi/KnowledgeAsset.json";
import MarketplaceArtifact from "@/contracts/abi/Marketplace.json";
import RoyaltySplitterArtifact from "@/contracts/abi/RoyaltySplitter.json";
import MockUSDCArtifact from "@/contracts/abi/MockERC20.json";

import { CONTRACTS } from "@/contracts/addresses";

export const knowledgeAssetContract = {
  address: CONTRACTS.KnowledgeAsset,
  abi: KnowledgeAssetArtifact.abi,
} as const;

export const marketplaceContract = {
  address: CONTRACTS.Marketplace,
  abi: MarketplaceArtifact.abi,
} as const;

export const royaltySplitterContract = {
  address: CONTRACTS.RoyaltySplitter,
  abi: RoyaltySplitterArtifact.abi,
} as const;

export const mockUSDCContract = {
  address: CONTRACTS.MockUSDC,
  abi: MockUSDCArtifact.abi,
} as const;
