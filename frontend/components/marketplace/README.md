# frontend/components/marketplace

Part of DKM. See the root README for startup, trust boundaries and validation.

## Files

### [AccountActivity.tsx](AccountActivity.tsx)

Sanitized account history display.

Main entry points: `AccountActivity`, `load`.

### [AssetCard.tsx](AssetCard.tsx)

Main asset interface: listing/cancel, quotes, token balance/allowance checks, purchase, access and download controls.

Main entry points: `licenseName`, `formatUSDC`, `AssetCard`, `handleViewDetails`, `handleApprove`, `handleList`, `handleBuy`.

### [AssetFunding.tsx](AssetFunding.tsx)

Supporting AssetFunding module. Its directly extracted symbols and references below identify its concrete scope.

Main entry points: `AssetFunding`, `run`.

### [AuctionPanel.tsx](AuctionPanel.tsx)

Auction creation, bids, finalization and refund interactions with matching market/token.

Main entry points: `AuctionPanel`, `transact`, `send`.

### [BlockchainTest.tsx](BlockchainTest.tsx)

Development chain connection diagnostic component.

Main entry points: `BlockchainTest`.

### [IndexedActivity.tsx](IndexedActivity.tsx)

Indexed blockchain activity with coverage limitations.

Main entry points: `IndexedActivity`, `refresh`.

### [LegacyListing.tsx](LegacyListing.tsx)

Operations for previous-market positions, maintaining original contract identity.

Main entry points: `LegacyListing`, `cancel`.

### [PaymentCapabilities.tsx](PaymentCapabilities.tsx)

Displays verified route availability and prevents unsupported payment promises.

Main entry points: `PaymentCapabilities`.

### [PayoutHistory.tsx](PayoutHistory.tsx)

Supporting PayoutHistory module. Its directly extracted symbols and references below identify its concrete scope.

Main entry points: `PayoutHistory`, `load`, `refresh`.

### [Positions.tsx](Positions.tsx)

Wallet-specific positions and actions based on backend/on-chain reads.

Main entry points: `Positions`.

### [PurchaseQuoteSummary.tsx](PurchaseQuoteSummary.tsx)

Displays purchase total and seller deductions; keeps conversion/funding separate from asset purchase.

Main entry points: `PurchaseQuoteSummary`.

### [RecordingHistory.tsx](RecordingHistory.tsx)

Supporting RecordingHistory module. Its directly extracted symbols and references below identify its concrete scope.

Main entry points: `RecordingHistory`.

### [ReviewHistory.tsx](ReviewHistory.tsx)

Account review history display.

Main entry points: `ReviewHistory`.

### [Reviews.tsx](Reviews.tsx)

Read/write review interface with backend entitlement enforcement.

Main entry points: `Reviews`.

### [SalePayout.tsx](SalePayout.tsx)

Supporting SalePayout module. Its directly extracted symbols and references below identify its concrete scope.

Main entry points: `SalePayout`, `act`.

### [SellerPayout.tsx](SellerPayout.tsx)

Supporting SellerPayout module. Its directly extracted symbols and references below identify its concrete scope.

Main entry points: `SellerPayout`, `save`.

### [TransakFunding.tsx](TransakFunding.tsx)

Supporting TransakFunding module. Its directly extracted symbols and references below identify its concrete scope.

Main entry points: `TransakFunding`, `start`.

### [TransakOrders.tsx](TransakOrders.tsx)

Supporting TransakOrders module. Its directly extracted symbols and references below identify its concrete scope.

Main entry points: `TransakOrders`, `load`, `refresh`.

### [Web2Checkout.tsx](Web2Checkout.tsx)

Supporting Web2Checkout module. Its directly extracted symbols and references below identify its concrete scope.

Main entry points: `Window`, `request`, `Web2Checkout`, `checkout`, `refresh`.
