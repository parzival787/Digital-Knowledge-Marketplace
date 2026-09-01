"use client";

import { useState } from "react";
import {
  useAccount,
  useWriteContract,
  useWaitForTransactionReceipt,
} from "wagmi";

import { knowledgeAssetContract } from "@/lib/blockchain/contracts";

import {
  analyzeAsset,
  uploadAssetToIPFS,
  type AnalyzeResponse,
} from "@/lib/api/backend";

export default function MintPage() {
  const { address, isConnected } = useAccount();

  const [ipfsCID, setIpfsCID] = useState("");
  const [metadataCID, setMetadataCID] = useState("");
  const [price, setPrice] = useState("");
  const [license, setLicense] = useState("0");
  const [qualityScore, setQualityScore] = useState("");

  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [analysis, setAnalysis] =
    useState<AnalyzeResponse | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState("");

  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const {
    data: hash,
    writeContractAsync,
    isPending,
    error,
  } = useWriteContract();

  const {
    isLoading: isConfirming,
    isSuccess: isConfirmed,
  } = useWaitForTransactionReceipt({
    hash,
  });

  // =========================================================
  // AI ANALYSIS
  // =========================================================

  async function handleAnalyze() {
    if (!selectedFile) {
      alert("Please select a file first.");
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError("");
    setAnalysis(null);

    // Clear previous upload
    setIpfsCID("");
    setMetadataCID("");
    setUploadError("");

    try {
      const result = await analyzeAsset(selectedFile);

      console.log("ANALYSIS RESULT:", result);

      setAnalysis(result);

      const quality = Math.round(
        (result.metadata.quality_score ?? 0) * 100
      );

      setQualityScore(quality.toString());

      if (
        result.metadata.recommended_price_usdc !==
        undefined
      ) {
        setPrice(
          result.metadata.recommended_price_usdc.toString()
        );
      }
    } catch (err) {
      console.error("Analysis failed:", err);

      setAnalysisError(
        err instanceof Error
          ? err.message
          : "Failed to analyze file."
      );
    } finally {
      setIsAnalyzing(false);
    }
  }

  // =========================================================
  // IPFS UPLOAD
  // =========================================================

  async function handleUploadIPFS() {
    if (!selectedFile) {
      alert("Please select a file first.");
      return;
    }

    if (!analysis) {
      alert("Please analyze the dataset first.");
      return;
    }

    setIsUploading(true);
    setUploadError("");

    try {
      const metadata = {
        title: analysis.metadata.title ?? "",
        summary: analysis.metadata.summary ?? "",
        domain: analysis.metadata.domain ?? "other",
        tags: analysis.metadata.tags ?? [],
        quality_score:
          analysis.metadata.quality_score ?? 0,
        recommended_price_usdc:
          analysis.metadata.recommended_price_usdc ?? 5,
      };

      console.log("UPLOADING METADATA:", metadata);

      const result = await uploadAssetToIPFS(
        selectedFile,
        metadata
      );

      console.log("IPFS UPLOAD RESULT:", result);

      setIpfsCID(result.file_cid);
      setMetadataCID(result.metadata_cid);
    } catch (err) {
      console.error("IPFS upload failed:", err);

      setUploadError(
        err instanceof Error
          ? err.message
          : "Failed to upload asset to IPFS."
      );
    } finally {
      setIsUploading(false);
    }
  }

  // =========================================================
  // BLOCKCHAIN MINT
  // =========================================================

  async function mintAsset() {
    if (!isConnected) {
      alert("Please connect your wallet first.");
      return;
    }

    if (!address) {
      alert("Wallet address not available.");
      return;
    }

    if (!analysis) {
      alert("Please analyze the dataset first.");
      return;
    }

    if (!ipfsCID || !metadataCID) {
      alert("Please upload the dataset to IPFS first.");
      return;
    }

    const priceNumber = Number(price);

    if (
      !Number.isFinite(priceNumber) ||
      priceNumber < 1 ||
      priceNumber > 100
    ) {
      alert("Price must be between 1 and 100 USDC");
      return;
    }

    const qualityNumber = Number(qualityScore);

    if (
      !Number.isInteger(qualityNumber) ||
      qualityNumber < 0 ||
      qualityNumber > 100
    ) {
      alert("Quality score must be between 0 and 100");
      return;
    }

    const licenseNumber = Number(license);

    if (
      !Number.isInteger(licenseNumber) ||
      licenseNumber < 0 ||
      licenseNumber > 2
    ) {
      alert("Invalid license");
      return;
    }

    const priceUSDC = BigInt(
      Math.round(priceNumber * 1_000_000)
    );

    const mintArgs = [
      ipfsCID.trim(),
      metadataCID.trim(),
      priceUSDC,
      BigInt(licenseNumber),
      BigInt(qualityNumber),
    ] as const;

    console.log("MINT ARGUMENTS:", mintArgs);

    try {
      const txHash = await writeContractAsync({
        ...knowledgeAssetContract,
        functionName: "mint",
        args: mintArgs,
      });

      console.log("Transaction submitted:", txHash);
    } catch (err) {
      console.error("Mint transaction error:", err);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">

      <h1 className="text-3xl font-bold">
        Create Knowledge Asset
      </h1>

      <p className="mt-2 text-muted-foreground">
        Analyze, upload, and mint your knowledge asset.
      </p>

      <div className="mt-8 space-y-6">

        {/* ================================================= */}
        {/* 1. SELECT FILE */}
        {/* ================================================= */}

        <div className="rounded-xl border p-6">

          <h2 className="text-xl font-bold">
            1. Select Knowledge Dataset
          </h2>

          <p className="mt-2 text-sm text-muted-foreground">
            Upload a PDF, CSV, TXT, or supported knowledge
            document for AI analysis.
          </p>

          <input
            type="file"
            onChange={(e) => {
              const file =
                e.target.files?.[0] ?? null;

              setSelectedFile(file);
              setAnalysis(null);
              setAnalysisError("");
              setUploadError("");
              setIpfsCID("");
              setMetadataCID("");
            }}
            className="mt-4 w-full rounded-md border px-3 py-2"
          />

          {selectedFile && (
            <p className="mt-3 text-sm">
              <span className="font-medium">
                Selected:
              </span>{" "}
              {selectedFile.name}
            </p>
          )}

          <button
            type="button"
            onClick={handleAnalyze}
            disabled={
              !selectedFile ||
              isAnalyzing
            }
            className="mt-4 rounded-md border px-5 py-2 font-medium disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isAnalyzing
              ? "Analyzing with AI..."
              : "Analyze Dataset"}
          </button>

          {analysisError && (
            <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-600">
              <p className="font-medium">
                Analysis failed
              </p>

              <p className="mt-1">
                {analysisError}
              </p>
            </div>
          )}

        </div>

        {/* ================================================= */}
        {/* 2. AI ANALYSIS */}
        {/* ================================================= */}

        {analysis && (
          <div className="rounded-xl border p-6">

            <h2 className="text-xl font-bold">
              2. AI Analysis
            </h2>

            <div className="mt-5 space-y-4 text-sm">

              <div>
                <p className="font-medium">Title</p>
                <p className="mt-1">
                  {analysis.metadata.title ??
                    "Not available"}
                </p>
              </div>

              <div>
                <p className="font-medium">Summary</p>
                <p className="mt-1">
                  {analysis.metadata.summary ??
                    "Not available"}
                </p>
              </div>

              <div>
                <p className="font-medium">Domain</p>
                <p className="mt-1">
                  {analysis.metadata.domain ??
                    "Not available"}
                </p>
              </div>

              <div>
                <p className="font-medium">Tags</p>
                <p className="mt-1">
                  {analysis.metadata.tags?.join(", ") ||
                    "No tags"}
                </p>
              </div>

              <div>
                <p className="font-medium">
                  Quality Score
                </p>

                <p className="mt-1">
                  {Math.round(
                    (analysis.metadata.quality_score ??
                      0) * 100
                  )}
                  /100
                </p>
              </div>

              <div>
                <p className="font-medium">
                  Recommended Price
                </p>

                <p className="mt-1">
                  {analysis.metadata
                    .recommended_price_usdc ??
                    "Not available"}{" "}
                  USDC
                </p>
              </div>

            </div>

          </div>
        )}

        {/* ================================================= */}
        {/* 3. IPFS UPLOAD */}
        {/* ================================================= */}

        {analysis && (
          <div className="rounded-xl border p-6">

            <h2 className="text-xl font-bold">
              3. Upload to IPFS
            </h2>

            <p className="mt-2 text-sm text-muted-foreground">
              Store the dataset and its metadata using the
              existing backend IPFS pipeline.
            </p>

            <button
              type="button"
              onClick={handleUploadIPFS}
              disabled={isUploading}
              className="mt-4 rounded-md border px-5 py-2 font-medium disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isUploading
                ? "Uploading to IPFS..."
                : "Upload to IPFS"}
            </button>

            {uploadError && (
              <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-600">
                <p className="font-medium">
                  IPFS upload failed
                </p>

                <p className="mt-1">
                  {uploadError}
                </p>
              </div>
            )}

            {ipfsCID && metadataCID && (
              <div className="mt-5 rounded-md border border-green-200 bg-green-50 p-4 text-sm">

                <p className="font-medium text-green-700">
                  Upload successful
                </p>

                <div className="mt-3 space-y-3">

                  <div>
                    <p className="font-medium">
                      File CID
                    </p>

                    <p className="mt-1 break-all">
                      {ipfsCID}
                    </p>
                  </div>

                  <div>
                    <p className="font-medium">
                      Metadata CID
                    </p>

                    <p className="mt-1 break-all">
                      {metadataCID}
                    </p>
                  </div>

                </div>

              </div>
            )}

          </div>
        )}

        {/* ================================================= */}
        {/* 4. ASSET SETTINGS */}
        {/* ================================================= */}

        {analysis && (
          <div className="rounded-xl border p-6">

            <h2 className="text-xl font-bold">
              4. Asset Settings
            </h2>

            {/* Price */}

            <div className="mt-5">

              <label className="text-sm font-medium">
                Price (USDC)
              </label>

              <input
                type="number"
                min="1"
                max="100"
                step="0.01"
                value={price}
                onChange={(e) =>
                  setPrice(e.target.value)
                }
                className="mt-2 w-full rounded-md border px-3 py-2"
              />

              <p className="mt-1 text-xs text-muted-foreground">
                Recommended price is generated by AI.
                You can adjust it between 1 and 100 USDC.
              </p>

            </div>

            {/* License */}

            <div className="mt-5">

              <label className="text-sm font-medium">
                License
              </label>

              <select
                value={license}
                onChange={(e) =>
                  setLicense(e.target.value)
                }
                className="mt-2 w-full rounded-md border px-3 py-2"
              >
                <option value="0">
                  Open Access
                </option>

                <option value="1">
                  Single Use
                </option>

                <option value="2">
                  Commercial
                </option>
              </select>

            </div>

            {/* Quality */}

            <div className="mt-5">

              <label className="text-sm font-medium">
                Quality Score
              </label>

              <input
                type="number"
                min="0"
                max="100"
                value={qualityScore}
                onChange={(e) =>
                  setQualityScore(e.target.value)
                }
                className="mt-2 w-full rounded-md border px-3 py-2"
              />

            </div>

          </div>
        )}

        {/* ================================================= */}
        {/* 5. MINT */}
        {/* ================================================= */}

        {analysis && (
          <div>

            <button
              type="button"
              onClick={mintAsset}
              disabled={
                isPending ||
                isConfirming ||
                !ipfsCID ||
                !metadataCID
              }
              className="w-full rounded-md bg-primary px-6 py-3 font-medium text-primary-foreground disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isPending
                ? "Confirm transaction..."
                : isConfirming
                ? "Minting..."
                : "Mint Knowledge Asset"}
            </button>

            {!ipfsCID || !metadataCID ? (
              <p className="mt-2 text-center text-xs text-muted-foreground">
                Upload the asset to IPFS before minting.
              </p>
            ) : null}

          </div>
        )}

        {/* ================================================= */}
        {/* TRANSACTION */}
        {/* ================================================= */}

        {hash && (
          <div className="rounded-md border p-4 text-sm">

            <p className="font-medium">
              Transaction submitted
            </p>

            <p className="mt-1 break-all text-muted-foreground">
              {hash}
            </p>

          </div>
        )}

        {isConfirmed && (
          <div className="rounded-md border border-green-200 bg-green-50 p-4 text-sm text-green-700">

            <p className="font-medium">
              Knowledge Asset minted successfully!
            </p>

          </div>
        )}

        {error && (
          <div className="rounded-md border p-4 text-sm text-red-500">

            <p className="font-medium">
              Transaction failed
            </p>

            <p className="mt-1">
              {error.message}
            </p>

          </div>
        )}

      </div>

    </main>
  );
}