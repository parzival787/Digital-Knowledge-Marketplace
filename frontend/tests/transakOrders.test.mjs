import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";
const require = createRequire(import.meta.url);
test("sandbox history verifies through backend, preserves amounts, and reports failures", async () => {
  const receipt = { order_id: "00000000-0000-0000-0000-000000000001", status: "COMPLETED",
    fiat_currency: "USD", fiat_amount: "100", amount_paid: "100", provider_fee: "3.99",
    crypto_amount: "96.01", transaction_hash: null };
  const state = [[receipt], receipt.order_id, false, ""];
  let cursor = 0, fail = false;
  const calls = [], module = { exports: {} };
  const code = ts.transpileModule(readFileSync(new URL("../components/marketplace/TransakOrders.tsx", import.meta.url), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require(name) {
    if (name === "react") return { useEffect() {}, useState() { const i = cursor++; return [state[i], value => state[i] = value]; } };
    if (name === "@/lib/api/client") return { api: async (path, options) => {
      calls.push(path);
      if (fail) throw new Error("Provider unavailable");
      if (path.endsWith("/refresh")) {
        assert.equal(options.method, "POST");
        assert.equal(JSON.parse(options.body).order_id, receipt.order_id);
        return { ...receipt, grants_access: false };
      }
      return { orders: [receipt] };
    }};
    return require(name);
  }});
  function render() { cursor = 0; return module.exports.default(); }
  function find(node, type) {
    if (!node || typeof node !== "object") return null;
    if (node.type === type) return node;
    for (const child of [node.props?.children].flat(Infinity)) { const match = find(child, type); if (match) return match; }
    return null;
  }
  find(render(), "form").props.onSubmit({ preventDefault() {} });
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(calls, ["/api/payments/transak/orders/refresh", "/api/payments/transak/orders"]);
  const view = JSON.stringify(render());
  assert.match(view, /3.99/);
  assert.match(view, /100/);
  assert.doesNotMatch(view, /103.99/);
  assert.match(view, /not independent blockchain verification/);
  receipt.verification_state = "review_required";
  receipt.observed_status = "PROCESSING";
  receipt.refresh_error = "Automatic provider refresh failed";
  assert.match(JSON.stringify(render()), /Review required/);
  assert.match(JSON.stringify(render()), /Automatic provider refresh failed/);
  fail = true; state[1] = receipt.order_id;
  find(render(), "form").props.onSubmit({ preventDefault() {} });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(state[0].length, 1);
  assert.equal(state[2], false);
  assert.ok(state[3]);
});
