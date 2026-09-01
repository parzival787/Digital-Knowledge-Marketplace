import hre from "hardhat";

async function main() {
  const { ethers } = await hre.network.connect();

  const marketplace = await ethers.getContractAt(
    "Marketplace",
    "0x67E4148eBf2d23997a30950efCBbc3294B069008"
  );

  const selector = "0x91c0aaa2";

  console.log("Looking for:", selector);

  for (const fragment of marketplace.interface.fragments) {
    if (fragment.type !== "error") continue;

    const errorFragment = fragment;

    const selectorForError =
      marketplace.interface.getError(errorFragment.name)?.selector;

    if (selectorForError === selector) {
      console.log("MATCH FOUND!");
      console.log("Error:", errorFragment.format());
      console.log("Selector:", selectorForError);
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});