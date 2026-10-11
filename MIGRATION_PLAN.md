# Preserve existing marketplace access

No deployment is authorized. migration_inventory.json is a block-pinned read-only
snapshot, not a deployment manifest. It found five fixed listings and no auctions;
frontend/backend legacy configurations match. Full buyer discovery is incomplete
until the event backfill finishes. Unknown mapping keys cannot be enumerated by
reading Solidity storage getters alone.

## Contracts and invariants

- Preserve KnowledgeAsset: 0x2C16409A3db9880f9A70e71B5b131A17db533Fc9.
- Current Marketplace: 0xDe7bdacb8B3ff631dbcdb09C81c0de7421475A5d.
- Current RoyaltySplitter: 0x43cE72CEd667bDe9252044451b07ecA1aec2D300.
- Current MockUSDC: 0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719.
- Currently configured legacy list: empty. Preserve old markets in both frontend
  and backend lists when switching; never erase them from entitlement checks.
- A new PaymentReceiptRegistry can coexist independently. It cannot replace
  Marketplace.hasPurchased, move funds or migrate NFT ownership.
- If funded buyAssetFor is needed, deploy a new Marketplace and a separate new
  RoyaltySplitter using the existing KnowledgeAsset/token. Do not repoint the old
  splitter away from its market while old listings/auctions still need it.

## Deployment approval package (not a request to deploy now)

ACTION REQUIRED: Later approve specific sandbox deployment transactions only.
WHY: Registry recording needs deployed code; funded settlement also needs the new
Marketplace interface. Current compiled source is not current deployed bytecode.
EXACT CONTRACTS: PaymentReceiptRegistry; optionally Marketplace + RoyaltySplitter
for funded test checkout after separate migration review.
OLD ADDRESSES: Listed above and in migration_inventory.json.
NEW CONTRACTS TO DEPLOY: Registry with sandbox=true and separate recorder/admin
addresses; new splitter/market only if the funded route is accepted.
WHAT IS PRESERVED: KnowledgeAsset, token, existing NFT owners, existing contracts,
purchase entitlements/counts, listings, auctions and refundable balances.
ROLLBACK PLAN: Disable new record/settlement workers, preserve transaction
checkpoints, restore the old active-market configuration, retain any newly used
market as legacy for its purchasers and outstanding refunds. Never delete ledger
rows or reassign the old splitter. Investigate pending signed jobs before restart.
TEST EVIDENCE: 128 contract tests on the upgraded compiler, existing backend legacy
entitlement checks and frontend old-market cancellation/auction/refund tests;
database indexer/reorg and recorder restart tests. Interactive old/new coexistence
is not yet provider/wallet verified.

## Before switch

Refresh the snapshot; finish/check historical backfill; list affected seller
cancellations and pending refunds; compare old purchase counts; record constructor
arguments, code hashes and role owners. Verify current/legacy wiring read-only.
Sellers cancel old fixed listings before intentionally relisting. Keep finalization
and refund actions targeting the original market. Pause/recovery behavior must be
checked against the actual deployed version, not assumed from new source.
