import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

test("payment availability fails closed on unknown route, wrong token/network and paused purchases", () => {
  const module = { exports: {} };
  const code = ts.transpileModule(readFileSync(new URL("../lib/api/capabilities.ts", import.meta.url), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require: () => ({}) });
  const available = module.exports.marketRouteAvailable;
  const data = { chain_id: 80002, routes: { fixed_price: { enabled: true }, auction: { enabled: true } },
    markets: [{ address: "0xABC", token_address: "0xDEF", paused: false }] };
  assert.equal(available(undefined, "fixed_price", "0xabc", "0xdef"), false);
  assert.equal(available(data, "fixed_price", "0xabc", "0xdef"), true);
  assert.equal(available(data, "fixed_price", "0xother", "0xdef"), false);
  assert.equal(available(data, "fixed_price", "0xabc", "0xother"), false);
  assert.equal(available({...data,chain_id:1}, "fixed_price", "0xabc", "0xdef"), false);
  data.markets[0].paused = true;
  assert.equal(available(data, "fixed_price", "0xabc", "0xdef"), false);
  assert.equal(available(data, "auction", "0xabc", "0xdef"), true);
  data.routes.auction.enabled = false;
  assert.equal(available(data, "auction", "0xabc", "0xdef"), false);
});
