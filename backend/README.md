# backend

FastAPI backend. Start from this directory with `venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000`. Local `.env` supplies private configuration. PostgreSQL, configured Ollama/model cache, Pinata and Amoy RPC must be available. The master key must remain stable to decrypt saved content. Set `PINATA_GATEWAY` to your dedicated `*.mypinata.cloud` hostname; TLS verification remains enabled.

## Files

### [.env.example](.env.example)

Repository/tooling metadata controlling ignores, linting or project behavior; not user-facing application logic.

### [acceptance.py](acceptance.py)

Runs consolidated acceptance commands and records outcomes; execution can require databases/services and should use isolated test state.

### [check_demo_readiness.py](check_demo_readiness.py)

Checks configured dependencies and deployment readiness, not a substitute for interactive end-to-end purchase/download.

Main entry points: `main`.

### [check_restore.py](check_restore.py)

Database backup/restore verification helper; inspect disposable target controls before running.

Main entry points: `main`.

### [init_content_key.py](init_content_key.py)

Generates/provisions backend encryption master-key material. Output is secret and must never be pasted into this handbook.

Main entry points: `main`.

### [main.py](main.py)

FastAPI composition root: registers routers, starts database setup/workers, validates uploads, performs Pinata storage, search, access/download, recovery and provider-order endpoints. The central bridge between HTTP requests and services.

Main entry points: `duplicate_upload`, `validation_error`, `private_response_headers`, `startup`, `shutdown`, `root`, `health`, `analyze`, `upload_ipfs`, `SearchRequest`, `read_upload`, `search`, `check_asset_access`, `download_asset`, `asset_description`, `asset_details`, `LinkTokenRequest`, `recover_mint`, `link_token`, `dashboard`, `capabilities`, `account_reviews`, `latest_payment`, `activity`, `require_order_owner`, `razorpay_webhook`, `settle_payment`, `create_payment`, `get_payment`, `confirm_payment`.

### [migration_inventory.py](migration_inventory.py)

Snapshots old deployment/state for safe transition planning.

Main entry points: `main`.

### [mint_test_usdc.py](mint_test_usdc.py)

Amoy-only test MockUSDC mint CLI. Preview by default; --send signs a transaction using existing private configuration. Each send creates additional tokens.

Main entry points: `main`.

### [operator_roles.sql](operator_roles.sql)

Database role/privilege setup for operational separation.

### [payment_recovery.py](payment_recovery.py)

Operator CLI for payment reconciliation; may change financial workflow state.

Main entry points: `main`.

### [payout_recovery.py](payout_recovery.py)

Operator CLI for seller payout reconciliation.

Main entry points: `main`.

### [requirements-research.txt](requirements-research.txt)

Python dependency constraints for research simulation. Installed versions and saved benchmark versions may differ.

### [requirements.txt](requirements.txt)

Python dependency constraints for backend runtime. Installed versions and saved benchmark versions may differ.

### [sync_history.py](sync_history.py)

Backfills event history from chain with bounded/checkpointed progress.

Main entry points: `main`.

### [test_blockchain.py](test_blockchain.py)

Test or diagnostic coverage for blockchain. File presence alone does not prove that tests passed.

### [test_insert.py](test_insert.py)

Test or diagnostic coverage for insert. File presence alone does not prove that tests passed.

Main entry points: `main`.

### [test_ipfs_gateway.py](test_ipfs_gateway.py)

Tests gateway ordering, fallback behavior and rejection of non-Pinata destinations.

Main entry points: `GatewayTests`.

### [test_knowledge_asset.py](test_knowledge_asset.py)

Test or diagnostic coverage for knowledge asset. File presence alone does not prove that tests passed.

### [test_marketplace.py](test_marketplace.py)

Test or diagnostic coverage for marketplace. File presence alone does not prove that tests passed.

### [test_raw_vector.py](test_raw_vector.py)

Test or diagnostic coverage for raw vector. File presence alone does not prove that tests passed.

Main entry points: `main`.

### [test_search.py](test_search.py)

Test or diagnostic coverage for search. File presence alone does not prove that tests passed.

Main entry points: `main`.

### [test_setup.py](test_setup.py)

Test or diagnostic coverage for setup. File presence alone does not prove that tests passed.

### [verify_transak_coverage.py](verify_transak_coverage.py)

Historical staging route/quote discovery evidence capture; offers and quotes can expire.

Main entry points: `main`.

### [verify_transak_token.py](verify_transak_token.py)

Historical provider test-token chain verification, not verification of the current MockUSDC purchase.

Main entry points: `abi`, `verify`.

## Subdirectories

- [research](research/README.md)
- [services](services/README.md)
- [tests](tests/README.md)
