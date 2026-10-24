import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

test("old marketplace entitlements apply only to the preserved six-token prefix", () => {
  const module = { exports: {} };
  vm.runInNewContext(ts.transpileModule(readFileSync(new URL("../lib/blockchain/contracts.ts", import.meta.url), "utf8"), {
    compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.CommonJS, esModuleInterop: true },
  }).outputText, { module, exports: module.exports, require(name) {
    if (name === "@/contracts/addresses") return {
      CONTRACTS: { Marketplace: "0xcurrent", KnowledgeAsset: "0xregistry", RoyaltySplitter: "0xsplit", MockUSDC: "0xtoken" },
      LEGACY_MARKETPLACES: ["0xold"], LEGACY_TOKEN_LIMIT: 6n,
    };
    return { abi: [] };
  } });
  const { marketsForToken } = module.exports;
  assert.equal(marketsForToken(1n).length, 2);
  assert.equal(marketsForToken(6n)[1].address, "0xold");
  assert.equal(marketsForToken(7n).length, 1);
  assert.equal(marketsForToken(7n)[0].address, "0xcurrent");
});
