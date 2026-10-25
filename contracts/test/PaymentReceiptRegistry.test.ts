import { expect } from "chai";
import { network } from "hardhat";

const { ethers, networkHelpers } = await network.create();
async function fixture() {
  const [admin, recorder, buyer, seller, stranger] = await ethers.getSigners();
  const registry: any = await ethers.deployContract("PaymentReceiptRegistry", [recorder.address, true]);
  const reference = ethers.id("random-internal-reference");
  const payment = {
    assetContract: admin.address, tokenId: 1n, buyer: buyer.address, seller: seller.address,
    paymentCurrency: ethers.id("fiat:INR:2"), paymentAmount: 10000n,
    payoutCurrency: ethers.id("fiat:EUR:2"), payoutAmount: 95n,
    providerReference: ethers.id("salted-provider-reference"), evidenceHash: ethers.id("salted-verified-evidence"),
  };
  return { registry, admin, recorder, buyer, seller, stranger, reference, payment };
}
describe("Payment receipt attestations", function () {
  it("records different payment and payout denominations without moving funds or NFTs", async function () {
    const { registry, recorder, buyer, seller, reference, payment } = await networkHelpers.loadFixture(fixture);
    const buyerBefore = await ethers.provider.getBalance(buyer.address);
    const sellerBefore = await ethers.provider.getBalance(seller.address);
    await expect(registry.connect(recorder).recordPayment(reference, payment)).to.emit(registry, "PaymentRecorded");
    expect((await registry.records(reference)).status).to.equal(1n);
    const encoded = ethers.AbiCoder.defaultAbiCoder().encode(
      ["tuple(address assetContract,uint256 tokenId,address buyer,address seller,bytes32 paymentCurrency,uint256 paymentAmount,bytes32 payoutCurrency,uint256 payoutAmount,bytes32 providerReference,bytes32 evidenceHash)"],
      [payment],
    );
    expect((await registry.records(reference)).paymentHash).to.equal(ethers.keccak256(encoded));
    expect(await registry.sandbox()).to.equal(true);
    expect(await ethers.provider.getBalance(buyer.address)).to.equal(buyerBefore);
    expect(await ethers.provider.getBalance(seller.address)).to.equal(sellerBefore);
  });

  it("rejects a zero initial recorder and makes environment classification immutable", async function () {
    const { recorder } = await networkHelpers.loadFixture(fixture);
    await expect(ethers.deployContract("PaymentReceiptRegistry", [ethers.ZeroAddress, true])).to.be.revertedWith("Zero recorder");
    const registry = await ethers.deployContract("PaymentReceiptRegistry", [recorder.address, false]);
    expect(await registry.sandbox()).to.equal(false);
  });

  it("rejects unauthorized attestations and duplicate internal/provider references", async function () {
    const { registry, recorder, stranger, reference, payment } = await networkHelpers.loadFixture(fixture);
    await expect(registry.connect(stranger).recordPayment(reference, payment)).to.revert(ethers);
    await registry.connect(recorder).recordPayment(reference, payment);
    await expect(registry.connect(recorder).recordPayment(reference, payment)).to.be.revertedWith("Already recorded");
    await expect(registry.connect(recorder).recordPayment(ethers.id("another-order"), payment)).to.be.revertedWith("Provider reference reused");
  });

  it("validates asset, parties, amounts and evidence before consuming references", async function () {
    const { registry, recorder, buyer, reference, payment } = await networkHelpers.loadFixture(fixture);
    const cases = [
      { assetContract: ethers.ZeroAddress }, { tokenId: 0n }, { buyer: ethers.ZeroAddress },
      { seller: buyer.address }, { paymentCurrency: ethers.ZeroHash }, { payoutCurrency: ethers.ZeroHash },
      { paymentAmount: 0n }, { payoutAmount: 0n }, { providerReference: ethers.ZeroHash }, { evidenceHash: ethers.ZeroHash },
    ];
    for (const invalid of cases) {
      await expect(registry.connect(recorder).recordPayment(reference, { ...payment, ...invalid })).to.revert(ethers);
      expect((await registry.records(reference)).status).to.equal(0n);
    }
    await expect(registry.connect(recorder).recordPayment(ethers.ZeroHash, payment)).to.revert(ethers);
    await registry.connect(recorder).recordPayment(reference, payment);
  });

  for (const status of [2, 3]) it("records terminal reversal " + status + " while retaining original hash", async function () {
    const { registry, recorder, stranger, reference, payment } = await networkHelpers.loadFixture(fixture);
    const evidence = ethers.id("verified-reversal");
    await expect(registry.connect(recorder).recordReversal(reference, status, evidence)).to.be.revertedWith("Payment not reversible");
    await registry.connect(recorder).recordPayment(reference, payment);
    const original = (await registry.records(reference)).paymentHash;
    await expect(registry.connect(stranger).recordReversal(reference, status, evidence)).to.revert(ethers);
    await expect(registry.connect(recorder).recordReversal(reference, 1, evidence)).to.be.revertedWith("Invalid reversal");
    await expect(registry.connect(recorder).recordReversal(reference, status, ethers.ZeroHash)).to.be.revertedWith("Missing evidence");
    await expect(registry.connect(recorder).recordReversal(reference, status, evidence)).to.emit(registry, "PaymentReversed");
    expect((await registry.records(reference)).paymentHash).to.equal(original);
    expect((await registry.records(reference)).status).to.equal(BigInt(status));
    await expect(registry.connect(recorder).recordReversal(reference, status, evidence)).to.be.revertedWith("Payment not reversible");
  });

  it("allows recorder rotation without allowing the revoked signer to write", async function () {
    const { registry, recorder, stranger, reference, payment } = await networkHelpers.loadFixture(fixture);
    const role = await registry.RECORDER_ROLE();
    await expect(registry.connect(stranger).grantRole(role, stranger.address)).to.revert(ethers);
    await registry.revokeRole(role, recorder.address);
    await registry.grantRole(role, stranger.address);
    await expect(registry.connect(recorder).recordPayment(reference, payment)).to.revert(ethers);
    await registry.connect(stranger).recordPayment(reference, payment);
  });
});
