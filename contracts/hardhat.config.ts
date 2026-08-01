import { defineConfig } from "hardhat/config";
import toolbox from "@nomicfoundation/hardhat-toolbox-mocha-ethers";
import dotenv from "dotenv";

dotenv.config();

export default defineConfig({
  plugins: [toolbox],

  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },

  networks: {
    hardhatMainnet: {
      type: "edr-simulated",
      chainType: "l1",
    },

    polygonAmoy: {
      type: "http",
      chainType: "l1",
      url: process.env.ALCHEMY_AMOY_URL!,
      accounts: process.env.PRIVATE_KEY
        ? [process.env.PRIVATE_KEY] : [],
    },
  },
});