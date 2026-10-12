import assert from "node:assert/strict";
import test from "node:test";
import { checkListing, checkUnlisted, checkGas, confirmedReceipt } from "../lib/blockchain/purchaseSafety.ts";

const contract = { address: "0xmarket", abi: [] };
const buyer = "0xbuyer";
test("listing is blocked by any current or legacy active listing and failed reads", async()=>{
  const markets=[contract,{address:"0xlegacy",abi:[]}];
  await assert.rejects(checkUnlisted({getBlockNumber:async()=>11n,readContract:async args=>args.address==="0xlegacy"},markets,1n),/Cancel/);
  await assert.rejects(checkUnlisted({getBlockNumber:async()=>11n,readContract:async()=>{throw new Error("RPC failed");}},markets,1n));
  await checkUnlisted({getBlockNumber:async()=>11n,readContract:async()=>false},markets,1n);
});
function client() {
  const state = { listing: [1n, 5n, "0xseller", 0, true], active: true, purchased: false, id: 2n };
  return { state, getBlockNumber: async () => 11n,
    readContract: async ({ functionName, blockNumber }) => {
      assert.equal(blockNumber, 11n);
      return { tokenToListing: state.id, listings: state.listing, getAsset: [0,0,0,0,0,0,state.active], hasPurchased: state.purchased }[functionName];
    },
  };
}

test("fresh listing rejects relisting, changed price, cancellation, inactive asset and existing access", async () => {
  for (const change of [s => s.id=3n, s => s.listing[1]=6n, s => s.listing[4]=false, s => s.active=false, s => s.purchased=true]) {
    const c = client();
    await checkListing(c, contract, contract, 1n, buyer, 2n, 5n);
    change(c.state);
    await assert.rejects(checkListing(c, contract, contract, 1n, buyer, 2n, 5n));
  }
});

test("gas estimate includes a 20 percent margin and fails before signing", async () => {
  const c = { estimateContractGas: async () => 100n, estimateFeesPerGas: async () => ({ maxFeePerGas: 2n }), getBalance: async () => 239n };
  await assert.rejects(checkGas(c, contract, "buyAsset", [2n], buyer), /POL/);
  c.getBalance = async () => 240n;
  await checkGas(c, contract, "buyAsset", [2n], buyer);
});

test("two-block receipt verification rejects reorg, disappearance, revert, shallow depth and replacement", async () => {
  const receipt = { transactionHash: "0xtx", status: "success", blockNumber: 10n, blockHash: "0xblock" };
  const make = () => ({
    waitForTransactionReceipt: async args => { assert.equal(args.confirmations, 2); return receipt; },
    getBlock: async () => ({ hash: "0xblock" }), getTransactionReceipt: async () => receipt, getBlockNumber: async () => 11n,
  });
  await confirmedReceipt(make(), "0xtx");
  for (const change of [
    c => c.getBlock = async () => ({ hash: "0xreorg" }),
    c => c.getTransactionReceipt = async () => { throw new Error("disappeared"); },
    c => c.getTransactionReceipt = async () => ({ ...receipt, status: "reverted" }),
    c => c.getBlockNumber = async () => 10n,
    c => c.waitForTransactionReceipt = async () => ({ ...receipt, transactionHash: "0xcancel" }),
  ]) {
    const c = make(); change(c);
    await assert.rejects(confirmedReceipt(c, "0xtx"));
  }
});


test("an old marketplace entitlement blocks a duplicate purchase", async () => {
  const c = client();
  const read = c.readContract;
  c.readContract = async args => args.address === "0xold" ? true : read(args);
  await assert.rejects(checkListing(c, contract, contract, 1n, buyer, 2n, 5n,
    [{ address: "0xold", abi: [] }]), /already owns or has access/);
  c.readContract = async args => { if (args.address === "0xold") throw new Error("RPC unavailable"); return read(args); };
  await assert.rejects(checkListing(c, contract, contract, 1n, buyer, 2n, 5n,
    [{ address: "0xold", abi: [] }]), /RPC unavailable/);
});
