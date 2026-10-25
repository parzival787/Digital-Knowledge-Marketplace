# Decentralized Knowledge Marketplace (DKM)

DKM is a college-project prototype for uploading knowledge documents, registering them on Polygon Amoy, discovering them through semantic search, and purchasing access to encrypted files. The browser uses Next.js and MetaMask; FastAPI connects PostgreSQL/pgvector, Ollama, Pinata and the deployed contracts.

## Current application

- Welcome, signup/login, revocable cookie sessions, optional Google OAuth and signed wallet verification.
- Document analysis with an evidence-backed Ollama rubric; normalized 384-dimensional MiniLM embeddings.
- AES-256-GCM encrypted files pinned through Pinata, with BLAKE3 exact-duplicate and integrity checks.
- Mint recovery, fixed-price listings, cancellation, access purchases and auctions on Amoy (chain ID **80002**).
- Auctions accept **2 minutes to 720 hours** through the Minutes/Hours selector. Finalization and refunds require separate transactions.
- MockUSDC pays asset prices; test POL pays gas. The minimum new registration price is **0.01 USDC**. A purchase grants access while the creator retains the registration NFT.
- Five-minute purchase quotes do not reserve listings. The recorded platform rate is 5%, deducted from seller proceeds; configured royalties also reduce proceeds.
- Protected downloads verify on-chain access, decrypt on the backend and check the recovered plaintext hash.

The user-facing payment route is wallet-only. Retained Transak/Razorpay/payout/receipt code supports historical and optional workflows; its presence is not a claim of live fiat conversion or universal currency support. QAOA/VQC are offline simulator experiments, not production search or price-setting algorithms.

## Start locally (Windows PowerShell)

Keep your existing private configuration and Docker volume. Do not regenerate the content master key or reset PostgreSQL to resolve a startup problem.

1. Start Docker Desktop and the existing `dkm-postgres` container. Its observed image is `pgvector/pgvector:pg15`, host port 5432. If provisioning a new database, enable the `vector` extension before running backend schema setup.
2. Check `backend/.env` privately: `DATABASE_URL`, the existing `CONTENT_MASTER_KEY`, Pinata credentials, Ollama settings and deployed chain addresses must match your setup. For a dedicated gateway set `PINATA_GATEWAY=your-gateway.mypinata.cloud` (hostname only). Credentials are never committed.
3. Start the configured Ollama service and ensure the configured model and MiniLM cache are available.
4. In one terminal:

```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

5. In another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000. For a production preview, use `npm run build` followed by `npm run start`; source changes require rebuilding and restarting that preview. Backend changes require restarting Uvicorn unless it was launched with `--reload`.

For a new Python environment, create `backend/venv` and install `backend/requirements.txt`; quantum experiments have separate requirements. Database, model, wallet and Pinata setup are prerequisites, not installed by starting the UI.

## Data and trust boundaries

| Location | Contents |
| --- | --- |
| PostgreSQL | Accounts, hashed sessions, metadata, vectors, wrapped per-file keys, quotes and workflow history |
| Pinata/IPFS | Encrypted document bytes and public metadata |
| Amoy contracts | Asset registrations, listings, auction bids, token settlement and access counters |
| Private backend configuration | Master encryption key, provider credentials and RPC configuration |

Inspect locally with `docker exec -it dkm-postgres psql -U postgres -d dkm` (adjust role/database to your configuration), then `\dt` or a limited SELECT. Do not publish password hashes, session records, encrypted-key envelopes or database dumps. A database backup also needs the original master key and retained IPFS content for full recovery.

The backend can decrypt content. IPFS pinning is an availability dependency; a CID does not provide confidentiality. Registration does not prove authorship. Authorized recipients can redistribute downloaded plaintext.

## Tests and evidence

```powershell
# From backend/
.\venv\Scripts\python.exe -m unittest discover -s tests
.\venv\Scripts\python.exe -m unittest test_ipfs_gateway

# From frontend/
node --test tests/*.test.mjs
npx tsc --noEmit
npm run build

# From contracts/
npx hardhat test
npx tsc --noEmit
```

See [TEST_EVIDENCE.md](TEST_EVIDENCE.md), [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) and [acceptance_results.json](acceptance_results.json) for dated outcomes. Local unit tests and simulated provider boundaries do not establish a complete live wallet workflow or an independent security audit. No real-money or mainnet completion is claimed.

The retained VQC benchmark reports test NDCG@10 of 0.905296 for MiniLM and 0.609317 for trained VQC; QAOA reports a 17.6013% mean optimality gap across 64 synthetic cases. See [research_results](research_results/README.md). These are small simulator comparisons with no demonstrated quantum advantage.

## Documentation map

- [Root file reference](docs/ROOT_FILES.md) describes top-level configuration, evidence and planning documents.
- [Backend](backend/README.md): APIs, services, storage and tests.
- [Frontend](frontend/README.md): routes, components, authentication and wallet interaction.
- [Contracts](contracts/README.md): actual Hardhat setup, deployment records and access semantics.
- Each source directory has a README describing every immediate file; each app-page directory describes its route. Dependencies, generated builds and secrets are excluded.
- [FEATURE_COVERAGE.md](FEATURE_COVERAGE.md) maps capabilities; older rollout documents describe their dated scope.
- [Technical guide](output/pdf/DKM_End_to_End_Project_Guide.pdf) provides the detailed walkthrough and file atlas. Code and newer dated notes take precedence over older PDFs.

## Test-token funding

From the repository root, preview with:

```powershell
.\backend\venv\Scripts\python.exe .\backend\mint_test_usdc.py WALLET_ADDRESS AMOUNT
```

Append `--send` to mint additional test tokens using the configured signer and its Amoy POL. The script is restricted to the known Amoy mock-token contract; its symbol is `USDC`, but it is test currency. Check any submitted transaction hash before retrying after a timeout.

## Contributing

Read [AGENTS.md](AGENTS.md) and [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md). Work on a feature branch, preserve user data and existing buyer entitlements, run relevant checks and use a pull request. Never commit `.env`, private keys, backup contents or copied credentials. Contract source changes do not alter already deployed bytecode.
