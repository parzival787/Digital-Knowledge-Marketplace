import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";
const require = createRequire(import.meta.url);
test("Transak only opens staging and never confirms a marketplace payment", async () => {
  const state = [true, false, ""];
  let cursor = 0, opened = [], calls = [];
  let session = { widget_url: "https://global-stg.transak.com?sessionId=test", environment: "staging", grants_access: false };
  const module = { exports: {} };
  const code = ts.transpileModule(readFileSync(new URL("../components/marketplace/TransakFunding.tsx", import.meta.url), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, URL, window: { location: { assign(url) { opened.push(url); } } }, require(name) {
    if (name === "react") return { useEffect() {}, useState() { const i = cursor++; return [state[i], value => state[i] = value]; } };
    if (name === "@/lib/api/client") return { api: async (path, options) => { calls.push(path); assert.equal(options.method, "POST"); return session; } };
    return require(name);
  }});
  function render() { cursor = 0; return module.exports.default(); }
  function button() { return render().props.children.find(child => child?.type === "button"); }
  await button().props.onClick();
  assert.equal(opened.length, 1);
  for (const invalid of [
    { widget_url: "https://global.transak.com?sessionId=test" },
    { environment: "production" }, { grants_access: true },
    { widget_url: "https://global-stg.transak.com.attacker.invalid" },
  ]) {
    session = { widget_url: "https://global-stg.transak.com?sessionId=test", environment: "staging", grants_access: false, ...invalid };
    await button().props.onClick();
    assert.equal(opened.length, 1);
    assert.ok(state[2]);
  }
  assert.ok(calls.every(path => path === "/api/payments/transak/session"));
  state[0] = false;
  assert.equal(button().props.disabled, true);
});
