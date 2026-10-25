# backend/services/payments

Retained payment/provider workflow implementations. Current frontend payments use wallet transactions. Provider confirmation, token funding and receipt recording are separate from blockchain purchase entitlement. Mock providers must never spend tokens or grant access. Optional workers require explicit configuration.

## Files

### [asset_funding.py](asset_funding.py)

Binds funding intent to asset/market/token context; funding alone must not grant access.

Main entry points: `setup_funding`, `nominal`, `public`, `FundingRequest`, `funding_quote`, `funding_session`, `reconcile_funding`, `create`, `session`, `history`.

### [capabilities.py](capabilities.py)

Reads deployed market/token wiring and reports route availability. Fails closed when chain/profile verification is unavailable.

Main entry points: `chain_routes`, `payment_capabilities`.

### [market_profiles.py](market_profiles.py)

Reads token symbol/decimals and market wiring from deployed contracts rather than assuming every token called USDC is identical.

Main entry points: `parse_units`, `market_profile`.

### [mock_provider.py](mock_provider.py)

Non-spending payment simulator for tests. Its confirmation must not become blockchain entitlement. Distinct from the real on-testnet MockERC20 contract.

Main entry points: `MockPaymentProvider`.

### [models.py](models.py)

Typed payment methods, statuses and request/order models. Defines the vocabulary used by persistence and provider state transitions.

Main entry points: `PaymentStatus`, `PaymentMethod`, `CreatePaymentRequest`, `PaymentOrder`, `ConfirmPaymentRequest`.

### [payouts.py](payouts.py)

Retained seller payout preferences and order tracking; preferences do not themselves perform conversion or bank payment.

Main entry points: `setup_payouts`, `digest`, `create_payout`, `verified_sell`, `refresh_payout`, `resolve_payout`, `reconcile_payouts`, `PayoutLookup`, `refresh`, `history`.

### [provider.py](provider.py)

Provider interface separating external payment operations from order orchestration.

Main entry points: `PaymentProvider`.

### [quotes.py](quotes.py)

Builds purchase terms and validates buyer, market, token, amount and expiry. A quote is not an asset reservation or a payment receipt.

Main entry points: `setup_quotes`, `accounting`, `purchase_terms`, `public_quote`, `create_quote`, `accept_quote`, `create`, `accept`.

### [razorpay_provider.py](razorpay_provider.py)

Retained Razorpay test-mode creation/signature/status integration. Razorpay collection itself is not INR-to-USDC conversion.

Main entry points: `RazorpayProvider`.

### [receipt_registry_abi.json](receipt_registry_abi.json)

Contract ABI/interface data used to encode calls and decode outputs/events. An ABI is not a deployment or evidence of a successful transaction.

### [recording.py](recording.py)

Optional blockchain receipt recorder workflow with durable transaction management. Receipt logging is not a source of NFT access entitlement.

Main entry points: `setup_recording`, `canonical`, `commitment`, `payment_tuple`, `payment_hash`, `enqueue_verified`, `enqueue_reversal`, `connection`, `call_for`, `prepare`, `validate_source`, `verify_or_broadcast`, `record_job`, `recording_worker`, `history`.

### [recording_sources.py](recording_sources.py)

Validates external/provider/chain source evidence before an optional recording job may assert a receipt.

Main entry points: `queue_indexed_sales`, `verify_saved_capture`, `saved_payment`, `queue_verified_refunds`.

### [recovery.py](recovery.py)

Operator reconciliation helpers for unsettled/captured orders, retries and refund-related state; execution can have external effects.

Main entry points: `require_refundable`, `verify_refund`, `recover`.

### [sale_payouts.py](sale_payouts.py)

Binds payout eligibility to verified canonical sales, correct seller, token and positive proceeds.

Main entry points: `SaleQuote`, `verified_sale`, `create_quote`, `open_session`, `outgoing_delivery`, `create`, `session`.

### [service.py](service.py)

Persists and transitions payment orders and coordinates providers; retains idempotency and confirmation/settlement separation.

Main entry points: `PaymentService`.

### [settlement.py](settlement.py)

Verifies configured chain/contract and performs controlled funded on-chain settlement, with receipt/state verification. A prefunded treasury is not currency exchange.

Main entry points: `function_abi`, `order_amount`, `verify_denomination`, `connection`, `validate_checkout`, `prepare`, `confirmed_receipt`, `broadcast_and_verify`, `has_entitlement`, `settle_order`, `reconcile_payments`, `settlement_worker`.

### [token_delivery.py](token_delivery.py)

Checks actual canonical token delivery evidence separately from provider completion status.

Main entry points: `verify_delivery`.

### [transak.py](transak.py)

Retained Transak staging order/session verification and durable workflow code. Not the current wallet-only UI payment route.

Main entry points: `setup_transak`, `configuration`, `provider_json`, `access_token`, `create_session`, `status`, `session`, `OrderLookup`, `verified_order`, `normalized_order`, `reconcile_receipt`, `refresh_order`, `check_order`, `orders`, `reconcile_saved_orders`, `reconciliation_worker`, `PayoutPreference`, `payout_preference`, `save_payout_preference`, `payout_session`.

### [transak_discovery.py](transak_discovery.py)

Retained provider discovery and quote coverage lookup. Returned methods depend on the provider; no universal currency support is implied.

Main entry points: `text`, `amount`, `lookup`, `discover`, `crypto_coverage`, `quote`, `coverage`.
