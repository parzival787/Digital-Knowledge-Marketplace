import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { polygonAmoy } from "wagmi/chains";

export const config = getDefaultConfig({
  appName: "Decentralized Knowledge Marketplace",

  projectId: process.env.NEXT_PUBLIC_WC_PROJECT_ID || "",

  chains: [polygonAmoy],

  ssr: true,
});