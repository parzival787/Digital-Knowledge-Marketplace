# frontend/lib/blockchain

Part of DKM. See the root README for startup, trust boundaries and validation.

## Files

### [amoyFees.ts](amoyFees.ts)

Checks chain ID and computes EIP-1559 fee bounds with the observed 25-gwei priority floor.

Main entry points: `amoyFees`.

### [auctionDuration.ts](auctionDuration.ts)

Converts whole minutes/hours into seconds and enforces the inclusive 2-minute to 720-hour duration range.

Main entry points: `auctionDurationSeconds`.

### [contracts.ts](contracts.ts)

Typed contract address/ABI bindings for wallet/RPC operations.

### [paymentToken.ts](paymentToken.ts)

Verified market token binding, decimal formatting and exact unit parsing.

Main entry points: `paymentToken`, `formatTokenAmount`, `paymentAmount`.

### [purchaseSafety.ts](purchaseSafety.ts)

Shared listing/ownership/entitlement, receipt and gas preflight protections reused across wallet writes.

Main entry points: `PurchaseCheckError`, `checkUnlisted`, `checkListing`, `checkGas`, `confirmedReceipt`.

### [useKnowledgeAssets.ts](useKnowledgeAssets.ts)

Registry read hooks for asset metadata, ownership and totals on Amoy.

Main entry points: `useTotalMinted`, `useKnowledgeAsset`, `useAssetOwner`, `useIsListed`, `useApproveMarketplace`, `useListFixedPrice`.

### [useMarketplace.ts](useMarketplace.ts)

React hooks for market reads/writes and token approval; callers still need fresh state and receipt verification.

Main entry points: `useIsListed`, `useTokenToListing`, `useListing`, `useMarketplaceWrite`, `approveNFT`, `listFixedPrice`, `buyAsset`, `useUSDCWrite`, `approveMarketplace`.

### [wagmi.ts](wagmi.ts)

Wallet connector and supported-chain configuration.
