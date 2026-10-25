# contracts/scripts

Part of DKM. See the root README for startup, trust boundaries and validation.

## Files

### [New Text Document.txt](New Text Document.txt)

Auxiliary text file; inspect its actual content before treating it as an executable project entry point.

### [check-balance.ts](check-balance.ts)

Read-only native POL balance diagnostic for the configured signer; not an ERC-20 balance or faucet.

Main entry points: `main`.

### [checkAsset.ts](checkAsset.ts)

Asset contract/state inspection utility.

Main entry points: `main`.

### [checkCode.ts](checkCode.ts)

Deployment bytecode-presence diagnostic; bytecode presence alone is not full configuration validation.

Main entry points: `main`.

### [decode-error.ts](decode-error.ts)

Contract error decoding helper for revert diagnostics.

Main entry points: `main`.

### [deploy-cents.mjs](deploy-cents.mjs)

Successor/market/splitter transition script and verification journal for the live one-cent Amoy deployment. Running it is a deployment action, not a harmless diagnostic.

### [deploy-knowledge-asset.ts](deploy-knowledge-asset.ts)

Knowledge registry deployment utility; a new address does not migrate old entitlements automatically.

Main entry points: `main`.

### [deploy-trnsk-sandbox.ts](deploy-trnsk-sandbox.ts)

Historical alternative-token sandbox deployment path; does not describe the active MockUSDC market.

Main entry points: `main`, `symbol`, `decimals`, `missing`, `record`.

### [deploy.ts](deploy.ts)

Deployment entry point for the earlier contract suite; verify target network and existing-state preservation before running.

Main entry points: `main`.

### [send-op-tx.ts](send-op-tx.ts)

Operational transaction helper. Review its exact payload and signer before running; not a generic read-only command.

### [test-list-empty-royalties.ts](test-list-empty-royalties.ts)

Supporting test list empty royalties module. Its directly extracted symbols and references below identify its concrete scope.

Main entry points: `main`.

### [verify-deployment.ts](verify-deployment.ts)

Checks deployed contract configuration and wiring against expected values.

Main entry points: `main`.
