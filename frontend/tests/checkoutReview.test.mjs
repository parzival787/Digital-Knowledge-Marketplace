import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";

const require = createRequire(import.meta.url);
test("checkout shows the persisted total before opening Razorpay and reuses the order", async () => {
  const order = { order_id: "test-order", status: "PENDING", amount_usdc: 5,
    fiat_amount: 42750, fiat_currency: "INR", exchange_rate: "85.5",
    checkout_key: "rzp_test_example", provider_order_id: "order_test" };
  const state = [{ fiat_configured: true }, null, "upi", true, false, "", false];
  let cursor = 0, creates = 0, opens = 0, options, latest = order, failLookup = false;
  const module = { exports: {} };
  const code = ts.transpileModule(readFileSync(new URL("../components/marketplace/Web2Checkout.tsx", import.meta.url), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, window: {
    Razorpay: function(value) { options = value; return { open() { opens++; } }; },
  }, require(name) {
    if (name === "react") return { useEffect() {}, useState() {
      const index = cursor++; return [state[index], value => { state[index] = value; }];
    } };
    if (name === "@/lib/api/client") return { api: async (path, request) => {
      if (path === "/api/payments/test-order") {
        assert.equal(request.method, "GET");
        if (failLookup) throw new Error("Status unavailable");
        return { order: latest };
      }
      assert.equal(path, "/api/payments/create");
      assert.equal(JSON.parse(request.body).payment_method, "upi");
      creates++; return { order };
    } };
    if (name === "@/providers/AuthProvider") return { useAuth: () => ({ user: { id: 1 } }) };
    if (name === "@tanstack/react-query") return { useQueryClient: () => ({}) };
    if (name === "next/script") return () => null;
    return require(name);
  } });
  function render() { cursor = 0; return module.exports.default({ tokenId: 1n, buyer: "0xbuyer", canStart: true }); }
  function button(tree, label) {
    if (!tree || typeof tree !== "object") return null;
    if (tree.type === "button" && tree.props.children === label) return tree;
    for (const child of [tree.props?.children].flat(Infinity)) {
      const match = button(child, label); if (match) return match;
    }
    return null;
  }
  await button(render(), "Review test payment").props.onClick();
  assert.equal(creates, 1);
  assert.equal(opens, 0, "preparing a quote must not open payment");
  const review = render();
  assert.match(JSON.stringify(review), /427.50/);
  await button(review, "Continue to test payment").props.onClick();
  assert.equal(creates, 1, "confirmation must reuse the reviewed order");
  assert.equal(opens, 1);
  assert.equal(options.amount, 42750, "do not add a buyer DKM surcharge");
  assert.equal(options.order_id, order.provider_order_id);
  for (const change of [
    { fiat_amount: 45000 }, { fiat_currency: "USD" }, { exchange_rate: "90" },
    { amount_usdc: 6 }, { provider_order_id: "order_changed" }, { checkout_key: "rzp_test_changed" },
    { recovery_status: "REVIEW_REQUIRED" }, { recovery_status: "REFUNDED" },
    { status: "PROVIDER_CONFIRMED" }, { provider_payment_id: "pay_already_captured" },
  ]) {
    state[1] = order; state[4] = false; latest = { ...order, ...change };
    await button(render(), "Continue to test payment").props.onClick();
    assert.equal(opens, 1, `must not open stale checkout: ${JSON.stringify(change)}`);
    assert.equal(state[1], latest);
    assert.ok(state[5], "explain why checkout stopped");
  }
  state[1] = order; state[4] = false; failLookup = true;
  await button(render(), "Continue to test payment").props.onClick();
  assert.equal(opens, 1, "failed status lookup must stop payment");
  failLookup = false; latest = { ...order, fiat_amount: 45000 }; state[1] = latest;
  await button(render(), "Continue to test payment").props.onClick();
  assert.equal(opens, 2, "a newly reviewed total can proceed");
  assert.equal(options.amount, 45000);
});
