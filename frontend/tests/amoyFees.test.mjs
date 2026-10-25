import assert from "node:assert/strict";
import test from "node:test";
import { amoyFees } from "../lib/blockchain/amoyFees.ts";

const gwei = 1_000_000_000n;
function client(tip = 1n, cap = 10n) {
  return {
    getChainId: async () => 80002,
    getBlock: async () => ({ baseFeePerGas: 10n * gwei }),
    estimateFeesPerGas: async () => ({ maxPriorityFeePerGas: tip * gwei, maxFeePerGas: cap * gwei }),
  };
}
test("Amoy mint replaces the rejected 1 gwei tip and raises the fee cap", async () => {
  assert.deepEqual(await amoyFees(client()), { maxPriorityFeePerGas: 25n * gwei, maxFeePerGas: 45n * gwei });
});
test("higher network estimates remain intact", async () => {
  assert.deepEqual(await amoyFees(client(40n, 100n)), { maxPriorityFeePerGas: 40n * gwei, maxFeePerGas: 100n * gwei });
});
test("wrong network, absent base fee and RPC failures block signing", async () => {
  await assert.rejects(amoyFees({ ...client(), getChainId: async () => 1 }), /Amoy/);
  await assert.rejects(amoyFees({ ...client(), getBlock: async () => ({ baseFeePerGas: null }) }), /unavailable/);
  await assert.rejects(amoyFees({ ...client(), estimateFeesPerGas: async () => { throw new Error("RPC failed"); } }), /RPC failed/);
});
