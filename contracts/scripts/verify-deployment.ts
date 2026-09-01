import { network } from "hardhat";
import deployment from "../deployment.json";

async function main() {
  const { ethers } = await network.connect();

  console.log("Checking Polygon Amoy deployment...\n");

  console.log("Network Chain ID:");
  console.log((await ethers.provider.getNetwork()).chainId.toString());

  console.log("\nDeployed addresses:");
  console.log("KnowledgeAsset :", deployment.KnowledgeAsset);
  console.log("RoyaltySplitter:", deployment.RoyaltySplitter);
  console.log("Marketplace    :", deployment.Marketplace);
  console.log("MockUSDC       :", deployment.MockUSDC);

  const knowledgeAsset = await ethers.getContractAt(
    "KnowledgeAsset",
    deployment.KnowledgeAsset
  );

  const marketplace = await ethers.getContractAt(
    "Marketplace",
    deployment.Marketplace
  );

  const royaltySplitter = await ethers.getContractAt(
    "RoyaltySplitter",
    deployment.RoyaltySplitter
  );

  const usdc = await ethers.getContractAt(
     "MockERC20",
    deployment.MockUSDC
  );

  console.log("\nContract checks:");

  console.log(
    "KnowledgeAsset totalMinted:",
    (await knowledgeAsset.totalMinted()).toString()
  );

  console.log(
    "Marketplace owner:",
    await marketplace.owner()
  );

  console.log(
    "Marketplace KnowledgeAsset:",
    await marketplace.knowledgeAsset()
  );

  console.log(
    "Marketplace RoyaltySplitter:",
    await marketplace.royaltySplitter()
  );

  console.log(
    "Marketplace USDC:",
    await marketplace.usdc()
  );

  console.log(
    "RoyaltySplitter owner:",
    await royaltySplitter.owner()
  );

  console.log("\nDeployment verification complete.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});