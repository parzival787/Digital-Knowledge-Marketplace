import { api } from "./client";

export type AnalyzeResponse = {
  success: boolean;
  metadata: {
    title?: string;
    summary?: string;
    domain?: string;
    tags?: string[];
    quality_score?: number;
    recommended_price_usdc?: number;
    [key: string]: unknown;
  };
  file_size?: number;
};

export type UploadIPFSResponse = {
  file_cid: string;
  metadata_cid: string;
  vector_id: string;
};

export type SearchResult = {
  token_id?: number;
  final_score?: number;
  score: number;
  distance?: number;
  vector_id: string;
  file_cid: string;
  metadata_cid: string;
  title: string;
  domain: string;
  tags: string[];
  quality?: number;
  price_usdc?: number;
  blake3_hash?: string;
};

export type SearchResponse = {
  results: SearchResult[];
};

export async function analyzeAsset(file: File): Promise<AnalyzeResponse> {
  const body = new FormData(); body.append("file", file);
  return api("/api/analyze", { method: "POST", body });
}
export async function uploadAssetToIPFS(file: File, metadata: Record<string, unknown>): Promise<UploadIPFSResponse> {
  const body = new FormData(); body.append("file", file); body.append("metadata_json", JSON.stringify(metadata));
  return api("/api/upload-ipfs", { method: "POST", body });
}
export async function searchAssets(query: string, domain?: string, max_price?: number): Promise<SearchResponse> {
  return api("/api/search", { method: "POST", body: JSON.stringify({ query, domain: domain || undefined, max_price }) });
}
export async function checkBackendHealth() { return api("/health"); }
