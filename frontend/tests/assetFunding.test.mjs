import assert from "node:assert/strict";
import test from "node:test";
import {readFileSync} from "node:fs";
import {createRequire} from "node:module";
import vm from "node:vm";
import ts from "typescript";
const require=createRequire(import.meta.url);
test("funding review precedes hosted checkout and only verified bound delivery reports funding",async()=>{
  const state=[null,"USD","credit_debit_card",null,"provider-order","","",false];let cursor=0,opened=0;
  const quote={id:"funding",terms:{buyer_token_total_base_units:"10000000000000000001"},quote:{fiatAmount:"11.46",fiatCurrency:"USD",cryptoAmount:"10.000000000000000001",totalFee:"1.46",fees:[],freshness_seconds:60}};
  let url="https://global-stg.transak.com?session=test",funded=false,asset="9007199254740993";const calls=[];const module={exports:{}};
  vm.runInNewContext(ts.transpileModule(readFileSync(new URL("../components/marketplace/AssetFunding.tsx",import.meta.url),"utf8"),{
    compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}
  }).outputText,{module,exports:module.exports,URL,window:{location:{assign(){opened++;}}},require(name){
    if(name==="react")return {useEffect(){},useState(){const i=cursor++;return [state[i],v=>state[i]=v];}};
    if(name==="@/lib/api/client")return {api:async(path,options)=>{calls.push(path);
      if(path.endsWith("/session"))return {widget_url:url};
      if(path.endsWith("/refresh"))return {funding_id:"funding",asset_token_id:asset,funding_state:funded?"wallet_funded":"provider_verified"};
      assert.equal(JSON.parse(options.body).token_id,"9007199254740993");return quote;
    }};
    return require(name);
  }});
  const render=()=>{cursor=0;return module.exports.default({tokenId:9007199254740993n});};
  function find(tree,label){if(!tree||typeof tree!=="object")return null;if(tree.type==="button"&&tree.props.children===label)return tree;for(const c of [tree.props?.children].flat(Infinity)){const found=find(c,label);if(found)return found;}return null;}
  await find(render(),"Get funding quote").props.onClick();assert.equal(opened,0);assert.equal(state[3].id,"funding");
  await find(render(),"Accept funding quote and open sandbox").props.onClick();assert.equal(opened,1);
  url="https://attacker.invalid";await find(render(),"Accept funding quote and open sandbox").props.onClick();assert.equal(opened,1);assert.ok(state[6]);
  await find(render(),"Verify provider and blockchain delivery").props.onClick();assert.match(state[5],/not verified/);
  funded=true;await find(render(),"Verify provider and blockchain delivery").props.onClick();assert.match(state[5],/buy separately/);
  state[3]=null;asset="42";await find(render(),"Verify provider and blockchain delivery").props.onClick();assert.equal(state[5],"");assert.match(state[6],/does not fund this asset/);
  assert.ok(calls.every(p=>p.startsWith("/api/payments/transak/")));
});
