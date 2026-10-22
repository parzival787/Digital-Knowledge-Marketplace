import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";
const require = createRequire(import.meta.url);
test("legacy listing cancellation targets the old market and requires verified seller", async () => {
  const old = "0x"+"11".repeat(20), seller="0x"+"22".repeat(20);
  const writes=[], state=[false,"",null]; let cursor=0, verified=true, connected=seller;
  const module={exports:{}};
  vm.runInNewContext(ts.transpileModule(readFileSync(new URL("../components/marketplace/LegacyListing.tsx",import.meta.url),"utf8"),{
    compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true},
  }).outputText,{module,exports:module.exports,require(name){
    if(name==="react")return {useState(){const i=cursor++;return [state[i],v=>state[i]=v];}};
    if(name==="@/providers/AuthProvider")return {useVerifiedWallet:()=>verified};
    if(name==="@tanstack/react-query")return {useQueryClient:()=>({invalidateQueries:async()=>{}})};
    if(name==="@/lib/blockchain/contracts")return {marketplaceContract:{address:"0xcurrent",abi:[]}};
    if(name==="@/lib/blockchain/purchaseSafety")return {checkGas:async()=>({gas:120000n,maxPriorityFeePerGas:25000000000n,maxFeePerGas:45000000000n}),confirmedReceipt:async()=>{}};
    if(name==="wagmi")return {
      useAccount:()=>({address:connected,chainId:80002}),useSwitchChain:()=>({}),usePublicClient:()=>({}),
      useWriteContract:()=>({writeContractAsync:async args=>{writes.push(args);return "0xtx";}}),
      useReadContract:args=>{assert.equal(args.address,old);return {data:args.functionName==="tokenToListing"?7n:[1n,5n,seller,0,true]};},
    };
    return require(name);
  }});
  const render=()=>{cursor=0;return module.exports.default({tokenId:1n,marketAddress:old});};
  const button=tree=>tree.props.children.find(child=>child?.type==="button");
  await button(render()).props.onClick();
  assert.equal(writes.length,1);assert.equal(writes[0].gas,120000n);assert.equal(writes[0].maxPriorityFeePerGas,25000000000n);assert.equal(writes[0].address,old);
  assert.equal(writes[0].functionName,"cancelListing");assert.equal(writes[0].args[0],7n);
  verified=false;
  const denied=button(render());assert.equal(denied.props.disabled,true);
  await denied.props.onClick();assert.equal(writes.length,1);
  connected=old;assert.equal(render(),null);
});
