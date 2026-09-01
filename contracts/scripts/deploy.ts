import { network } from "hardhat";
import fs from "fs";

async function main() {
    const { ethers } = await network.connect();

    const [deployer] = await ethers.getSigners();

    console.log("Deployer:", deployer.address);

    // ----------------------------------------------------
    // EXISTING CONTRACTS
    // DO NOT REDEPLOY THESE
    // ----------------------------------------------------

    const MOCK_USDC =
        "0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719";

    const KNOWLEDGE_ASSET =
        "0x2C16409A3db9880f9A70e71B5b131A17db533Fc9";

    console.log("Existing MockUSDC:", MOCK_USDC);
    console.log("Existing KnowledgeAsset:", KNOWLEDGE_ASSET);

    // ----------------------------------------------------
    // Deploy NEW RoyaltySplitter
    // ----------------------------------------------------

    const RoyaltySplitter =
        await ethers.getContractFactory("RoyaltySplitter");

    const royaltySplitter =
        await RoyaltySplitter.deploy(
            MOCK_USDC,
            deployer.address,
            500
        );

    await royaltySplitter.waitForDeployment();

    const royaltySplitterAddress =
        await royaltySplitter.getAddress();

    console.log(
        "NEW RoyaltySplitter:",
        royaltySplitterAddress
    );

    // ----------------------------------------------------
    // Deploy NEW Marketplace
    // Uses EXISTING KnowledgeAsset
    // Uses NEW RoyaltySplitter
    // Uses EXISTING MockUSDC
    // ----------------------------------------------------

    const Marketplace =
        await ethers.getContractFactory("Marketplace");

    const marketplace =
        await Marketplace.deploy(
            KNOWLEDGE_ASSET,
            royaltySplitterAddress,
            MOCK_USDC
        );

    await marketplace.waitForDeployment();

    const marketplaceAddress =
        await marketplace.getAddress();

    console.log(
        "NEW Marketplace:",
        marketplaceAddress
    );

    // ----------------------------------------------------
    // Configure RoyaltySplitter
    // ----------------------------------------------------

    const updateTx =
        await royaltySplitter.updateMarketplace(
            marketplaceAddress
        );

    await updateTx.wait();

    console.log("RoyaltySplitter Marketplace configured.");

    // ----------------------------------------------------
    // Verify configuration
    // ----------------------------------------------------

    console.log(
        "Marketplace KnowledgeAsset:",
        await marketplace.knowledgeAsset()
    );

    console.log(
        "Marketplace RoyaltySplitter:",
        await marketplace.royaltySplitter()
    );

    console.log(
        "Marketplace USDC:",
        await marketplace.usdc()
    );

    console.log(
        "RoyaltySplitter Marketplace:",
        await royaltySplitter.marketplace()
    );

    // ----------------------------------------------------
    // Save deployment
    // ----------------------------------------------------

    const addresses = {
        deployer: deployer.address,
        MockUSDC: MOCK_USDC,
        KnowledgeAsset: KNOWLEDGE_ASSET,
        RoyaltySplitter: royaltySplitterAddress,
        Marketplace: marketplaceAddress
    };

    fs.writeFileSync(
        "./deployment.json",
        JSON.stringify(addresses, null, 2)
    );

    console.log("\ndeployment.json generated.");
    console.log("\nDeployment Complete");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});