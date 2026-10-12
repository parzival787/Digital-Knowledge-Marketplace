import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";
const require = createRequire(import.meta.url);

test("old auction reads, approval, bid, finalization and refund target the selected market", async () => {
  const old = "0x" + "11".repeat(20), current = "0x" + "22".repeat(20), buyer = "0x" + "33".repeat(20);
  const writes = [], reads = [], state = [2n, "5", "24", "", "", false, null, 1];
  let cursor = 0;
  const module = { exports: {} };
  const auction = [1n, 1000000n, 0n, current, current, true, false, 0, 100];
  vm.runInNewContext(ts.transpileModule(readFileSync(new URL("../components/marketplace/AuctionPanel.tsx", import.meta.url), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
  }).outputText, { module, exports: module.exports, require(name) {
    if (name === "react") return { useEffect() {}, useState() { const i=cursor++; return [state[i], v => state[i]=v]; } };
    if (name === "@/lib/api/capabilities") return { usePaymentCapabilities: () => ({data:{markets:[{address:old,token_address:current,decimals:6,symbol:"MockUSDC",paused:false}]},isError:false}), marketRouteAvailable: () => true };
    if (name === "@/lib/blockchain/paymentToken") return {paymentToken:profile=>({address:profile.token_address,abi:[]}),paymentAmount:(value,decimals)=>require("viem").parseUnits(value,decimals)};
    if (name === "@/providers/AuthProvider") return { useVerifiedWallet: () => true };
    if (name === "@tanstack/react-query") return { useQueryClient: () => ({ invalidateQueries: async () => {} }) };
    if (name === "next/link") return () => null;
    if (name === "@/lib/blockchain/contracts") return { marketplaceContract: {address:current,abi:[]}, mockUSDCContract:{address:"0xtoken",abi:[]} };
    if (name === "@/lib/blockchain/purchaseSafety") return { checkGas:async()=>{}, confirmedReceipt:async()=>{}, PurchaseCheckError:Error };
    if (name === "wagmi") return {
      useAccount: () => ({address:buyer,chainId:80002}), useSwitchChain: () => ({}),
      useReadContract: args => { reads.push(args); return {data:args.functionName === "auctions" ? auction : 1n}; },
      usePublicClient: () => ({ readContract:async args => args.functionName === "balanceOf" ? 10000000n : 0n }),
      useWriteContract: () => ({ writeContractAsync:async args => { writes.push(args); return "0xtx"; } }),
    };
    return require(name);
  }});
  const render = () => { cursor=0; return module.exports.default({tokenId:1n,auctionId:2n,canCreate:false,price:1n,marketAddress:old}); };
  function find(tree,label) {
    if (!tree || typeof tree !== "object") return null;
    if (tree.type === "button" && tree.props.children === label) return tree;
    for (const child of [tree.props?.children].flat(Infinity)) { const match=find(child,label); if(match)return match; }
    return null;
  }
  await find(render(),"Place bid").props.onClick();
  assert.equal(writes[0].functionName,"approve"); assert.equal(writes[0].args[0],old);
  assert.equal(writes[1].functionName,"placeBid"); assert.equal(writes[1].address,old);
  state[7]=101;
  await find(render(),"Finalize auction").props.onClick();
  await find(render(),"Withdraw bid refund").props.onClick();
  assert.equal(writes[2].functionName,"endAuction"); assert.equal(writes[2].address,old);
  assert.equal(writes[3].functionName,"withdrawRefund"); assert.equal(writes[3].address,old);
  assert.ok(reads.every(read => read.address === old));
});
