import { expect } from "chai";
import { network } from "hardhat";

describe("KnowledgeAsset", function () {
  let ethers: any;
  let contract: any;
  let seller: any;
  let buyer: any;

  beforeEach(async function () {
    ({ ethers } = await network.connect());

    [seller, buyer] = await ethers.getSigners();

    const Factory = await ethers.getContractFactory("KnowledgeAsset");

    contract = await Factory.deploy();

    await contract.waitForDeployment();
  });

  it("mints NFT and stores all asset data correctly", async function () {
    await contract.connect(seller).mint(
      "QmBLAKE3CID_Test",
      "QmMetadata_Test",
      5_000_000n,
      0,
      85
    );

    const asset = await contract.getAsset(1);

    expect(asset.ipfsCID).to.equal("QmBLAKE3CID_Test");
    expect(asset.priceUSDC).to.equal(5_000_000n);
    expect(asset.seller).to.equal(await seller.getAddress());
    expect(asset.qualityScore).to.equal(85n);
    expect(asset.active).to.equal(true);
  });

  it("assigns NFT ownership to seller", async function () {
    await contract.connect(seller).mint(
      "QmCID",
      "QmMeta",
      5_000_000n,
      0,
      80
    );

    expect(await contract.ownerOf(1)).to.equal(
      await seller.getAddress()
    );
  });

  it("emits AssetMinted event", async function () {
    await expect(
      contract.connect(seller).mint(
        "QmCID",
        "QmMeta",
        5_000_000n,
        0,
        80
      )
    )
      .to.emit(contract, "AssetMinted")
      .withArgs(
        1n,
        await seller.getAddress(),
        "QmCID",
        5_000_000n,
        0n
      );
  });

  it("reverts when IPFS CID is empty", async function () {
    await expect(
      contract.connect(seller).mint(
        "",
        "QmMeta",
        5_000_000n,
        0,
        80
      )
    ).to.be.revertedWith("IPFS CID cannot be empty");
  });

  it("reverts when price is below 1 USDC", async function () {
    await expect(
      contract.connect(seller).mint(
        "QmCID",
        "QmMeta",
        500_000n,
        0,
        80
      )
    ).to.be.revertedWith("Minimum price is 1 USDC");
  });

  it("allows seller to update price", async function () {
    await contract.connect(seller).mint(
      "QmCID",
      "QmMeta",
      5_000_000n,
      0,
      80
    );

    await contract.connect(seller).updatePrice(
      1,
      10_000_000n
    );

    const asset = await contract.getAsset(1);

    expect(asset.priceUSDC).to.equal(10_000_000n);
  });

  it("prevents non-owner from updating price", async function () {
    await contract.connect(seller).mint(
      "QmCID",
      "QmMeta",
      5_000_000n,
      0,
      80
    );

    await expect(
      contract.connect(buyer).updatePrice(
        1,
        10_000_000n
      )
    ).to.be.revertedWith(
      "Only the NFT owner can update the price"
    );
  });
});