import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";
const require = createRequire(import.meta.url);

test("every marketplace hook forwards estimated gas and fees and blocks failed estimates", async () => {
  const writes = [], checks = [];
  const fees = { gas: 123456n, maxFeePerGas: 45000000000n, maxPriorityFeePerGas: 25000000000n };
  let fail = false;
  const module = { exports: {} };
  const contract = { address: "0xmarket", abi: [] };
  vm.runInNewContext(ts.transpileModule(readFileSync(new URL("../lib/blockchain/useMarketplace.ts", import.meta.url), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS },
  }).outputText, { module, exports: module.exports, require(name) {
    if (name === "@/lib/blockchain/contracts") return { marketplaceContract: contract, knowledgeAssetContract: contract, mockUSDCContract: contract };
    if (name === "@/lib/blockchain/purchaseSafety") return { checkGas: async (...args) => {
      checks.push(args);
      if (fail) throw new Error("estimate failed");
      return fees;
    } };
    if (name === "wagmi") return {
      useAccount: () => ({ address: "0xbuyer" }), usePublicClient: () => ({}),
      useWriteContract: () => ({ writeContractAsync: async args => { writes.push(args); return "0xtx"; } }),
    };
    return require(name);
  } });
  const market = module.exports.useMarketplaceWrite();
  const usdc = module.exports.useUSDCWrite("0xtoken");
  const actions = [
    () => market.approveNFT(1n),
    () => market.listFixedPrice(1n, 10000n, []),
    () => market.buyAsset(2n, "0xbuyer"),
    () => usdc.approveMarketplace(10000n, "0xbuyer"),
  ];
  for (const action of actions) await action();
  assert.equal(writes.length, 4);
  for (const write of writes) {
    for (const [key, value] of Object.entries(fees)) assert.equal(write[key], value);
    assert.equal(write.account, "0xbuyer");
    assert.equal(write.chainId, 80002);
  }
  assert.deepEqual(checks.map(args => args[2]), ["approve", "listFixedPrice", "buyAsset", "approve"]);
  fail = true;
  for (const action of actions) await assert.rejects(action(), /estimate failed/);
  assert.equal(writes.length, 4);
});
