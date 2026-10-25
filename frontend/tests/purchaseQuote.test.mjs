import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

test("quote acceptance rejects changed totals, expiry and deployment before wallet execution", async () => {
  const module = { exports: {} }; let calls = 0, response;
  const code = ts.transpileModule(readFileSync(new URL("../lib/api/quotes.ts", import.meta.url), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS },
  }).outputText;
  vm.runInNewContext(code, {module,exports:module.exports,require:()=>({api:async()=>{calls++;return response;}})});
  const quote = {id:"q", expires_at:new Date(Date.now()+60000).toISOString(), accepted_at:null, terms:{
    chain_id:80002, decimals:6, buyer:"0xbuyer", marketplace:"0xmarket", payment_token:"0xtoken", token_id:"1", listing_id:"2",
    asset_price_base_units:"5000000", buyer_token_total_base_units:"5000000", buyer_dkm_fee_base_units:"0" }};
  const expected = {buyer:"0xbuyer",market:"0xmarket",token:"0xtoken",tokenId:1n,listingId:2n,amount:5000000n,decimals:6};
  response = {...quote,accepted_at:new Date().toISOString()};
  await module.exports.acceptPurchaseQuote(quote,expected); assert.equal(calls,1);
  for(const changed of [{chain_id:1},{marketplace:"other"},{buyer:"other"},{buyer_dkm_fee_base_units:"250000"},{buyer_token_total_base_units:"5250000"},{listing_id:"3"}]) {
    await assert.rejects(module.exports.acceptPurchaseQuote({...quote,terms:{...quote.terms,...changed}},expected));
  }
  await assert.rejects(module.exports.acceptPurchaseQuote({...quote,expires_at:"2000-01-01"},expected));
  assert.equal(calls,1);
  response={...response,terms:{...response.terms,platform_fee_base_units:"999"}};
  await assert.rejects(module.exports.acceptPurchaseQuote(quote,expected),/changed/);
  const eighteen = {...quote,terms:{...quote.terms,decimals:18,asset_price_base_units:"5000000000000000001",buyer_token_total_base_units:"5000000000000000001"}};
  response={...eighteen,accepted_at:new Date().toISOString()};
  await module.exports.acceptPurchaseQuote(eighteen,{...expected,decimals:18,amount:5000000000000000001n});
  await assert.rejects(module.exports.acceptPurchaseQuote(eighteen,{...expected,amount:5000000000000000001n}));
});
