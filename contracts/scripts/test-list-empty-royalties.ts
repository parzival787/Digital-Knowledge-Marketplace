import hre from "hardhat";
import deployment from "../deployment.json";

async function main() {
  const { ethers } = await hre.network.connect();

  const [signer] = await ethers.getSigners();

  console.log("Signer:", signer.address);
  console.log("Marketplace:", deployment.Marketplace);
  console.log("KnowledgeAsset:", deployment.KnowledgeAsset);

  const marketplace = await ethers.getContractAt(
    "Marketplace",
    deployment.Marketplace
  );

  const nft = await ethers.getContractAt(
    "KnowledgeAsset",
    deployment.KnowledgeAsset
  );

  const tokenId = 1n;

  console.log("NFT owner:", await nft.ownerOf(tokenId));

  console.log(
    "Approved:",
    await nft.getApproved(tokenId)
  );

  console.log("Testing listFixedPrice with EMPTY royalties...");

  try {
    const tx = await marketplace.listFixedPrice(
      tokenId,
      10_000_000n,
      []
    );

    console.log("Transaction:", tx.hash);

    await tx.wait();

    console.log("SUCCESS: NFT listed!");
  } catch (error: any) {
    console.log("FAILED");

    console.log(error);

    if (error?.data) {
      console.log("Revert data:", error.data);
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});