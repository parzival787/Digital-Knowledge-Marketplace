import { network } from "hardhat";

async function main() {
  const { ethers } = await network.connect();

  const address =
    "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512";

  const code = await ethers.provider.getCode(address);

  console.log("KnowledgeAsset address:", address);
  console.log("Contract code length:", code.length);
  console.log("Contract exists:", code !== "0x");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});