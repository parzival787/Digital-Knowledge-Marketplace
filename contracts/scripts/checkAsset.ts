import { network } from "hardhat";

async function main() {
  const { ethers } = await network.connect();

  const knowledgeAssetAddress =
    "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512";

  const KnowledgeAsset =
    await ethers.getContractFactory("KnowledgeAsset");

  const knowledgeAsset =
    KnowledgeAsset.attach(knowledgeAssetAddress);

  const total = await knowledgeAsset.totalMinted();

  console.log(
    "Total minted:",
    total.toString()
  );

  for (
    let i = 1n;
    i <= total;
    i++
  ) {
    const asset =
      await knowledgeAsset.getAsset(i);

    console.log(`\nAsset #${i}:`);
    console.log(asset);

    console.log("IPFS CID:", asset[0]);
    console.log("Metadata CID:", asset[1]);
    console.log("Price USDC:", asset[2].toString());
    console.log("Creator:", asset[3]);
    console.log("License:", asset[4].toString());
    console.log("Quality Score:", asset[5].toString());
    console.log("Active:", asset[6]);
    console.log("Minted At:", asset[7].toString());
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});