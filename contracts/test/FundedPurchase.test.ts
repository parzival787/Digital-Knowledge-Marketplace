import { expect } from "chai";
import { network } from "hardhat";

const { ethers, networkHelpers } = await network.create();

async function fixture() {
  const [payer, seller, buyer, treasury, stranger] = await ethers.getSigners();
  const usdc = await ethers.deployContract("MockERC20", ["Mock USDC", "USDC", 6]);
  const asset = await ethers.deployContract("KnowledgeAsset");
  const splitter = await ethers.deployContract("RoyaltySplitter", [await usdc.getAddress(), treasury.address, 500]);
  const market = await ethers.deployContract("Marketplace", [await asset.getAddress(), await splitter.getAddress(), await usdc.getAddress()]);
  await splitter.updateMarketplace(await market.getAddress());
  const price = 5_000_000n;
  await asset.connect(seller).getFunction("mint")("file", "metadata", price, 1, 90);
  await market.connect(seller).getFunction("listFixedPrice")(1, price, []);
  await usdc.mint(payer.address, price * 2n);
  await usdc.approve(await market.getAddress(), price * 2n);
  return { payer, seller, buyer, treasury, stranger, usdc, asset, market, price, ref: ethers.id("payment-order-1") };
}

describe("Funded purchase for another wallet", function () {
  it("pays seller and fee, credits only the buyer, and rejects replay after relisting", async function () {
    const { payer, seller, buyer, treasury, usdc, asset, market, price, ref } = await networkHelpers.loadFixture(fixture);
    await expect(market.buyAssetFor(1, buyer.address, price, ref))
      .to.emit(market, "FundedPurchase").withArgs(payer.address, ref, 1n, buyer.address, price);
    expect(await asset.ownerOf(1)).to.equal(seller.address);
    expect(await market.purchaseCount(1, buyer.address)).to.equal(1n);
    expect(await market.hasPurchased(1, payer.address)).to.equal(false);
    expect(await usdc.balanceOf(seller.address)).to.equal(price * 95n / 100n);
    expect(await usdc.balanceOf(treasury.address)).to.equal(price * 5n / 100n);
    await market.connect(seller).getFunction("listFixedPrice")(1, price, []);
    await expect(market.buyAssetFor(2, buyer.address, price, ref)).to.be.revertedWithCustomError(market, "PaymentAlreadySettled");
  });

  it("cannot grant a license without funds and allowance; a failed attempt leaves the reference reusable", async function () {
    const { buyer, stranger, usdc, market, price, ref } = await networkHelpers.loadFixture(fixture);
    await expect(market.connect(stranger).getFunction("buyAssetFor")(1, buyer.address, price, ref)).to.revert(ethers);
    expect(await market.hasPurchased(1, buyer.address)).to.equal(false);
    expect(await market.settledPayments(stranger.address, ref)).to.equal(false);
    await usdc.mint(stranger.address, price);
    await usdc.connect(stranger).getFunction("approve")(await market.getAddress(), price);
    await market.connect(stranger).getFunction("buyAssetFor")(1, buyer.address, price, ref);
    expect(await market.hasPurchased(1, buyer.address)).to.equal(true);
  });

  it("rejects wrong price, invalid buyer, seller as buyer, missing reference, and paused purchases", async function () {
    const { seller, buyer, market, price, ref } = await networkHelpers.loadFixture(fixture);
    await expect(market.buyAssetFor(1, buyer.address, price - 1n, ref)).to.be.revertedWithCustomError(market, "InvalidPrice");
    await expect(market.buyAssetFor(1, ethers.ZeroAddress, price, ref)).to.be.revertedWithCustomError(market, "InvalidBuyer");
    await expect(market.buyAssetFor(1, seller.address, price, ref)).to.be.revertedWithCustomError(market, "SellerCannotBuyOwnAsset");
    await expect(market.buyAssetFor(1, buyer.address, price, ethers.ZeroHash)).to.be.revertedWithCustomError(market, "InvalidPaymentReference");
    await market.pause();
    await expect(market.buyAssetFor(1, buyer.address, price, ref)).to.be.revertedWith("Pausable: paused");
  });
});
