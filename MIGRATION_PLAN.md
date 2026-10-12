# TRNSK sandbox migration — 2026-10-12

No public deployment or application switch has been authorized or performed.
New marketplace: TRNSK, 18 decimals. Existing marketplace: original MockUSDC
contract (on-chain symbol USDC), 6 decimals. Units must never be mixed.

## Preserved contracts

| Contract | Amoy address |
|---|---|
| KnowledgeAsset | 0x2C16409A3db9880f9A70e71B5b131A17db533Fc9 |
| Existing Marketplace | 0xDe7bdacb8B3ff631dbcdb09C81c0de7421475A5d |
| Existing RoyaltySplitter | 0x43cE72CEd667bDe9252044451b07ecA1aec2D300 |
| Existing MockUSDC | 0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719 |
| Verified TRNSK | 0x0c86A754A29714C4Fe9C6F1359fa7099eD174c0b |

migration_inventory.json is a read-only snapshot at block 49969644: five listings,
zero auctions, matching frontend/backend configuration, code hashes and known
wallet entitlements. All historical buyers are not yet discoverable because log
backfill is incomplete; direct hasPurchased remains authoritative.
Refresh this inventory immediately before activation.

## Deployment preparation

Copy sandbox-deployment-addresses.example.json to sandbox-deployment-addresses.json
and enter approved PUBLIC addresses. Admin, settlement and recorder must differ.
From contracts, run:
`node_modules/.bin/hardhat.cmd run scripts/deploy-trnsk-sandbox.ts --network polygonAmoy`

Default execution verifies chain 80002, existing code/wiring and TRNSK metadata,
then writes trnsk-deployment-plan.json without signing. Only AFTER explicit human
approval may DKM_APPROVED_AMOY_DEPLOYMENT=true enable the deployment sequence:

1. RoyaltySplitter(TRNSK, approved treasury, 500).
2. Marketplace(existing KnowledgeAsset, new splitter, TRNSK).
3. updateMarketplace(new market) on the NEW splitter only.
4. PaymentReceiptRegistry(dedicated recorder, true).

trnsk-deployment-manifest.json journals broadcasts, addresses, code hashes and
post-deployment role/wiring checks. An existing journal blocks automatic retry.
For partial deployment, inspect recorded receipts and recover; never delete it
to blindly deploy again. Script execution does not activate application addresses.

## Activation after approval

Disable settlement/recording workers; reconcile pending signed transactions.
Keep old persisted orders in their original denomination and market. Do not
redirect pending orders to the new market or reinterpret their prices.
Set the new current market in both frontend/backend, add the original market to
BOTH legacy lists, configure new splitter/token/registry and copy ABI only from
the exact approved compiled source. Re-run acceptance and deployed wiring checks.

KnowledgeAsset.priceUSDC remains a 6-decimal reference. Sellers confirm TRNSK
listing/reserve prices explicitly. Cancel old listings on the original market
before relisting; the UI checks all markets. This is not an atomic cross-contract
reservation. Old auctions/refunds/access continue targeting their original market.

## Rollback

Disable new workers; preserve signed checkpoints. Restore original active-market
configuration. Retain any used new market in both legacy lists so its licenses
and refunds survive. Never delete ledgers, entitlements or the manifest, or
repoint the old splitter. Provider funding is not reversed by a config rollback.
