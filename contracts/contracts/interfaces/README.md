# contracts/contracts/interfaces

Part of DKM. See the root README for startup, trust boundaries and validation.

## Files

### [IKnowledgeAsset.sol](IKnowledgeAsset.sol)

Solidity interface defining the cross-contract callable surface and shared types; implementation lives in the corresponding contract.

Main entry points: `IKnowledgeAsset`, `mint`, `getAsset`, `ownerOf`, `getApproved`, `isApprovedForAll`, `safeTransferFrom`, `updatePrice`, `deactivate`, `totalMinted`.

### [IMarketplace.sol](IMarketplace.sol)

Solidity interface defining the cross-contract callable surface and shared types; implementation lives in the corresponding contract.

Main entry points: `IMarketplace`, `listAsset`, `purchaseAsset`, `cancelListing`.

### [IRoyaltySplitter.sol](IRoyaltySplitter.sol)

Solidity interface defining the cross-contract callable surface and shared types; implementation lives in the corresponding contract.

Main entry points: `IRoyaltySplitter`, `calculatePlatformFee`, `calculateRoyaltyPool`, `distributeRoyalty`, `updatePlatformFee`, `updateTreasury`, `updateMarketplace`, `treasury`, `platformFeeBps`, `marketplace`.
