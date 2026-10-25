# frontend/lib/api

Part of DKM. See the root README for startup, trust boundaries and validation.

## Files

### [backend.ts](backend.ts)

Typed backend request/response helpers for upload, search, download and other app operations.

Main entry points: `analyzeAsset`, `uploadAssetToIPFS`, `searchAssets`, `checkBackendHealth`.

### [capabilities.ts](capabilities.ts)

Polling query for chain-verified market profiles and route gating.

Main entry points: `usePaymentCapabilities`, `marketRouteAvailable`.

### [client.ts](client.ts)

Shared authenticated backend request handling and normalized errors.

Main entry points: `downloadAsset`, `api`.

### [quotes.ts](quotes.ts)

Validates accepted terms against buyer, chain, token, amount, asset and listing before signing.

Main entry points: `acceptPurchaseQuote`.
