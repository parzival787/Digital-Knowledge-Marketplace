export const CONTRACTS = {
  MockUSDC: "0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719",
  KnowledgeAsset: "0xCA6f1E6C08Dddda08e4288B8eFE07bF54f67AeD7",
  RoyaltySplitter: "0x36CAa5b59825a378664E75b5EFB30988F71901c0",
  Marketplace: "0xc1cfA63fDA41cD1Ee76B24F1D1B2b993661a67A5",
} as const;
// Add reviewed old marketplace addresses here when switching deployments.
export const LEGACY_MARKETPLACES: readonly `0x${string}`[] = ["0xDe7bdacb8B3ff631dbcdb09C81c0de7421475A5d"];

export const LEGACY_TOKEN_LIMIT = 6n;
