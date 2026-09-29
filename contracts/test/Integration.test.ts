import { expect } from "chai";
import { network } from "hardhat";

describe("Integration", function () {

    let ethers: any;

    let owner: any;
    let seller: any;
    let buyer: any;
    let professor: any;
    let university: any;
    let treasury: any;

    let usdc: any;
    let knowledgeAsset: any;
    let royaltySplitter: any;
    let marketplace: any;

    let PRICE: bigint;

    function royaltyRecipients(
        professor: any,
        university: any
    ) {
        return [
            {
                wallet: professor.address,
                shareBps: 1000
            },
            {
                wallet: university.address,
                shareBps: 500
            }
        ];
    }

    beforeEach(async function () {

        ({ ethers } = await network.connect());

        PRICE = ethers.parseUnits("100", 6);

        [
            owner,
            seller,
            buyer,
            professor,
            university,
            treasury
        ] = await ethers.getSigners();

        /*--------------------------------------------------
                        Mock USDC
        --------------------------------------------------*/

        const MockERC20 =
            await ethers.getContractFactory(
                "MockERC20"
            );

        usdc =
            await MockERC20.deploy(
                "Mock USD Coin",
                "USDC",
                6
            );

        await usdc.waitForDeployment();

        /*--------------------------------------------------
                    KnowledgeAsset
        --------------------------------------------------*/

        const KnowledgeAsset =
            await ethers.getContractFactory(
                "KnowledgeAsset"
            );

        knowledgeAsset =
            await KnowledgeAsset.deploy();

        await knowledgeAsset.waitForDeployment();

        /*--------------------------------------------------
                    RoyaltySplitter
        --------------------------------------------------*/

        const RoyaltySplitter =
            await ethers.getContractFactory(
                "RoyaltySplitter"
            );

        royaltySplitter =
            await RoyaltySplitter.deploy(

                await usdc.getAddress(),

                treasury.address,

                500

            );

        await royaltySplitter.waitForDeployment();

        /*--------------------------------------------------
                        Marketplace
        --------------------------------------------------*/

        const Marketplace =
            await ethers.getContractFactory(
                "Marketplace"
            );

        marketplace =
            await Marketplace.deploy(

                await knowledgeAsset.getAddress(),

                await royaltySplitter.getAddress(),

                await usdc.getAddress()

            );

        await marketplace.waitForDeployment();

        /*--------------------------------------------------
            Authorize Marketplace as RoyaltySplitter's caller.
            Without this, every buyAsset/endAuction call reverts
            with NotMarketplace — RoyaltySplitter now only accepts
            distributeRoyalty calls from this configured address.
        --------------------------------------------------*/

        await royaltySplitter.updateMarketplace(
            await marketplace.getAddress()
        );

    });

describe("Fixed Price Workflow", function () {

it("completes an entire NFT sale", async function () {

    /*------------------------------------
            Seller mints NFT
    ------------------------------------*/

    await knowledgeAsset
        .connect(seller)
        .mint(

            "ipfs://dataset",

            "ipfs://metadata",

            PRICE,

            0,

            95

        );

    expect(

        await knowledgeAsset.ownerOf(1)

    ).to.equal(

        seller.address

    );

    /*------------------------------------
            Seller approves Marketplace
    ------------------------------------*/

    await knowledgeAsset

        .connect(seller)

        .approve(

            await marketplace.getAddress(),

            1

        );

    /*------------------------------------
            Seller creates listing
    ------------------------------------*/

    await marketplace

        .connect(seller)

        .listFixedPrice(

            1,

            PRICE,

            royaltyRecipients(

                professor,

                university

            )

        );

    expect(

        await marketplace.isListed(1)

    ).to.equal(true);

    /*------------------------------------
            Buyer receives USDC
    ------------------------------------*/

    await usdc.mint(

        buyer.address,

        PRICE

    );

    /*------------------------------------
            Buyer approves Marketplace
    ------------------------------------*/

    await usdc

        .connect(buyer)

        .approve(

            await marketplace.getAddress(),

            PRICE

        );

    /*------------------------------------
            Buyer purchases NFT
    ------------------------------------*/

    await marketplace

        .connect(buyer)

        .buyAsset(1);

    /*------------------------------------
            Verify NFT Ownership
    ------------------------------------*/

    expect(

        await knowledgeAsset.ownerOf(1)

    ).to.equal(

        seller.address

    );
    expect(await marketplace.hasPurchased(1, buyer.address)).to.equal(true);
    expect(await marketplace.purchaseCount(1, buyer.address)).to.equal(1n);

    /*------------------------------------
            Verify Listing Closed
    ------------------------------------*/

    expect(

        await marketplace.isListed(1)

    ).to.equal(false);

});

});
it("distributes payment correctly after purchase", async function () {

    /*----------------------------------------
                Mint NFT
    ----------------------------------------*/

    await knowledgeAsset.connect(seller).mint(

        "ipfs://dataset",

        "ipfs://metadata",

        PRICE,

        0,

        95

    );

    await knowledgeAsset.connect(seller).approve(

        await marketplace.getAddress(),

        1

    );

    await marketplace.connect(seller).listFixedPrice(

        1,

        PRICE,

        royaltyRecipients(
            professor,
            university
        )

    );

    /*----------------------------------------
                Buyer receives USDC
    ----------------------------------------*/

    await usdc.mint(

        buyer.address,

        PRICE

    );

    await usdc.connect(buyer).approve(

        await marketplace.getAddress(),

        PRICE

    );

    /*----------------------------------------
            Record balances BEFORE
    ----------------------------------------*/

    const treasuryBefore =
        await usdc.balanceOf(
            treasury.address
        );

    const professorBefore =
        await usdc.balanceOf(
            professor.address
        );

    const universityBefore =
        await usdc.balanceOf(
            university.address
        );

    const sellerBefore =
        await usdc.balanceOf(
            seller.address
        );

    /*----------------------------------------
                Purchase
    ----------------------------------------*/

    await marketplace.connect(buyer).buyAsset(1);

    /*----------------------------------------
            Verify balances increased
    ----------------------------------------*/

    expect(

        await usdc.balanceOf(
            treasury.address
        )

    ).to.be.gt(treasuryBefore);

    expect(

        await usdc.balanceOf(
            professor.address
        )

    ).to.be.gt(professorBefore);

    expect(

        await usdc.balanceOf(
            university.address
        )

    ).to.be.gt(universityBefore);

    expect(

        await usdc.balanceOf(
            seller.address
        )

    ).to.be.gt(sellerBefore);

});
it("updates marketplace state after purchase", async function () {

    await knowledgeAsset.connect(seller).mint(
        "ipfs://cid",
        "ipfs://meta",
        PRICE,
        0,
        90
    );

    await knowledgeAsset.connect(seller).approve(
        await marketplace.getAddress(),
        1
    );

    await marketplace.connect(seller).listFixedPrice(
        1,
        PRICE,
        royaltyRecipients(
            professor,
            university
        )
    );

    await usdc.mint(
        buyer.address,
        PRICE
    );

    await usdc.connect(buyer).approve(
        await marketplace.getAddress(),
        PRICE
    );

    await marketplace.connect(buyer).buyAsset(1);

    expect(
        await marketplace.isListed(1)
    ).to.equal(false);

    expect(
        await knowledgeAsset.ownerOf(1)
    ).to.equal(
        seller.address
    );
    expect(await marketplace.hasPurchased(1, buyer.address)).to.equal(true);
    expect(await marketplace.purchaseCount(1, buyer.address)).to.equal(1n);

});it("emits PurchaseCompleted in integration flow", async function () {

    await knowledgeAsset.connect(seller).mint(
        "ipfs://cid",
        "ipfs://meta",
        PRICE,
        0,
        90
    );

    await knowledgeAsset.connect(seller).approve(
        await marketplace.getAddress(),
        1
    );

    await marketplace.connect(seller).listFixedPrice(
        1,
        PRICE,
        royaltyRecipients(
            professor,
            university
        )
    );

    await usdc.mint(
        buyer.address,
        PRICE
    );

    await usdc.connect(buyer).approve(
        await marketplace.getAddress(),
        PRICE
    );

    await expect(marketplace.connect(buyer).buyAsset(1))

    .to.emit(
        marketplace,
        "PurchaseCompleted"
    );

});

describe("Auction Workflow", function () {

    async function createAuction() {

        await knowledgeAsset.connect(seller).mint(
            "ipfs://auction",
            "ipfs://metadata",
            PRICE,
            0,
            95
        );

        await knowledgeAsset
            .connect(seller)
            .approve(
                await marketplace.getAddress(),
                1
            );

        const latest =
            await ethers.provider.getBlock("latest");

        const start =
            Number(latest!.timestamp);

        const end =
            start + 60;

        await marketplace
            .connect(seller)
            .createAuction(

                1,

                PRICE,

                start,

                end,

                royaltyRecipients(
                    professor,
                    university
                )

            );

        return {
            start,
            end
        };
    }

    it("completes an entire auction workflow", async function () {

        await createAuction();

        //-----------------------------------------
        // Fund buyers
        //-----------------------------------------

        await usdc.mint(
            buyer.address,
            PRICE * 10n
        );

        await usdc.mint(
            professor.address,
            PRICE * 10n
        );

        await usdc
            .connect(buyer)
            .approve(
                await marketplace.getAddress(),
                PRICE * 10n
            );

        await usdc
            .connect(professor)
            .approve(
                await marketplace.getAddress(),
                PRICE * 10n
            );

        //-----------------------------------------
        // Buyer bids
        //-----------------------------------------

        await marketplace
            .connect(buyer)
            .placeBid(
                1,
                PRICE
            );

        //-----------------------------------------
        // Professor outbids
        //-----------------------------------------

        await marketplace
            .connect(professor)
            .placeBid(
                1,
                PRICE + 1_000_000n
            );

        //-----------------------------------------
        // End auction
        //-----------------------------------------

        await ethers.provider.send(
            "evm_increaseTime",
            [120]
        );

        await ethers.provider.send(
            "evm_mine",
            []
        );

        await marketplace.endAuction(1);

        //-----------------------------------------
        // Verify NFT
        //-----------------------------------------

        expect(
            await knowledgeAsset.ownerOf(1)
        ).to.equal(
            seller.address
        );
    expect(await marketplace.hasPurchased(1, professor.address)).to.equal(true);
    expect(await marketplace.purchaseCount(1, professor.address)).to.equal(1n);

        expect(
            await marketplace.isAuctionActive(1)
        ).to.equal(false);

    });

    it("credits, but does not auto-pay, the outbid bidder's refund", async function () {

        await createAuction();

        await usdc.mint(
            buyer.address,
            PRICE * 10n
        );

        await usdc.mint(
            professor.address,
            PRICE * 10n
        );

        await usdc
            .connect(buyer)
            .approve(
                await marketplace.getAddress(),
                PRICE * 10n
            );

        await usdc
            .connect(professor)
            .approve(
                await marketplace.getAddress(),
                PRICE * 10n
            );

        const before =
            await usdc.balanceOf(
                buyer.address
            );

        await marketplace
            .connect(buyer)
            .placeBid(
                1,
                PRICE
            );

        await marketplace
            .connect(professor)
            .placeBid(
                1,
                PRICE + 1_000_000n
            );

        // Outbid refunds are no longer paid automatically — they're
        // credited to pendingRefunds and must be withdrawn explicitly.
        // See RoyaltySplitter/Marketplace audit notes: an automatic
        // push refund could be permanently blocked by a single
        // blocklisted USDC address, freezing the whole auction.
        //
        // Note: `before` was captured before the buyer placed any bid,
        // so once they bid PRICE, their balance is already down by
        // PRICE regardless of being outbid — that's the bid leaving
        // their wallet, not a missing refund.

        const afterOutbid =
            await usdc.balanceOf(
                buyer.address
            );

        expect(afterOutbid).to.equal(before - PRICE);

        expect(
            await marketplace.pendingRefunds(buyer.address)
        ).to.equal(PRICE);

        await marketplace.connect(buyer).withdrawRefund();

        const afterWithdraw =
            await usdc.balanceOf(
                buyer.address
            );

        expect(afterWithdraw).to.equal(before);

    });

    it("stores complete bid history", async function () {

        await createAuction();

        await usdc.mint(
            buyer.address,
            PRICE * 10n
        );

        await usdc.mint(
            professor.address,
            PRICE * 10n
        );

        await usdc.connect(buyer).approve(
            await marketplace.getAddress(),
            PRICE * 10n
        );

        await usdc.connect(professor).approve(
            await marketplace.getAddress(),
            PRICE * 10n
        );

        await marketplace.connect(buyer)
            .placeBid(
                1,
                PRICE
            );

        await marketplace.connect(professor)
            .placeBid(
                1,
                PRICE + 1000000n
            );

        const bids =
            await marketplace.getAuctionBids(1);

        expect(
            bids.length
        ).to.equal(2);

    });

    it("emits AuctionEnded event", async function () {

        await createAuction();

        await usdc.mint(
            buyer.address,
            PRICE
        );

        await usdc.connect(buyer)
            .approve(
                await marketplace.getAddress(),
                PRICE
            );

        await marketplace
            .connect(buyer)
            .placeBid(
                1,
                PRICE
            );

        await ethers.provider.send(
            "evm_increaseTime",
            [120]
        );

        await ethers.provider.send(
            "evm_mine",
            []
        );

        await expect(

            marketplace.endAuction(1)

        )

        .to.emit(
            marketplace,
            "AuctionEnded"
        );

    });

});

describe("Multiple Marketplace Workflows", function () {
    it("handles multiple fixed-price sales", async function () {

    // -------- NFT #1 --------

    await knowledgeAsset.connect(seller).mint(
        "cid1",
        "meta1",
        PRICE,
        0,
        90
    );

    await knowledgeAsset
        .connect(seller)
        .approve(
            await marketplace.getAddress(),
            1
        );

    await marketplace
        .connect(seller)
        .listFixedPrice(
            1,
            PRICE,
            royaltyRecipients(
                professor,
                university
            )
        );

    // -------- NFT #2 --------

    await knowledgeAsset.connect(seller).mint(
        "cid2",
        "meta2",
        PRICE,
        0,
        91
    );

    await knowledgeAsset
        .connect(seller)
        .approve(
            await marketplace.getAddress(),
            2
        );

    await marketplace
        .connect(seller)
        .listFixedPrice(
            2,
            PRICE,
            royaltyRecipients(
                professor,
                university
            )
        );

    await usdc.mint(
        buyer.address,
        PRICE * 2n
    );

    await usdc
        .connect(buyer)
        .approve(
            await marketplace.getAddress(),
            PRICE * 2n
        );

    await marketplace
        .connect(buyer)
        .buyAsset(1);

    await marketplace
        .connect(buyer)
        .buyAsset(2);

    expect(
        await knowledgeAsset.ownerOf(1)
    ).to.equal(seller.address);
    expect(await marketplace.hasPurchased(1, buyer.address)).to.equal(true);
    expect(await marketplace.purchaseCount(1, buyer.address)).to.equal(1n);

    expect(
        await knowledgeAsset.ownerOf(2)
    ).to.equal(seller.address);
    expect(await marketplace.hasPurchased(2, buyer.address)).to.equal(true);
    expect(await marketplace.purchaseCount(2, buyer.address)).to.equal(1n);

});
it("supports listing and auction simultaneously", async function () {

    // NFT #1 -> Fixed Price

    await knowledgeAsset.connect(seller).mint(
        "cid1",
        "meta1",
        PRICE,
        0,
        90
    );

    await knowledgeAsset.connect(seller).approve(
        await marketplace.getAddress(),
        1
    );

    await marketplace.connect(seller).listFixedPrice(
        1,
        PRICE,
        royaltyRecipients(
            professor,
            university
        )
    );

    // NFT #2 -> Auction

    await knowledgeAsset.connect(seller).mint(
        "cid2",
        "meta2",
        PRICE,
        0,
        90
    );

    await knowledgeAsset.connect(seller).approve(
        await marketplace.getAddress(),
        2
    );

    const latest =
        await ethers.provider.getBlock("latest");

    const start =
        Number(latest!.timestamp);

    await marketplace.connect(seller)
        .createAuction(
            2,
            PRICE,
            start,
            start + 60,
            royaltyRecipients(
                professor,
                university
            )
        );

    expect(
        await marketplace.isListed(1)
    ).to.equal(true);

    expect(
        await marketplace.isAuctionActive(2)
    ).to.equal(true);

});
it("handles multiple auctions", async function () {

    const latest =
        await ethers.provider.getBlock("latest");

    const start =
        Number(latest!.timestamp);

    for (let i = 1; i <= 2; i++) {

        await knowledgeAsset.connect(seller).mint(
            "cid",
            "meta",
            PRICE,
            0,
            90
        );

        await knowledgeAsset
            .connect(seller)
            .approve(
                await marketplace.getAddress(),
                i
            );

        await marketplace
            .connect(seller)
            .createAuction(
                i,
                PRICE,
                start,
                start + 60,
                royaltyRecipients(
                    professor,
                    university
                )
            );

    }

    expect(
        await marketplace.auctionExists(1)
    ).to.equal(true);

    expect(
        await marketplace.auctionExists(2)
    ).to.equal(true);

});
it("maintains marketplace state correctly", async function () {

    await knowledgeAsset.connect(seller).mint(
        "cid",
        "meta",
        PRICE,
        0,
        90
    );

    await knowledgeAsset.connect(seller).approve(
        await marketplace.getAddress(),
        1
    );

    await marketplace.connect(seller).listFixedPrice(
        1,
        PRICE,
        royaltyRecipients(
            professor,
            university
        )
    );

    expect(
        await marketplace.listingExists(1)
    ).to.equal(true);

    expect(
        await marketplace.isListed(1)
    ).to.equal(true);

    await marketplace
        .connect(seller)
        .cancelListing(1);

    expect(
        await marketplace.isListed(1)
    ).to.equal(false);

});
});

});