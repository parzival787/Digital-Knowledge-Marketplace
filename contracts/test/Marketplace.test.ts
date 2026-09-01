import { expect } from "chai";
import { network } from "hardhat";



describe("Marketplace", function () {

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

    const PLATFORM_FEE = 500; // 5%


    let PRICE: bigint;

        async function mintAsset() {
    await knowledgeAsset.connect(seller).mint(
        "ipfs://file",
        "ipfs://metadata",
        PRICE,
        0,
        90
    );
}

async function approveMarketplace() {
    await knowledgeAsset
        .connect(seller)
        .approve(
            await marketplace.getAddress(),
            1
        );
}

async function createListing() {

    await mintAsset();

    await approveMarketplace();

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
}

async function createAuction() {

    await mintAsset();

    await approveMarketplace();

    const latest = await ethers.provider.getBlock("latest");

    const startTime = Number(latest!.timestamp);

    const endTime = startTime + 3600;

    await marketplace
        .connect(seller)
        .createAuction(
            1,
            PRICE,
            startTime,
            endTime,
            royaltyRecipients(
                professor,
                university
            )
        );

    return {
        startTime,
        endTime
    };
}

async function createFinishedAuction() {

    const latest = await ethers.provider.getBlock("latest");

    const start = Number(latest!.timestamp);
    const end = start + 10;

    await mintAsset();

    await approveMarketplace();

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

    await usdc.mint(
        buyer.address,
        PRICE * 10n
    );

    await usdc
        .connect(buyer)
        .approve(
            await marketplace.getAddress(),
            PRICE * 10n
        );

    await marketplace
        .connect(buyer)
        .placeBid(
            1,
            PRICE
        );

    // Move blockchain time forward
    await ethers.provider.send(
        "evm_increaseTime",
        [20]
    );

    await ethers.provider.send(
        "evm_mine",
        []
    );
}

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

        /*----------------------------------------------------------
                            Deploy Mock USDC
        ----------------------------------------------------------*/

        const MockERC20 =
            await ethers.getContractFactory(
                "MockERC20"
            );

        usdc = await MockERC20.deploy(
            "Mock USD Coin",
            "USDC",
            6
        );

        await usdc.waitForDeployment();

        /*----------------------------------------------------------
                        Deploy KnowledgeAsset
        ----------------------------------------------------------*/

        const KnowledgeAsset =
            await ethers.getContractFactory(
                "KnowledgeAsset"
            );

        knowledgeAsset = await KnowledgeAsset.deploy();

        await knowledgeAsset.waitForDeployment();

        /*----------------------------------------------------------
                    Deploy RoyaltySplitter
        ----------------------------------------------------------*/

        const RoyaltySplitter =
            await ethers.getContractFactory(
                "RoyaltySplitter"
            );

        royaltySplitter =
            await RoyaltySplitter.deploy(

                await usdc.getAddress(),

                treasury.address,

                PLATFORM_FEE

            );

        await royaltySplitter.waitForDeployment();

        /*----------------------------------------------------------
                        Deploy Marketplace
        ----------------------------------------------------------*/

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

        /*----------------------------------------------------------
            Authorize Marketplace as RoyaltySplitter's caller.
            Without this, every buyAsset/endAuction call reverts
            with NotMarketplace — RoyaltySplitter now only accepts
            distributeRoyalty calls from this configured address.
        ----------------------------------------------------------*/

        await royaltySplitter.updateMarketplace(
            await marketplace.getAddress()
        );

    });
    describe("Deployment", function () {

    it("stores KnowledgeAsset correctly", async function () {

        expect(

            await marketplace.knowledgeAsset()

        ).to.equal(

            await knowledgeAsset.getAddress()

        );

    });

    it("stores RoyaltySplitter correctly", async function () {

        expect(

            await marketplace.royaltySplitter()

        ).to.equal(

            await royaltySplitter.getAddress()

        );

    });

    it("stores USDC correctly", async function () {

        expect(

            await marketplace.usdc()

        ).to.equal(

            await usdc.getAddress()

        );

    });

    it("starts with zero listings", async function () {

        expect(

            await marketplace.totalListingsCreated()

        ).to.equal(0);

    });

    it("starts with zero auctions", async function () {

        expect(

            await marketplace.totalAuctionsCreated()

        ).to.equal(0);

    });

    it("seller can mint an NFT", async function () {

    await knowledgeAsset.connect(seller).mint(

        "ipfs://file",

        "ipfs://metadata",

        PRICE,

        0,

        90

    );

    expect(

        await knowledgeAsset.ownerOf(1)

    ).to.equal(

        seller.address

    );

});
    it("seller approves marketplace", async function () {

    await knowledgeAsset.connect(seller).mint(

        "ipfs://file",

        "ipfs://metadata",

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

    expect(

        await knowledgeAsset.getApproved(1)

    ).to.equal(

        await marketplace.getAddress()

    );

});

it("creates a fixed-price listing", async function () {

    await knowledgeAsset.connect(seller).mint(

        "ipfs://file",

        "ipfs://metadata",

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

    expect(

        await marketplace.totalListingsCreated()

    ).to.equal(1);

    expect(

        await marketplace.isListed(1)

    ).to.equal(true);

});


it("emits AssetListed", async function () {

    await knowledgeAsset.connect(seller).mint(

        "ipfs://file",

        "ipfs://metadata",

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

    await expect(

        marketplace
            .connect(seller)
            .listFixedPrice(

                1,

                PRICE,

                royaltyRecipients(
                    professor,
                    university
                )

            )

    )

    .to.emit(
        marketplace,
        "AssetListed"
    )

    .withArgs(

        1,

        1,

        seller.address,

        PRICE

    );

});


it("rejects non-owner listing", async function () {

    await knowledgeAsset.connect(seller).mint(

        "ipfs://file",

        "ipfs://metadata",

        PRICE,

        0,

        90

    );

    await expect(

        marketplace
            .connect(buyer)
            .listFixedPrice(

                1,

                PRICE,

                royaltyRecipients(
                    professor,
                    university
                )

            )

    ).to.be.revertedWithCustomError(
        marketplace,
        "NotNFTOwner"
    );

});

it("rejects duplicate listing", async function () {

    await knowledgeAsset.connect(seller).mint(

        "ipfs://file",

        "ipfs://metadata",

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

    await expect(

        marketplace
            .connect(seller)
            .listFixedPrice(

                1,

                PRICE,

                royaltyRecipients(
                    professor,
                    university
                )

            )

    ).to.be.revertedWithCustomError(
        marketplace,
        "AlreadyListed"
    );

});

it("rejects invalid royalty shares", async function () {

    await knowledgeAsset.connect(seller).mint(

        "ipfs://file",

        "ipfs://metadata",

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

    await expect(

        marketplace
            .connect(seller)
            .listFixedPrice(

                1,

                PRICE,

                [
                    {
                        wallet: professor.address,
                        shareBps: 5000
                    }
                ]

            )

    ).to.be.revertedWithCustomError(
        marketplace,
        "RoyaltyExceedsMaximum"
    );
});

it("rejects more than MAX_RECIPIENTS royalty recipients", async function () {

    await knowledgeAsset.connect(seller).mint(
        "ipfs://file",
        "ipfs://metadata",
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

    const tooManyRecipients = Array.from(
        { length: 11 },
        () => ({
            wallet: ethers.Wallet.createRandom().address,
            shareBps: 1
        })
    );

    await expect(
        marketplace
            .connect(seller)
            .listFixedPrice(
                1,
                PRICE,
                tooManyRecipients
            )
    ).to.be.revertedWithCustomError(
        marketplace,
        "TooManyRecipients"
    );
});

    });

    it("buyer purchases listed NFT", async function () {

    await createListing();

    await usdc.mint(
        buyer.address,
        PRICE
    );

    await usdc
        .connect(buyer)
        .approve(
            await marketplace.getAddress(),
            PRICE
        );

    await marketplace
        .connect(buyer)
        .buyAsset(1);

    // NFT ownership remains with the original creator/seller
    expect(
        await knowledgeAsset.ownerOf(1)
    ).to.equal(
        seller.address
    );

    // Buyer receives a purchase/license entitlement
    expect(
        await marketplace.purchaseCount(
            1,
            buyer.address
        )
    ).to.equal(1);

});

it("prevents buyer from reselling purchased NFT", async function () {

    // Creator lists the NFT
    await createListing();

    // Give buyer enough USDC
    await usdc.mint(
        buyer.address,
        PRICE
    );

    // Approve Marketplace to spend buyer's USDC
    await usdc
        .connect(buyer)
        .approve(
            await marketplace.getAddress(),
            PRICE
        );

    // Buyer purchases the license/access
    await marketplace
        .connect(buyer)
        .buyAsset(1);

    // NFT must still belong to the original creator
    expect(
        await knowledgeAsset.ownerOf(1)
    ).to.equal(
        seller.address
    );

    // Buyer must have the purchase entitlement
    expect(
        await marketplace.purchaseCount(
            1,
            buyer.address
        )
    ).to.equal(1);

    // Buyer must NOT be able to list the creator's NFT
    await expect(
        marketplace
            .connect(buyer)
            .listFixedPrice(
                1,
                PRICE,
                royaltyRecipients(
                    professor,
                    university
                )
            )
    ).to.be.revertedWithCustomError(
        marketplace,
        "NotNFTOwner"
    );
});

it("marks listing inactive after purchase", async function () {

    await createListing();

    await usdc.mint(
        buyer.address,
        PRICE
    );

    await usdc
        .connect(buyer)
        .approve(
            await marketplace.getAddress(),
            PRICE
        );

    await marketplace
        .connect(buyer)
        .buyAsset(1);

    expect(
        await marketplace.isListed(1)
    ).to.equal(false);

});it("emits PurchaseCompleted", async function () {

    await createListing();

    await usdc.mint(
        buyer.address,
        PRICE
    );

    await usdc
        .connect(buyer)
        .approve(
            await marketplace.getAddress(),
            PRICE
        );

    await expect(

        marketplace
            .connect(buyer)
            .buyAsset(1)

    )

    .to.emit(
        marketplace,
        "PurchaseCompleted"
    );

});it("prevents seller from buying own NFT", async function () {

    await createListing();

    await expect(

        marketplace
            .connect(seller)
            .buyAsset(1)

    ).to.be.revertedWithCustomError(
        marketplace,
        "SellerCannotBuyOwnAsset"
    );

});it("rejects inactive listing", async function () {

    await createListing();

    await marketplace
        .connect(seller)
        .cancelListing(1);

    await expect(

        marketplace
            .connect(buyer)
            .buyAsset(1)

    ).to.be.revertedWithCustomError(
        marketplace,
        "ListingInactive"
    );

});it("fails when buyer has no USDC", async function () {

    await createListing();

    await expect(

        marketplace
            .connect(buyer)
            .buyAsset(1)

    ).to.be.revertedWith("ERC20: insufficient allowance");;

});it("fails without USDC approval", async function () {

    await createListing();

    await usdc.mint(
        buyer.address,
        PRICE
    );

    await expect(

        marketplace
            .connect(buyer)
            .buyAsset(1)

    ).to.be.revertedWith("ERC20: insufficient allowance"); 

});it("creates auction successfully", async function () {

    await createAuction();

    expect(
        await marketplace.totalAuctionsCreated()
    ).to.equal(1);

    expect(
        await marketplace.isAuctionActive(1)
    ).to.equal(true);

});it("auction exists", async function () {

    await createAuction();

    expect(
        await marketplace.auctionExists(1)
    ).to.equal(true);

});it("stores royalty recipients", async function () {

    await createAuction();

    const recipients =
        await marketplace.getAuctionRecipients(1);

    expect(
        recipients.length
    ).to.equal(2);

});it("emits AuctionCreated", async function () {

    await mintAsset();

    await approveMarketplace();

    const latest =
        await ethers.provider.getBlock("latest");

    const start =
        Number(latest!.timestamp);

    const end =
        start + 3600;

    await expect(

        marketplace
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

            )

    )

    .to.emit(
        marketplace,
        "AuctionCreated"
    );

});it("rejects duplicate auction", async function () {

    await createAuction();

    const latest =
        await ethers.provider.getBlock("latest");

    const start =
        Number(latest!.timestamp);

    const end =
        start + 3600;

    await expect(

        marketplace
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

            )

    ).to.be.revertedWithCustomError(
        marketplace,
        "AuctionAlreadyExists"
    );

});it("rejects zero reserve price", async function () {

    await mintAsset();

    await approveMarketplace();

    const latest =
        await ethers.provider.getBlock("latest");

    const start =
        Number(latest!.timestamp);

    const end =
        start + 3600;

    await expect(

        marketplace
            .connect(seller)
            .createAuction(

                1,

                0,

                start,

                end,

                royaltyRecipients(
                    professor,
                    university
                )

            )

    ).to.be.revertedWithCustomError(
        marketplace,
        "InvalidReservePrice"
    );

});it("rejects invalid duration", async function () {

    await mintAsset();

    await approveMarketplace();

    const latest =
        await ethers.provider.getBlock("latest");

    const start =
        Number(latest!.timestamp);

    await expect(

        marketplace
            .connect(seller)
            .createAuction(

                1,

                PRICE,

                start,

                start,

                royaltyRecipients(
                    professor,
                    university
                )

            )

    ).to.be.revertedWithCustomError(
        marketplace,
        "InvalidAuctionDuration"
    );

});it("rejects non-owner", async function () {

    await mintAsset();

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
        start + 3600;

    await expect(

        marketplace
            .connect(buyer)
            .createAuction(

                1,

                PRICE,

                start,

                end,

                royaltyRecipients(
                    professor,
                    university
                )

            )

    ).to.be.revertedWithCustomError(
        marketplace,
        "NotNFTOwner"
    );

});it("accepts the first valid bid", async function () {

    await createAuction();

    await usdc.mint(buyer.address, PRICE);

    await usdc
        .connect(buyer)
        .approve(await marketplace.getAddress(), PRICE);

    await marketplace
        .connect(buyer)
        .placeBid(1, PRICE);

    const bids = await marketplace.getAuctionBids(1);

    expect(bids.length).to.equal(1);
    expect(bids[0].bidder).to.equal(buyer.address);
    expect(bids[0].amount).to.equal(PRICE);

});it("emits BidPlaced event", async function () {

    await createAuction();

    await usdc.mint(buyer.address, PRICE);

    await usdc
        .connect(buyer)
        .approve(await marketplace.getAddress(), PRICE);

    await expect(

        marketplace
            .connect(buyer)
            .placeBid(1, PRICE)

    )

    .to.emit(marketplace, "BidPlaced");

});it("rejects bid below reserve", async function () {

    await createAuction();

    await usdc.mint(buyer.address, PRICE);

    await usdc
        .connect(buyer)
        .approve(await marketplace.getAddress(), PRICE);

    await expect(

        marketplace
            .connect(buyer)
            .placeBid(
                1,
                PRICE - 1n
            )

    ).to.be.revertedWithCustomError(
        marketplace,
        "BelowReservePrice"
    );

});it("prevents seller from bidding", async function () {

    await createAuction();

    await usdc.mint(seller.address, PRICE);

    await usdc
        .connect(seller)
        .approve(await marketplace.getAddress(), PRICE);

    await expect(

        marketplace
            .connect(seller)
            .placeBid(
                1,
                PRICE
            )

    ).to.be.revertedWithCustomError(
        marketplace,
        "SellerCannotBid"
    );

});it("accepts a higher bid", async function () {

    await createAuction();

    await usdc.mint(buyer.address, PRICE * 10n);
    await usdc.mint(professor.address, PRICE * 10n);

    await usdc
        .connect(buyer)
        .approve(await marketplace.getAddress(), PRICE * 10n);

    await usdc
        .connect(professor)
        .approve(await marketplace.getAddress(), PRICE * 10n);

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
            PRICE + 1000n
        );

    const bids =
        await marketplace.getAuctionBids(1);

    expect(
        bids.length
    ).to.equal(2);

});it("credits, but does not auto-pay, the outbid bidder's refund", async function () {

    await createAuction();

    await usdc.mint(buyer.address, PRICE * 10n);
    await usdc.mint(professor.address, PRICE * 10n);

    await usdc
        .connect(buyer)
        .approve(await marketplace.getAddress(), PRICE * 10n);

    await usdc
        .connect(professor)
        .approve(await marketplace.getAddress(), PRICE * 10n);

    await marketplace
        .connect(buyer)
        .placeBid(1, PRICE);

    const buyerBalanceBeforeOutbid =
        await usdc.balanceOf(buyer.address);

    await marketplace
        .connect(professor)
        .placeBid(1, PRICE + 1000n);

    // Not paid automatically — still a pull, not a push.
    expect(
        await usdc.balanceOf(buyer.address)
    ).to.equal(buyerBalanceBeforeOutbid);

    expect(
        await marketplace.pendingRefunds(buyer.address)
    ).to.equal(PRICE);

    await marketplace.connect(buyer).withdrawRefund();

    expect(
        await usdc.balanceOf(buyer.address)
    ).to.equal(buyerBalanceBeforeOutbid + PRICE);

    expect(
        await marketplace.pendingRefunds(buyer.address)
    ).to.equal(0);

});
it("returns true for buyer after purchase", async function () {

    await createListing();

    await usdc.mint(
        buyer.address,
        PRICE
    );

    await usdc
        .connect(buyer)
        .approve(
            await marketplace.getAddress(),
            PRICE
        );

    await marketplace
        .connect(buyer)
        .buyAsset(1);

    expect(
        await marketplace.hasPurchased(
            1,
            buyer.address
        )
    ).to.equal(true);
});
    
it("returns false for wallet that has not purchased", async function () {

    await createListing();

    expect(
        await marketplace.hasPurchased(
            1,
            buyer.address
        )
    ).to.equal(false);
});





it("rejects withdrawRefund with nothing owed", async function () {

    await expect(
        marketplace.connect(buyer).withdrawRefund()
    ).to.be.revertedWithCustomError(
        marketplace,
        "NoRefundOwed"
    );

});it("rejects lower bid", async function () {

    await createAuction();

    await usdc.mint(buyer.address, PRICE * 10n);
    await usdc.mint(professor.address, PRICE * 10n);

    await usdc
        .connect(buyer)
        .approve(await marketplace.getAddress(), PRICE * 10n);

    await usdc
        .connect(professor)
        .approve(await marketplace.getAddress(), PRICE * 10n);

    await marketplace
        .connect(buyer)
        .placeBid(
            1,
            PRICE
        );

    await expect(

        marketplace
            .connect(professor)
            .placeBid(
                1,
                PRICE
            )

    ).to.be.revertedWithCustomError(
        marketplace,
        "BidTooLow"
    );

});it("stores bid history", async function () {

    await createAuction();

    await usdc.mint(buyer.address, PRICE * 10n);

    await usdc
        .connect(buyer)
        .approve(await marketplace.getAddress(), PRICE * 10n);

    await marketplace
        .connect(buyer)
        .placeBid(
            1,
            PRICE
        );

    const bids =
        await marketplace.getAuctionBids(1);

    expect(
        bids.length
    ).to.equal(1);

    expect(
        bids[0].bidder
    ).to.equal(
        buyer.address
    );

});it("ends auction successfully", async function () {

    await createFinishedAuction();

    await marketplace.endAuction(1);

    expect(
        await marketplace.isAuctionActive(1)
    ).to.equal(false);

});it("keeps NFT with creator after auction", async function () {

    await createFinishedAuction();

    await marketplace.endAuction(1);

    expect(
    await knowledgeAsset.ownerOf(1)
).to.equal(
    seller.address
);

// Auction winner receives a purchase/license entitlement
expect(
    await marketplace.purchaseCount(
        1,
        buyer.address
    )
).to.equal(1);

});
it("prevents auction winner from reselling purchased NFT", async function () {

    await createFinishedAuction();

    await marketplace.endAuction(1);

    // NFT remains with the original creator
    expect(
        await knowledgeAsset.ownerOf(1)
    ).to.equal(
        seller.address
    );

    // Auction winner received the purchase/license entitlement
    expect(
        await marketplace.purchaseCount(
            1,
            buyer.address
        )
    ).to.equal(1);

    // Auction winner must not be able to resell the NFT
    await expect(
        marketplace
            .connect(buyer)
            .listFixedPrice(
                1,
                PRICE,
                royaltyRecipients(
                    professor,
                    university
                )
            )
    ).to.be.revertedWithCustomError(
        marketplace,
        "NotNFTOwner"
    );
});


it("emits AuctionEnded", async function () {

    await createFinishedAuction();

    await expect(

        marketplace.endAuction(1)

    )

    .to.emit(
        marketplace,
        "AuctionEnded"
    );

});it("cannot end auction twice", async function () {

    await createFinishedAuction();

    await marketplace.endAuction(1);

    await expect(

        marketplace.endAuction(1)

    ).to.be.revertedWithCustomError(
        marketplace,
        "AuctionInactive"
    );

});it("cannot end auction before end time", async function () {

    const latest =
        await ethers.provider.getBlock("latest");

    const start =
        Number(latest!.timestamp);

    const end =
        start + 3600;

    await mintAsset();

    await approveMarketplace();

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

    await expect(

        marketplace.endAuction(1)

    ).to.be.revertedWithCustomError(
        marketplace,
        "AuctionStillRunning"
    );

});it("handles auction with no bids", async function () {

    const latest =
        await ethers.provider.getBlock("latest");

    const start =
        Number(latest!.timestamp);

    const end =
        start + 10;

    await mintAsset();

    await approveMarketplace();

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

    await ethers.provider.send(
        "evm_increaseTime",
        [20]
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

});it("clears auction mapping after settlement", async function () {

    await createFinishedAuction();

    await marketplace.endAuction(1);

    expect(
        await marketplace.isAuctionActive(1)
    ).to.equal(false);

});it("marks auction finalized", async function () {

    await createFinishedAuction();

    await marketplace.endAuction(1);

    expect(
        await marketplace.auctionExists(1)
    ).to.equal(true);

});
it("owner can pause marketplace", async function () {

    await marketplace.pause();

    expect(
        await marketplace.paused()
    ).to.equal(true);

});
it("owner can unpause marketplace", async function () {

    await marketplace.pause();

    await marketplace.unpause();

    expect(
        await marketplace.paused()
    ).to.equal(false);

});
it("rejects non-owner pause", async function () {

    await expect(

        marketplace
            .connect(buyer)
            .pause()

    ).to.be.revertedWith("Ownable: caller is not the owner");

});
it("updates royalty splitter", async function () {

    const RoyaltySplitter =
        await ethers.getContractFactory(
            "RoyaltySplitter"
        );

    const newSplitter =
        await RoyaltySplitter.deploy(

            await usdc.getAddress(),

            treasury.address,

            PLATFORM_FEE

        );

    await newSplitter.waitForDeployment();

    await marketplace.updateRoyaltySplitter(

        await newSplitter.getAddress()

    );

    expect(

        await marketplace.royaltySplitter()

    ).to.equal(

        await newSplitter.getAddress()

    );

});
it("rejects zero royalty splitter", async function () {

    await expect(

        marketplace.updateRoyaltySplitter(

            ethers.ZeroAddress

        )

    ).to.be.revertedWithCustomError(
        marketplace,
        "InvalidRoyaltySplitter"
    );

});
it("listingExists works", async function () {

    await createListing();

    expect(

        await marketplace.listingExists(1)

    ).to.equal(true);

});
it("auctionExists works", async function () {

    await createAuction();

    expect(

        await marketplace.auctionExists(1)

    ).to.equal(true);

});
it("returns listing recipients", async function () {

    await createListing();

    const recipients =

        await marketplace.getListingRecipients(1);

    expect(

        recipients.length

    ).to.equal(2);

});
it("returns auction recipients", async function () {

    await createAuction();

    const recipients =

        await marketplace.getAuctionRecipients(1);

    expect(

        recipients.length

    ).to.equal(2);

});
it("returns empty bid history", async function () {

    await createAuction();

    const bids =

        await marketplace.getAuctionBids(1);

    expect(

        bids.length

    ).to.equal(0);

});
it("cannot cancel listing twice", async function () {

    await createListing();

    await marketplace
        .connect(seller)
        .cancelListing(1);

    await expect(

        marketplace
            .connect(seller)
            .cancelListing(1)

    ).to.be.revertedWithCustomError(
        marketplace,
        "ListingInactive"
    );

});
it("listing inactive after cancel", async function () {

    await createListing();

    await marketplace
        .connect(seller)
        .cancelListing(1);

    expect(

        await marketplace.isListed(1)

    ).to.equal(false);

});
it("auction inactive after settlement", async function () {

    await createFinishedAuction();

    await marketplace.endAuction(1);

    expect(

        await marketplace.isAuctionActive(1)

    ).to.equal(false);

});
it("keeps bid history after settlement", async function () {

    await createFinishedAuction();

    await marketplace.endAuction(1);

    const bids =

        await marketplace.getAuctionBids(1);

    expect(

        bids.length

    ).to.equal(1);

});


    
});