import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";
const require = createRequire(import.meta.url);
test("seller preference must be saved before withdrawal; only staging sessions open", async () => {
  const state = ["EUR", "USDC", true, false, "", ""];
  let cursor = 0, verified = true, opened = 0;
  let session = { widget_url: "https://global-stg.transak.com?sessionId=sell", environment: "staging", automatic_payout_enabled: false };
  const calls = [], module = { exports: {} };
  const code = ts.transpileModule(readFileSync(new URL("../components/marketplace/SellerPayout.tsx", import.meta.url), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, URL, window: { location: { assign() { opened++; } } }, require(name) {
    if (name === "react") return { useEffect() {}, useState() { const i = cursor++; return [state[i], value => state[i] = value]; } };
    if (name === "@/providers/AuthProvider") return { useVerifiedWallet: () => verified };
    if (name === "@/lib/api/client") return { api: async (path, options) => {
      calls.push(path);
      if (path.endsWith("/payout-preference")) {
        assert.equal(options.method, "PUT");
        assert.deepEqual(JSON.parse(options.body), { currency: "EUR" });
        return { currency: "EUR", automatic_payout_enabled: false };
      }
      assert.equal(options.method, "POST");
      assert.equal(options.body, undefined);
      return session;
    }};
    return require(name);
  }});
  function render() { cursor = 0; return module.exports.default(); }
  function button(label) { return render().props.children.find(child => child?.type === "button" && child.props.children === label); }
  assert.equal(button("Open Transak withdrawal sandbox").props.disabled, true);
  await button("Save preference").props.onClick();
  assert.equal(state[1], "EUR");
  assert.match(state[4], /not enabled/);
  assert.equal(button("Open Transak withdrawal sandbox").props.disabled, false);
  await button("Open Transak withdrawal sandbox").props.onClick();
  assert.equal(opened, 1);
  for (const invalid of [{ environment: "production" }, { automatic_payout_enabled: true }, { widget_url: "https://attacker.invalid" }]) {
    session = { widget_url: "https://global-stg.transak.com?sessionId=sell", environment: "staging", automatic_payout_enabled: false, ...invalid };
    await button("Open Transak withdrawal sandbox").props.onClick();
    assert.equal(opened, 1); assert.ok(state[5]);
  }
  verified = false;
  assert.equal(button("Open Transak withdrawal sandbox").props.disabled, true);
  assert.ok(calls.every(path => path.startsWith("/api/payments/transak/payout-")));
});
