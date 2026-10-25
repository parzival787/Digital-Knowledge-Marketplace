# backend/services

Part of DKM. See the root README for startup, trust boundaries and validation.

## Files

### [__init__.py](__init__.py)

Python package initializer; may be intentionally empty.

### [activity.py](activity.py)

Builds sanitized account activity from available persisted/indexed records. Incomplete indexing cannot establish complete lifetime history.

Main entry points: `account_activity`.

### [asset_price.py](asset_price.py)

Validates exact decimal asset prices and rejects invalid precision/range instead of relying on binary floating-point money calculations.

Main entry points: `asset_price`.

### [auth.py](auth.py)

Password accounts with scrypt, hashed revocable cookie sessions, exact-origin checks, rate limiting, Google OAuth plumbing and signed wallet challenges. Account identity and wallet identity are separate until proof is verified.

Main entry points: `setup_auth`, `digest`, `password_hash`, `hash_password`, `same_origin`, `current_user`, `wallet_user`, `Credentials`, `throttle`, `new_session`, `signup`, `login`, `google_config`, `methods`, `google_start`, `google_callback`, `me`, `logout`, `WalletProof`, `wallet_challenge`, `verify_wallet`.

### [blockchain.py](blockchain.py)

RPC contract reads and current/legacy registry and entitlement lookup. Keeps legacy access bounded to the preserved token prefix.

Main entry points: `check_blockchain_connection`, `entitlement_markets`, `has_purchased`, `get_purchase_count`, `get_knowledge_asset`, `legacy_registry_address`, `market_token_supported`.

### [chain_event_abis.json](chain_event_abis.json)

Contract ABI/interface data used to encode calls and decode outputs/events. An ABI is not a deployment or evidence of a successful transaction.

### [content_security.py](content_security.py)

AES-256-GCM envelope encryption and decryption. Uses independent random nonces for document encryption and key wrapping, with the plaintext digest as associated authenticated data.

Main entry points: `master_key`, `seal`, `unseal`.

### [embedding.py](embedding.py)

Lazy local-cache loading of all-MiniLM-L6-v2; produces normalized 384-dimensional summary/query vectors. It does not call Ollama to produce embeddings.

Main entry points: `get_model`, `generate_embedding`, `embed_query`.

### [event_indexer.py](event_indexer.py)

Persists chain-event sources, checkpoints and derived activity. Handles idempotency and chain consistency; source availability and backlog determine coverage.

Main entry points: `setup_indexer`, `first_code_block`, `normalized`, `sale_accounting`, `fetch_page`, `sync_market`, `rebuild_market`, `index_worker`, `history`.

### [fraud_detector.py](fraud_detector.py)

Checks persisted BLAKE3 duplicates and files smaller than 100 bytes. Despite its class name, this is a classical rule-based screen, not learned fraud or plagiarism detection.

Main entry points: `QuantumFraudDetector`.

### [ipfs_gateway.py](ipfs_gateway.py)

Validates the optional dedicated Pinata hostname and prioritizes it for protected content and metadata retrieval; retains public fallback gateways.

Main entry points: `ipfs_gateways`.

### [knowledge_asset_abi.py](knowledge_asset_abi.py)

Contract ABI/interface data used to encode calls and decode outputs/events. An ABI is not a deployment or evidence of a successful transaction.

### [llm_enrichment.py](llm_enrichment.py)

Calls Ollama through the OpenAI-compatible client, validates structured metadata and four evidence-backed criteria, then computes quality on the server. Rejects fabricated or malformed support rather than manufacturing a fallback score.

Main entry points: `AnalysisUnavailable`, `validate_metadata`, `enrich_document`.

### [marketplace_abi.py](marketplace_abi.py)

Contract ABI/interface data used to encode calls and decode outputs/events. An ABI is not a deployment or evidence of a successful transaction.

### [mint_recovery.py](mint_recovery.py)

Finds already minted registrations for a saved upload and prevents an immediate blind retry when completion can be recovered. Uses creator/content matching and bounded scanning.

Main entry points: `find_mint`.

### [pgvector_client.py](pgvector_client.py)

PostgreSQL schema setup, compatible column migrations, asset persistence, duplicate protection, vector decoding and cosine candidate queries. Owns the knowledge_assets catalog and initial payment/review tables.

Main entry points: `DuplicateUploadError`, `get_conn`, `setup_tables`, `insert_embedding`, `semantic_search`, `update_token_id`, `get_asset_by_token_id`.

### [positions.py](positions.py)

Reads wallet-specific on-chain positions including owned assets, listings, auctions and refundable bids, preserving market/registry identity.

Main entry points: `snapshot`, `positions`.

### [quantum_hash.py](quantum_hash.py)

Classical BLAKE3 digest and integrity comparison. The historical quantum_hash name does not make the implementation a quantum algorithm.

Main entry points: `quantum_hash`, `verify_integrity`, `hash_string`.

### [quantum_search.py](quantum_search.py)

Current cosine-candidate plus deterministic MMR search, with legacy graph propagation and annealing helpers retained separately. Production search does not call QAOA or VQC.

Main entry points: `build_asset_graph`, `quantum_walk_discover`, `qubo_rerank`, `quantum_enhanced_search`, `rank_results`.

### [research_results.py](research_results.py)

Authenticated API exposing retained experiment reports/results without executing quantum experiments on every request.

Main entry points: `load_result`, `results`.

### [reviews.py](reviews.py)

Review APIs bound to verified wallet/account and purchase entitlement; includes legacy entitlement compatibility.

Main entry points: `Review`, `get_reviews`, `save_review`.

### [text_extractor.py](text_extractor.py)

Converts supported uploaded formats into bounded text excerpts for analysis. Extraction is partial, not a complete document-understanding guarantee.

Main entry points: `extract_text`, `_extract_from_pdf`, `_extract_from_csv`, `_extract_from_text`.

## Subdirectories

- [payments](payments/README.md)
