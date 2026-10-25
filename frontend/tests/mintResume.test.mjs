import assert from "node:assert/strict";
import test from "node:test";
import {readFileSync} from "node:fs";
import {createRequire} from "node:module";
import vm from "node:vm";
import ts from "typescript";
const require=createRequire(import.meta.url);

test("mint resume uses the browser query even without server page props", () => {
  const module={exports:{}};
  vm.runInNewContext(ts.transpileModule(readFileSync(new URL("../app/mint/page.tsx",import.meta.url),"utf8"),{
    compilerOptions:{target:ts.ScriptTarget.ES2020,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true},
  }).outputText,{module,exports:module.exports,require(name){
    if(name==="next/navigation")return {useSearchParams:()=>new URLSearchParams("upload=saved-upload-123")};
    if(name==="next/link")return ()=>null;
    if(name.startsWith("@/"))return {AccountGate:"account-gate"};
    if(name==="wagmi")return {};
    return require(name);
  }});
  const suspense=module.exports.default();
  const main=suspense.props.children.type();
  const gate=main.props.children.find(child=>child?.type==="account-gate");
  assert.equal(gate.props.children.props.resume,"saved-upload-123");
});
