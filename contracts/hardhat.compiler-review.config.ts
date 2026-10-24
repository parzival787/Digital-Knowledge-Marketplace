import config from "./hardhat.config.js";

// Isolated compiler experiment; the deployment configuration stays pinned.
export default {
  ...config,
  solidity: {
    version: "0.8.37",
    settings: { optimizer: { enabled: true, runs: 200 }, evmVersion: "shanghai" },
  },
  paths: { cache: "./cache/compiler-review", artifacts: "./artifacts/compiler-review" },
};
