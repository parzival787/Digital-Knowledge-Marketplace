# DKM checklist — 2026-10-12

## Implemented and locally tested

- [x] Welcome/auth isolation; existing encrypted upload/mint/link/search/download/review.
- [x] Current/legacy marketplace and auctions; old licenses/refunds preserved.
- [x] Generic payment profiles and exact 6/18-decimal units.
- [x] Seller-confirmed sandbox listing/reserve prices; reference USDC stays separate.
- [x] Transak runtime methods/quotes/fees, bound BUY and independent delivery checks.
- [x] Sale-bound SELL, conflict/restart handling and provider/chain distinction.
- [x] Razorpay test-mode prefunded settlement, durable idempotency/recovery.
- [x] Audit-only registry integration, separate recorder and canonical evidence.
- [x] Adaptive persisted historical indexing; incomplete range labelled honestly.
- [x] Guarded Amoy deployment preparation, inventory and rollback procedure.
- [x] Required QAOA/VQC simulator reports retained without rerunning.

## Human approval/configuration and subsequent engineering

- [ ] Explicitly approve the three Amoy sandbox contracts; provide PUBLIC role addresses.
- [ ] Prepare final role-specific gas plan; approve/fund test POL and sandbox tokens.
- [ ] Deploy approved contracts, verify manifest, activate both current/legacy configs.
- [ ] Configure separate local settlement/recorder keys and bounded token allowance.
- [ ] Run and document S/B1/B2 wallet, provider, access, auction and audit acceptance.
- [ ] Configure Google OAuth if it must be demonstrated.
- [ ] Physically secure content-key backup and rotate any exposed external RPC key.
- [ ] Improve historical RPC only if complete lifetime history is required.
- [ ] Capture final screenshots/receipts and update completion evidence.

See HUMAN_ACTION_REQUIRED.md for exact steps. Production/mainnet/real FX,
universal crypto, hosting, independent audit and managed custody are not local
demo completion claims.
