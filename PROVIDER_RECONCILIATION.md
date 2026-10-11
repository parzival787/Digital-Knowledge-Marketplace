# Transak saved-order reconciliation

Implemented 2026-10-11 for the existing BUY sandbox history. This polls the
authenticated provider API; it never creates a payment, spends funds or grants
Marketplace entitlement. Funding, purchase and payout remain distinct.

When staging configuration is valid, the backend checks a maximum of five due
saved orders per minute. Each order is scheduled at least five minutes apart.
PostgreSQL row claims (SKIP LOCKED) prevent duplicate multi-worker batches;
the existing shared-token lock serializes provider authentication and verification.
Claims survive a restart and become due again after the delay. Failures preserve
the previous receipt and expose only a generic refresh error.

Completed -> refunded is allowed. A terminal-to-earlier state, late completion
after failed/cancelled/expired, or changed completed financial evidence enters
review_required without replacing original evidence. Conflicts remain held and
are excluded from automatic polling. Manual refresh can gather the latest observed
status but does not clear review. A reviewed resolution/audit workflow is still
needed before such evidence could be used by a future settlement/recording adapter.

Users still enter the provider order ID initially. Polling covers only saved BUY
orders, not automatic discovery, verified SELL payouts or bank verification.
Account-wallet matching is required for polling. It does not follow a browser
redirect or accept a browser status as payment proof.

Set TRANSAK_RECONCILIATION_ENABLED=false to disable this read-only worker.
The frontend shows last successful verification and refresh/conflict messages.
No provider webhook was registered and no public endpoint was exposed.

Official references checked 2026-10-11:
- https://docs.transak.com/guides/track-order-status
- https://docs.transak.com/features/webhooks
- https://docs.transak.com/api/public/get-order-by-order-id

Transak documents public HTTPS and provider registration for webhooks. Its
walletAddress parameter is BUY-only; safe SELL ownership cannot be inferred by
reusing the BUY wallet match. SELL tracking needs a verified session/order binding
and payout schema before claiming that a particular DKM seller was paid.
