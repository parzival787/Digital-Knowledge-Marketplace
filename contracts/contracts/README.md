# contracts/contracts

Part of DKM. See the root README for startup, trust boundaries and validation.

## Files

### [KnowledgeAsset.sol](KnowledgeAsset.sol)

ERC-721 knowledge registration: content/metadata CIDs, creator, price, license, quality and active status. Minting registers content; it is not an asset purchase.

Main entry points: `KnowledgeAsset`, `mint`, `getAsset`, `updatePrice`, `deactivate`, `_beforeTokenTransfer`, `totalMinted`, `tokenURI`.

### [KnowledgeAssetSuccessor.sol](KnowledgeAssetSuccessor.sol)

Successor registry reads the fixed original prefix 1-6 and creates new tokens from 7 onward. Preserves original NFTs without copying their ownership.

Main entry points: `addresses`, `KnowledgeAssetSuccessor`, `_ownerOf`, `balanceOf`, `getAsset`, `tokenURI`.

### [Marketplace.sol](Marketplace.sol)

Fixed-price listings, entitlement purchases, funded purchases, auctions, bids, finalization and refunds. Payment token is immutable; buyAsset transfers ERC-20 tokens and grants access, not NFT ownership.

Main entry points: `Marketplace`, `hasPurchased`, `listFixedPrice`, `cancelListing`, `buyAsset`, `buyAssetFor`, `_buyAsset`, `createAuction`, `placeBid`, `withdrawRefund`, `endAuction`, `pause`, `unpause`, `updateRoyaltySplitter`, `isListed`, `listingExists`, `isAuctionActive`, `auctionExists`, `getAuctionBids`, `getListingRecipients`, `getAuctionRecipients`, `totalListingsCreated`, `totalAuctionsCreated`.

### [MockERC20.sol](MockERC20.sol)

Test ERC-20 with configured decimals and externally callable mint. Creates test currency; never treat its unrestricted issuance as a production stablecoin.

Main entry points: `MockERC20`, `mint`, `decimals`.

### [PaymentReceiptRegistry.sol](PaymentReceiptRegistry.sol)

Optional restricted receipt-recording contract. Records evidence identifiers without replacing marketplace entitlement rules.

Main entry points: `PaymentReceiptRegistry`, `recordPayment`, `recordReversal`.

### [RoyaltySplitter.sol](RoyaltySplitter.sol)

Restricted marketplace caller distributes token proceeds to treasury, royalty recipients and seller with validated basis-point limits.

Main entry points: `RoyaltySplitter`, `must`, `happened`, `calculatePlatformFee`, `calculateRoyaltyPool`, `updateTreasury`, `updatePlatformFee`, `updateMarketplace`, `_validateRecipients`, `before`, `distributeRoyalty`.

## Subdirectories

- [interfaces](interfaces/README.md)
