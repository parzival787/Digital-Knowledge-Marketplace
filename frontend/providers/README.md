# frontend/providers

Part of DKM. See the root README for startup, trust boundaries and validation.

## Files

### [AuthProvider.tsx](AuthProvider.tsx)

Shared account/session state and authentication actions.

Main entry points: `AuthProvider`, `logout`, `useVerifiedWallet`, `AccountGate`.

### [Web3Provider.tsx](Web3Provider.tsx)

Wagmi/RainbowKit/query providers for wallet and chain interactions.

Main entry points: `Web3Provider`.
