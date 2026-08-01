import { network } from "hardhat";
import fs from "fs";

async function main() {
  const { ethers } = await network.connect();

  const [deployer] = await ethers.getSigners();

  console.log("=================================");
  console.log("Deploying KnowledgeAsset");
  console.log("=================================");
  console.log("Deployer:", deployer.address);

  const balance = await deployer.provider.getBalance(deployer.address);

  console.log(
    "Balance:",
    ethers.formatEther(balance),
    "POL"
  );

  if (balance < ethers.parseEther("0.01")) {
    throw new Error(
      "Wallet balance too low. Get test POL from the Polygon Amoy faucet."
    );
  }

  const Factory = await ethers.getContractFactory("KnowledgeAsset");

  console.log("Deploying contract...");

  const contract = await Factory.deploy();

  await contract.waitForDeployment();

  const address = await contract.getAddress();

  console.log();
  console.log("KnowledgeAsset deployed!");
  console.log("Address:", address);

  fs.writeFileSync(
    "deployed_addresses.json",
    JSON.stringify(
      {
        KnowledgeAsset: address,
        network: "polygonAmoy",
        deployedAt: new Date().toISOString(),
        deployer: deployer.address,
      },
      null,
      2
    )
  );

  console.log();
  console.log("Saved deployed_addresses.json");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
