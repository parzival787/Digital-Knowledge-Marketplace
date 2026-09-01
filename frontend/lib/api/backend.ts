const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

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

export async function analyzeAsset(
  file: File
): Promise<AnalyzeResponse> {
  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(
    `${BACKEND_URL}/api/analyze`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    const message = await response.text();

    throw new Error(
      `Analyze failed (${response.status}): ${message}`
    );
  }

  return response.json();
}

export async function uploadAssetToIPFS(
  file: File,
  metadata: Record<string, unknown>
): Promise<UploadIPFSResponse> {
  const formData = new FormData();

  formData.append("file", file);
  formData.append(
    "metadata_json",
    JSON.stringify(metadata)
  );

  const response = await fetch(
    `${BACKEND_URL}/api/upload-ipfs`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    const message = await response.text();

    throw new Error(
      `IPFS upload failed (${response.status}): ${message}`
    );
  }

  return response.json();
}

export async function searchAssets(
  query: string,
  limit = 5
): Promise<SearchResponse> {
  const response = await fetch(
    `${BACKEND_URL}/api/search`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        limit,
      }),
    }
  );

  if (!response.ok) {
    const message = await response.text();

    throw new Error(
      `Search failed (${response.status}): ${message}`
    );
  }

  return response.json();
}

export async function checkBackendHealth() {
  const response = await fetch(
    `${BACKEND_URL}/health`,
    {
      method: "GET",
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      `Backend health check failed (${response.status})`
    );
  }

  return response.json();
}
