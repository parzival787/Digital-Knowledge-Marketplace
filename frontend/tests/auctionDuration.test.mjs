import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

const module = { exports: {} };
vm.runInNewContext(ts.transpileModule(readFileSync(new URL("../lib/blockchain/auctionDuration.ts", import.meta.url), "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
}).outputText, { module, exports: module.exports });
const { auctionDurationSeconds } = module.exports;

test("auction durations convert both units with inclusive two-minute and 30-day bounds", () => {
  for (const [value, unit, expected] of [["2", "minutes", 120n], ["90", "minutes", 5400n], ["1", "hours", 3600n], ["24", "hours", 86400n], ["720", "hours", 2592000n], ["43200", "minutes", 2592000n]]) {
    assert.equal(auctionDurationSeconds(value, unit), expected);
  }
  for (const [value, unit] of [["1", "minutes"], ["0", "hours"], ["-2", "minutes"], ["2.5", "minutes"], ["721", "hours"], ["43201", "minutes"], ["", "minutes"], ["NaN", "hours"], ["Infinity", "hours"]]) {
    assert.throws(() => auctionDurationSeconds(value, unit), /2 minutes to 720 hours/);
  }
});
