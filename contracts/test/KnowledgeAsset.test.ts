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
    expect(asset.creator).to.equal(await seller.getAddress());
    expect(asset.qualityScore).to.equal(85n);
    expect(asset.active).to.equal(true);
  });

  it("accepts the one-cent mint and update boundary and rejects zero/below-minimum updates", async function () {
    expect(await contract.MIN_PRICE_USDC()).to.equal(10_000n);
    await contract.connect(seller).mint("cent-file", "cent-metadata", 10_000n, 0, 80);
    expect((await contract.getAsset(1)).priceUSDC).to.equal(10_000n);
    await contract.connect(seller).updatePrice(1, 500_000n);
    await contract.connect(seller).updatePrice(1, 10_000n);
    expect((await contract.getAsset(1)).priceUSDC).to.equal(10_000n);
    for (const price of [0n, 9_999n]) {
      await expect(contract.connect(seller).mint("file", "metadata", price, 0, 80))
        .to.be.revertedWithCustomError(contract, "PriceTooLow").withArgs(price, 10_000n);
      await expect(contract.connect(seller).updatePrice(1, price))
        .to.be.revertedWithCustomError(contract, "PriceTooLow").withArgs(price, 10_000n);
    }
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
    ).to.be.revertedWithCustomError(
      contract,
      "EmptyIPFSCID"
    );
  });

  it("reverts when metadata CID is empty", async function () {
    await expect(
      contract.connect(seller).mint(
        "QmCID",
        "",
        5_000_000n,
        0,
        80
      )
    ).to.be.revertedWithCustomError(
      contract,
      "EmptyMetadataCID"
    );
  });

  it("reverts when price is below 0.01 USDC", async function () {
    await expect(
      contract.connect(seller).mint(
        "QmCID",
        "QmMeta",
        9_999n,
        0,
        80
      )
    ).to.be.revertedWithCustomError(
      contract,
      "PriceTooLow"
    ).withArgs(9_999n, 10_000n);
  });

  it("reverts when price is above 100 USDC", async function () {
    await expect(
      contract.connect(seller).mint(
        "QmCID",
        "QmMeta",
        200_000_000n,
        0,
        80
      )
    ).to.be.revertedWithCustomError(
      contract,
      "PriceTooHigh"
    ).withArgs(200_000_000n, 100_000_000n);
  });

  it("reverts when quality score exceeds 100", async function () {
    await expect(
      contract.connect(seller).mint(
        "QmCID",
        "QmMeta",
        5_000_000n,
        0,
        101
      )
    ).to.be.revertedWithCustomError(
      contract,
      "QualityScoreTooHigh"
    ).withArgs(101n, 100n);
  });

  it("reverts when looking up a nonexistent asset", async function () {
    await expect(
      contract.getAsset(999)
    ).to.be.revertedWithCustomError(
      contract,
      "AssetDoesNotExist"
    ).withArgs(999n);
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
    ).to.be.revertedWithCustomError(
      contract,
      "NotAssetOwner"
    );
  });

  it("prevents updating the price of an inactive asset", async function () {
    await contract.connect(seller).mint(
      "QmCID",
      "QmMeta",
      5_000_000n,
      0,
      80
    );

    await contract.connect(seller).deactivate(1);

    await expect(
      contract.connect(seller).updatePrice(
        1,
        10_000_000n
      )
    ).to.be.revertedWithCustomError(
      contract,
      "AssetInactive"
    );
  });

  it("allows the owner to deactivate an asset", async function () {
    await contract.connect(seller).mint(
      "QmCID",
      "QmMeta",
      5_000_000n,
      0,
      80
    );

    await contract.connect(seller).deactivate(1);

    const asset = await contract.getAsset(1);

    expect(asset.active).to.equal(false);
  });

  it("prevents non-owner from deactivating", async function () {
    await contract.connect(seller).mint(
      "QmCID",
      "QmMeta",
      5_000_000n,
      0,
      80
    );

    await expect(
      contract.connect(buyer).deactivate(1)
    ).to.be.revertedWithCustomError(
      contract,
      "NotAssetOwner"
    );
  });

  it("prevents deactivating an already-inactive asset", async function () {
    await contract.connect(seller).mint(
      "QmCID",
      "QmMeta",
      5_000_000n,
      0,
      80
    );

    await contract.connect(seller).deactivate(1);

    await expect(
      contract.connect(seller).deactivate(1)
    ).to.be.revertedWithCustomError(
      contract,
      "AlreadyInactive"
    );
  });

  it("emits AssetDeactivated event", async function () {
    await contract.connect(seller).mint(
      "QmCID",
      "QmMeta",
      5_000_000n,
      0,
      80
    );

    await expect(
      contract.connect(seller).deactivate(1)
    )
      .to.emit(contract, "AssetDeactivated")
      .withArgs(1n);
  });

  it("returns an ipfs:// tokenURI pointing at the metadata CID", async function () {
    await contract.connect(seller).mint(
      "QmCID",
      "QmMetadata_Test",
      5_000_000n,
      0,
      80
    );

    expect(await contract.tokenURI(1)).to.equal(
      "ipfs://QmMetadata_Test"
    );
  });
});
