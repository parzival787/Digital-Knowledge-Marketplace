# Decentralized Knowledge Marketplace

DKM is a prototype marketplace for discovering and sharing knowledge assets such as documents and datasets. A creator uploads a file, AI generates catalog metadata, semantic search helps buyers find relevant assets, and a connected wallet handles the blockchain marketplace workflow.

## Start here

- **Creators:** analyze a document, review its generated metadata, upload the file and metadata to IPFS, and use the minting interface.
- **Buyers:** browse or search the marketplace, connect a wallet on Polygon Amoy, and use the contract-based purchase workflow.
- **Developers:** the application has three independently configured parts: a Next.js frontend, a FastAPI backend, and Solidity contracts.

This repository is a development prototype. Service configuration and deployed contract addresses are required before the full workflow can run.

## Features in the code

- Text extraction from PDF, CSV, TXT, Markdown, JSON, and XML files.
- Local Ollama metadata enrichment: title, summary, tags, domain, quality score, and suggested price.
- Sentence Transformer embeddings and PostgreSQL/pgvector semantic search.
- Pinata uploads for files and metadata, with BLAKE3 integrity hashes.
- In-memory exact-duplicate checks and rejection of very small uploads.
- Knowledge-asset, marketplace, mock token, and royalty-splitter contracts.
- Wallet connection, minting, marketplace, and backend diagnostic pages.
- Experimental graph discovery and QUBO reranking using a classical simulated-annealing sampler.

The modules named `quantum_hash` and `quantum_search` use BLAKE3 and software-based search/reranking; they do not require quantum hardware.

## How the project works

```text
File -> text extraction -> Ollama metadata -> review
     -> Pinata/IPFS storage + pgvector indexing -> asset minting
Search -> query embedding -> candidate retrieval/reranking -> marketplace
Wallet -> contract purchase -> purchase/ownership access check
```

## Technology

| Part | Technology |
| --- | --- |
| Web interface | Next.js 14, React, TypeScript, Tailwind CSS |
| Wallet integration | wagmi, RainbowKit, viem |
| API | Python, FastAPI |
| AI | Ollama llama3.2:3b, Sentence Transformers all-MiniLM-L6-v2 |
| Database | PostgreSQL with pgvector |
| File storage | Pinata/IPFS |
| Contracts | Solidity 0.8.20, Hardhat, OpenZeppelin; Polygon Amoy |

## Repository map

- [backend/main.py](backend/main.py): API routes and upload/search orchestration.
- [backend/services](backend/services): extraction, AI, embeddings, database, blockchain, and integrity services.
- [frontend/app](frontend/app): home, minting, marketplace, and diagnostic pages.
- [frontend/lib](frontend/lib): API client and blockchain integration.
- [contracts/contracts](contracts/contracts): Solidity contracts.
- [contracts/test](contracts/test): contract tests.

## Local setup

Clone the repository and open separate terminals for the services:

```sh
git clone https://github.com/parzival787/capstone-project.git
cd capstone-project
```

### 1. Start the supporting services

Use PostgreSQL with the pgvector extension available and a database for the project. Run Ollama and download its model:

```sh
ollama pull llama3.2:3b
```

Configure a Polygon Amoy RPC endpoint and the contract deployment you intend to use. Ensure the frontend addresses in [frontend/contracts/addresses/index.ts](frontend/contracts/addresses/index.ts) match the backend's contract addresses.

### 2. Configure and run the backend

Create a Python virtual environment inside `backend/` and activate it. The committed [backend/requirements.txt](backend/requirements.txt) currently lists only part of the dependencies, so it is not a complete fresh-install manifest. Imports in the API and service modules also require these packages:

```sh
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install fastapi uvicorn python-multipart python-dotenv httpx openai sentence-transformers pdfplumber asyncpg pgvector web3 blake3 networkx dimod
```

Create `backend/.env` with your own configuration:

```dotenv
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/dkm
OLLAMA_BASE_URL=http://localhost:11434/v1
PINATA_JWT=YOUR_PINATA_JWT
BLOCKCHAIN_RPC_URL=YOUR_POLYGON_AMOY_RPC_URL
BLOCKCHAIN_CHAIN_ID=80002
MARKETPLACE_ADDRESS=YOUR_DEPLOYED_MARKETPLACE_ADDRESS
KNOWLEDGE_ASSET_ADDRESS=YOUR_DEPLOYED_KNOWLEDGE_ASSET_ADDRESS
```

Start the API from `backend/`:

```sh
python -m uvicorn main:app --reload --port 8000
```

API documentation: http://localhost:8000/docs. The startup hook creates the application's database tables. The health endpoint also checks the legacy `NFT_STORAGE_TOKEN` setting even though the upload implementation uses `PINATA_JWT`; a degraded health response may reflect that mismatch.

### 3. Configure and run the frontend

From `frontend/`, create `.env.local`:

```dotenv
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_WC_PROJECT_ID=YOUR_WALLETCONNECT_PROJECT_ID
```

```sh
npm install
npm run dev
```

Open http://localhost:3000. Connect a wallet configured for Polygon Amoy when testing blockchain features.

### 4. Work with the contracts

From `contracts/`:

```sh
npm install
npx hardhat compile
npx hardhat test
```

The package's `npm test` script is a placeholder; use the Hardhat test command. Network deployment requires `ALCHEMY_AMOY_URL` and a test wallet's `PRIVATE_KEY` in `contracts/.env`. See [contracts/scripts](contracts/scripts) for deployment and verification scripts.

## Current limits

- The backend dependency manifest needs completion; the setup above is derived from imports and has not been rehearsed in a fresh environment.
- PDF extraction samples up to five pages and 4,000 characters; CSV extraction samples the header and first 50 data rows.
- Duplicate detection is process-local and resets when the backend restarts.
- Pinata uploads use the public network. A blockchain access check does not make the underlying IPFS file private.
- Contract addresses, RPC settings, and external service credentials must agree across the three parts.

Use sample documents and a testnet wallet for demonstrations. Never commit credentials or wallet private keys.
