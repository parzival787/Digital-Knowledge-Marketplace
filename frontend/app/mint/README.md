# frontend/app/mint

Part of DKM. See the root README for startup, trust boundaries and validation.

## Page

Route: `/mint`. Analyze, upload encrypted content, then sign a separate registration transaction and link the confirmed token. Supports recovery after an interrupted mint.

## Files

### [page.tsx](page.tsx)

File analysis/upload, price/license entry, wallet mint, receipt confirmation and upload/token linking. Resumes saved uploads and pending transaction hashes.

Main entry points: `MintFlow`, `run`, `link`, `mint`, `finishMint`, `MintContent`, `MintPage`.
