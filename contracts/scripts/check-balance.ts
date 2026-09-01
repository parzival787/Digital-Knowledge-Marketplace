import { network } from "hardhat";

async function main() {
  const { ethers } = await network.connect();

  const [signer] = await ethers.getSigners();

  const balance = await ethers.provider.getBalance(
    signer.address
  );

  console.log("Address:", signer.address);
  console.log("Balance:", ethers.formatEther(balance), "POL");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});