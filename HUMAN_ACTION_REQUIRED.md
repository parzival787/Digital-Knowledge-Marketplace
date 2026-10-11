# Human actions for the local college demonstration

Updated 2026-10-11. Engineering continues independently. Do not paste secrets.
No additional payment-provider signup or public hosting is required now.

## College scope (QAOA/VQC requirement resolved)

QAOA pricing and VQC embeddings are mandatory core components, confirmed by the
owner on 2026-10-11. No further approval or reconfirmation is needed to implement
and evaluate them. Their engineering work belongs to Codex, not the owner.

ACTION REQUIRED: Send the submission deadline if it has not already been supplied.
WHY: Schedule the final human acceptance session; engineering continues meanwhile.
WHERE TO DO IT: Reply in this chat with the college requirements.
WHAT TO ENTER/CLICK: Provide the deadline and any additional rubric text not
already present in the repository/handout. Do not reconfirm QAOA/VQC.
WHAT NOT TO SHARE: Personal student records or private credentials.
WHAT RESULT TO SEND BACK: Required feature list and deadline.

## Interactive acceptance (after engineering readiness)

ACTION REQUIRED: Prepare seller and two bidder/buyer accounts and wallets.
WHY: The final auction requires two independent bidders and human signatures.
WHERE TO DO IT: DKM Account pages in separate browser profiles and MetaMask.
WHAT TO ENTER/CLICK: Verify wallets; confirm Amoy chain 80002 for the existing
deployment. Follow the final demo runbook when ready; test assets only.
WHAT NOT TO SHARE: Seed phrases, private keys, passwords or OTPs.
WHAT RESULT TO SEND BACK: Public wallet labels/addresses and acceptance outcomes.
Signing or spending test funds remains a human action; no automatic spending.

## Transak sandbox acceptance

ACTION REQUIRED: Complete documented hosted sandbox steps when the runbook is ready.
WHY: BUY/SELL session creation was verified; completed checkout/payout was not.
WHERE TO DO IT: DKM Funding / Account and the Transak staging widget.
WHAT TO ENTER/CLICK: Use official sandbox details only; keep partner fee zero;
enable SELL in the provider portal if required. Report absent UPI support.
WHAT NOT TO SHARE: Real card/bank/KYC data, API secrets or OTPs.
WHAT RESULT TO SEND BACK: Safe test order reference, selected route and outcome.
Transak TRNSK funding never purchases a DKM asset or grants access.

## Google OAuth configuration

ACTION REQUIRED: Configure the existing Google implementation if needed for demo.
WHY: Code exists; external OAuth configuration and interaction are human-only.
WHERE TO DO IT: Google Cloud OAuth Web Application and ignored backend/.env.
WHAT TO ENTER/CLICK: Callback http://localhost:8000/api/auth/google/callback;
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI; allowed test users;
FRONTEND_ORIGIN=http://localhost:3000. Tell me when locally saved.
WHAT NOT TO SHARE: Client secret, login password, tokens.
WHAT RESULT TO SEND BACK: Configuration ready or a non-secret setup error.

## Key custody and RPC rotation

ACTION REQUIRED: Keep a secure backup of the existing CONTENT_MASTER_KEY; create
a replacement RPC credential in the provider dashboard if rotation remains pending.
WHY: Encrypted content depends on that key; an earlier diagnostic exposed an RPC
credential. Engineering must validate the replacement before the old one is revoked.
WHERE TO DO IT: Private password manager/offline backup and RPC provider dashboard.
WHAT TO ENTER/CLICK: Save replacement locally without printing it; do not overwrite
the content master key. Notify me for read-only RPC validation before revocation.
WHAT NOT TO SHARE: Keys, credential URLs, database backups containing personal data.
WHAT RESULT TO SEND BACK: Backup secured and replacement RPC saved locally.

## Later deployment approval / optional embedded wallet

BLOCKED - HUMAN/EXTERNAL ACTION REQUIRED: No contract deployment is approved.
A concrete plan, migration impact, rollback and test evidence must come first.
Only then approve the specified deployment and test-gas spending, if desired.
KnowledgeAsset stays unchanged. Registry records remain audit-only.

Privy setup is deferred unless the rubric requires walletless users. If required,
create a development app, allow localhost and supply only the public app ID.
No paid plan, production KYB, mainnet or domain/DNS work is requested for this demo.
