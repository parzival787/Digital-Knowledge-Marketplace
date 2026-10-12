# Human actions — TRNSK college sandbox, 2026-10-12

## ACTION REQUIRED: Approve Amoy sandbox deployment

WHY: Transak staging delivers TRNSK, while the existing market accepts MockUSDC.
Three new sandbox contracts connect real staging delivery to a DKM purchase
without replacing old contracts or granting access from provider status.

CONTRACTS TO DEPLOY:
- new TRNSK RoyaltySplitter
- new TRNSK Marketplace
- PaymentReceiptRegistry

EXISTING CONTRACTS PRESERVED: KnowledgeAsset, old Marketplace, old splitter,
MockUSDC, NFT ownership, listings, auctions, entitlements and refunds.

EXISTING ADDRESSES:
- KnowledgeAsset: 0x2C16409A3db9880f9A70e71B5b131A17db533Fc9
- Marketplace: 0xDe7bdacb8B3ff631dbcdb09C81c0de7421475A5d
- RoyaltySplitter: 0x43cE72CEd667bDe9252044451b07ecA1aec2D300
- MockUSDC: 0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719

TRNSK VERIFIED ADDRESS: 0x0c86A754A29714C4Fe9C6F1359fa7099eD174c0b
TRNSK VERIFIED DECIMALS: 18

PUBLIC ADDRESSES YOU NEED FROM ME:
- treasury
- deployer/admin
- settlement signer
- recorder

Admin, settlement and recorder must be different wallets. Use dedicated test
accounts; share only their public 0x addresses. Treasury receives the existing
5% seller deduction. There is no new 5% buyer fee.

TEST POL NEEDED: Deployer for three deployments plus new-splitter wiring; S/B1/B2
for mint/list/approve/buy/bid/refund/finalize; settlement and recorder for their
transactions. Exact amount requires public addresses and a fresh RPC gas estimate.
Do not buy real POL or treat a guessed amount as a guaranteed gas quote.

TRNSK NEEDED: B1's reviewed listing amount via Transak staging, B1/B2 auction
amounts, and settlement signer's intended Razorpay-demo listing total. Settlement
allowance must be bounded to approved demo purchases. Deployment itself does not
require spending TRNSK. Seller receives sale proceeds for the optional SELL route.

AUTOMATED TEST RESULTS: 82 backend, 15 frontend, frontend production build,
129 contract tests and contract typecheck passed. The included canonical
seller/proceeds test passed. Wrong-chain deployment guard passed without a journal.
These are automated tests, not hosted provider or signed-wallet E2E evidence.

MIGRATION INVENTORY: migration_inventory.json, block 49969644, five fixed listings,
zero auctions, configuration aligned. Full historical buyer discovery remains
incomplete; known entitlements and direct access checks are preserved.

ROLLBACK PLAN: Disable workers, retain signed checkpoints/ledger/manifest, restore
old current-market configuration, keep any used new market in both legacy lists.
Never delete access history or repoint the old splitter. See MIGRATION_PLAN.md.

WHAT I MUST NOT SHARE: Seed phrases, private keys, API secrets, passwords, OTPs,
full credential-bearing RPC URLs, real bank/card/KYC data.

WHERE: Reply in this chat; optionally fill sandbox-deployment-addresses.json locally
using the public-address example.
WHAT I NEED TO DO: Read the package and explicitly approve these three Amoy
sandbox contracts, then supply the four public role addresses.
EXPECTED RESULT: Codex verifies the exact plan, estimates gas and performs only
approved testnet transactions. No merge, hosting or mainnet deployment.
WHAT TO SEND BACK: “I approve the three Amoy sandbox contracts” and public addresses,
or the specific change you want. Typing “continue” alone is not deployment approval.

## Later: test-wallet funding and local signer setup

ACTION REQUIRED: Fund approved test accounts and save signer keys locally.
WHY: Settlement/recording keys are currently absent; workers remain disabled.
WHERE: MetaMask on chain 80002 and ignored backend/.env.
WHAT I NEED TO DO: After addresses/contracts are verified, add Amoy test POL to
admin, S/B1/B2, settlement and recorder as needed; acquire sandbox TRNSK for buyer/
settlement tests and approve only the bounded amount to the verified new market.
Save SETTLEMENT_PRIVATE_KEY and RECEIPT_RECORDER_PRIVATE_KEY only in ignored local
configuration, using the distinct approved wallets. Codex can validate addresses
without printing keys. Do not enable workers until deployment/funding checks pass.
WHAT I MUST NOT SHARE: Any private key, seed phrase or secret configuration.
EXPECTED RESULT: Funded, separated sandbox signers and bounded allowance.
WHAT TO SEND BACK: “Saved/funded locally” and public transaction hashes.

## Later: hosted checkout and signed acceptance

ACTION REQUIRED: Follow DEMO_RUNBOOK.md with S, B1 and B2.
WHY: Hosted provider eligibility and wallet signatures cannot be established by
unit tests. Current lookup offered USD/EUR cards, not INR/UPI.
WHERE: localhost:3000, MetaMask and Transak staging.
WHAT I NEED TO DO: Perform supported BUY, separate TRNSK purchase, access/review,
sale-bound SELL if offered, two-bidder refund/finalization, optional configured
Razorpay test settlement, registry and legacy checks. Capture sanitized evidence.
WHAT I MUST NOT SHARE: Real financial details, KYC, keys, passwords or OTPs.
EXPECTED RESULT: Actual canonical testnet transactions and correct access/accounting.
WHAT TO SEND BACK: Step, PASS/FAIL, account label, asset ID and public tx hash.

## Google, backup and optional historical RPC

ACTION REQUIRED: Configure Google if required, secure the existing content key,
and replace any previously exposed RPC credential.
WHY: Google credentials are absent; key custody/rotation needs your external account.
WHERE: Google Cloud OAuth Web Application, private backup and ignored backend/.env.
WHAT I NEED TO DO: Set Google callback http://localhost:8000/api/auth/google/callback;
save GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI locally and allow
demo test users. Securely back up the EXISTING CONTENT_MASTER_KEY; do not overwrite
it. Save a replacement RPC locally and validate before revoking the old credential.
Only obtain a historical Amoy RPC if your rubric requires full lifetime history;
current access does not depend on full backfill.
WHAT I MUST NOT SHARE: Secret values or full RPC URLs.
EXPECTED RESULT: Google login can be tested and encryption remains recoverable.
WHAT TO SEND BACK: “Configured/backed up locally” or a sanitized error.

No extra on-ramp signup is required for this plan. Production KYB/mainnet/real
currency conversion, universal cryptocurrency support, public hosting and
independent production audit are outside the local sandbox completion claim.
