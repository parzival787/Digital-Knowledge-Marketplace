import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";
const require = createRequire(import.meta.url);
test("payment parsing keeps exact six/eighteen decimals and rejects rounded bids", () => {
  const module = {exports:{}};
  vm.runInNewContext(ts.transpileModule(readFileSync(new URL("../lib/blockchain/paymentToken.ts",import.meta.url),"utf8"),{
    compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}
  }).outputText,{module,exports:module.exports,require});
  const {paymentAmount} = module.exports;
  assert.equal(paymentAmount("10",6),10000000n);
  assert.equal(paymentAmount("0.01",6),10000n);
  assert.equal(paymentAmount("0.29",6),290000n);
  assert.equal(paymentAmount("10.000000000000000001",18),10000000000000000001n);
  for(const [value,decimals] of [["0.0000001",6],["1e18",18],["-1",18],["0",18],[(2n**256n).toString(),0]])
    assert.throws(()=>paymentAmount(value,decimals));
});
