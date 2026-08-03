import { expect } from "chai";
import { network } from "hardhat";

describe("RoyaltySplitter", function () {

    let ethers: any;

    let owner: any;
    let treasury: any;
    let seller: any;
    let professor: any;
    let university: any;
    let buyer: any;
    let marketplace: any;

    let usdc: any;
    let royaltySplitter: any;

    const PLATFORM_FEE = 500;

    beforeEach(async function () {
        ({ ethers } = await network.connect());
        [
            owner,
            treasury,
            seller,
            professor,
            university,
            buyer,
            marketplace
        ] = await ethers.getSigners();

        //----------------------------------------------------------
        // Deploy Mock USDC
        //----------------------------------------------------------

        const MockERC20 =
            await ethers.getContractFactory(
                "MockERC20"
            );

        usdc = await MockERC20.deploy(
            "Mock USDC",
            "mUSDC",
            6
        );

        await usdc.waitForDeployment();

        //----------------------------------------------------------
        // Deploy RoyaltySplitter
        //----------------------------------------------------------

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

        //----------------------------------------------------------
        // Authorize the marketplace signer as the only caller
        // allowed to invoke distributeRoyalty. In production this
        // is Marketplace.sol's deployed address; here a plain
        // signer stands in for it.
        //----------------------------------------------------------

        await royaltySplitter.updateMarketplace(
            marketplace.address
        );

        //----------------------------------------------------------
        // Mint Mock USDC
        //----------------------------------------------------------

        await usdc.mint(
            buyer.address,
            1_000_000_000
        );
    });

    /*//////////////////////////////////////////////////////////////
                        CONSTRUCTOR TESTS
    //////////////////////////////////////////////////////////////*/

    it("stores treasury correctly", async function () {

        expect(
            await royaltySplitter.treasury()
        ).to.equal(
            treasury.address
        );
    });

    it("stores platform fee correctly", async function () {

        expect(
            await royaltySplitter.platformFeeBps()
        ).to.equal(
            PLATFORM_FEE
        );
    });

    it("calculates platform fee correctly", async function () {

        const fee =
            await royaltySplitter.calculatePlatformFee(
                100_000_000
            );

        expect(fee)
            .to.equal(5_000_000);
    });

    it("calculates royalty pool correctly", async function () {

        const amount =
            await royaltySplitter.calculateRoyaltyPool(
                100_000_000
            );

        expect(amount)
            .to.equal(95_000_000);
    });

        /*//////////////////////////////////////////////////////////////
                        ADMIN FUNCTION TESTS
    //////////////////////////////////////////////////////////////*/

    it("allows owner to update treasury", async function () {

        await royaltySplitter.updateTreasury(
            seller.address
        );

        expect(
            await royaltySplitter.treasury()
        ).to.equal(
            seller.address
        );
    });

    it("prevents non-owner from updating treasury", async function () {

        await expect(
            royaltySplitter
                .connect(buyer)
                .updateTreasury(
                    seller.address
                )
        ).to.be.revertedWith(
    "Ownable: caller is not the owner"
);
    });

    it("rejects zero treasury address", async function () {

        await expect(
            royaltySplitter.updateTreasury(
                ethers.ZeroAddress
            )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "InvalidTreasury"
);
    });

    it("allows owner to update platform fee", async function () {

        await royaltySplitter.updatePlatformFee(
            300
        );

        expect(
            await royaltySplitter.platformFeeBps()
        ).to.equal(
            300
        );
    });

    it("prevents non-owner from updating platform fee", async function () {

        await expect(
            royaltySplitter
                .connect(buyer)
                .updatePlatformFee(
                    300
                )
        ).to.be.revertedWith(
    "Ownable: caller is not the owner"
);
    });

    it("rejects platform fee above maximum", async function () {

        await expect(
            royaltySplitter.updatePlatformFee(
                5000
            )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "InvalidPlatformFee"
);
    });

    it("emits TreasuryUpdated event", async function () {

        await expect(
            royaltySplitter.updateTreasury(
                seller.address
            )
        )
        .to.emit(
            royaltySplitter,
            "TreasuryUpdated"
        )
        .withArgs(
            treasury.address,
            seller.address
        );
    });

    it("emits PlatformFeeUpdated event", async function () {

        await expect(
            royaltySplitter.updatePlatformFee(
                300
            )
        )
        .to.emit(
            royaltySplitter,
            "PlatformFeeUpdated"
        )
        .withArgs(
            PLATFORM_FEE,
            300
        );
    });

    it("allows owner to update the marketplace address", async function () {

        await royaltySplitter.updateMarketplace(
            buyer.address
        );

        expect(
            await royaltySplitter.marketplace()
        ).to.equal(
            buyer.address
        );
    });

    it("prevents non-owner from updating the marketplace address", async function () {

        await expect(
            royaltySplitter
                .connect(buyer)
                .updateMarketplace(
                    buyer.address
                )
        ).to.be.revertedWith(
    "Ownable: caller is not the owner"
);
    });

    it("rejects zero marketplace address", async function () {

        await expect(
            royaltySplitter.updateMarketplace(
                ethers.ZeroAddress
            )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "InvalidMarketplace"
);
    });

    it("emits MarketplaceUpdated event", async function () {

        await expect(
            royaltySplitter.updateMarketplace(
                buyer.address
            )
        )
        .to.emit(
            royaltySplitter,
            "MarketplaceUpdated"
        )
        .withArgs(
            marketplace.address,
            buyer.address
        );
    });

        /*//////////////////////////////////////////////////////////////
                    ROYALTY DISTRIBUTION TESTS
    //////////////////////////////////////////////////////////////*/

    it("distributes royalties correctly", async function () {

        const totalAmount = 100_000_000; //100 USDC

        // Transfer funds into splitter
        await usdc
            .connect(buyer)
            .transfer(
                await royaltySplitter.getAddress(),
                totalAmount
            );

        const recipients = [
            {
                wallet: professor.address,
                shareBps: 1000
            },
            {
                wallet: university.address,
                shareBps: 500
            }
        ];

        await royaltySplitter
            .connect(marketplace)
            .distributeRoyalty(
                seller.address,
                recipients,
                totalAmount
            );

        expect(
            await usdc.balanceOf(
                treasury.address
            )
        ).to.equal(
            5_000_000
        );

        expect(
            await usdc.balanceOf(
                professor.address
            )
        ).to.equal(
            9_500_000
        );

        expect(
            await usdc.balanceOf(
                university.address
            )
        ).to.equal(
            4_750_000
        );

        expect(
            await usdc.balanceOf(
                seller.address
            )
        ).to.equal(
            80_750_000
        );
    });

    it("emits SellerPaid event", async function () {

        const totalAmount = 100_000_000;

        await usdc
            .connect(buyer)
            .transfer(
                await royaltySplitter.getAddress(),
                totalAmount
            );

        const recipients = [
            {
                wallet: professor.address,
                shareBps: 1000
            }
        ];

        await expect(
            royaltySplitter
                .connect(marketplace)
                .distributeRoyalty(
                    seller.address,
                    recipients,
                    totalAmount
                )
        )
        .to.emit(
            royaltySplitter,
            "SellerPaid"
        )
        .withArgs(
            seller.address,
            85_500_000
        );
    });

    it("rejects calls from anyone other than the marketplace", async function () {

        const recipients = [
            {
                wallet: professor.address,
                shareBps: 1000
            }
        ];

        await expect(
            royaltySplitter
                .connect(buyer)
                .distributeRoyalty(
                    seller.address,
                    recipients,
                    100_000_000
                )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "NotMarketplace"
);
    });

    it("rejects zero seller address", async function () {

        const recipients = [
            {
                wallet: professor.address,
                shareBps: 1000
            }
        ];

        await expect(
            royaltySplitter
                .connect(marketplace)
                .distributeRoyalty(
                    ethers.ZeroAddress,
                    recipients,
                    100_000_000
                )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "InvalidSeller"
);
    });

    it("rejects zero amount", async function () {

        const recipients = [
            {
                wallet: professor.address,
                shareBps: 1000
            }
        ];

        await expect(
            royaltySplitter
                .connect(marketplace)
                .distributeRoyalty(
                    seller.address,
                    recipients,
                    0
                )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "InvalidAmount"
);
    });

    it("rejects royalty shares above the maximum", async function () {

        const recipients = [
            {
                wallet: professor.address,
                shareBps: 9000
            }
        ];

        await expect(
            royaltySplitter
                .connect(marketplace)
                .distributeRoyalty(
                    seller.address,
                    recipients,
                    100_000_000
                )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "RoyaltyExceedsMaximum"
);
    });

    it("rejects a recipient that is also the seller", async function () {

        const recipients = [
            {
                wallet: seller.address,
                shareBps: 1000
            }
        ];

        await expect(
            royaltySplitter
                .connect(marketplace)
                .distributeRoyalty(
                    seller.address,
                    recipients,
                    100_000_000
                )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "SellerCannotBeRecipient"
);
    });

    it("rejects duplicate recipients", async function () {

        const recipients = [
            {
                wallet: professor.address,
                shareBps: 500
            },
            {
                wallet: professor.address,
                shareBps: 500
            }
        ];

        await expect(
            royaltySplitter
                .connect(marketplace)
                .distributeRoyalty(
                    seller.address,
                    recipients,
                    100_000_000
                )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "DuplicateRecipient"
);
    });

    it("rejects zero recipient address", async function () {

        const recipients = [
            {
                wallet: ethers.ZeroAddress,
                shareBps: 1000
            }
        ];

        await expect(
            royaltySplitter
                .connect(marketplace)
                .distributeRoyalty(
                    seller.address,
                    recipients,
                    100_000_000
                )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "InvalidRecipient"
);
    });

    it("rejects too many recipients", async function () {

        const recipients = Array.from(
            { length: 11 },
            () => ({
                wallet: ethers.Wallet.createRandom().address,
                shareBps: 100
            })
        );

        await expect(
            royaltySplitter
                .connect(marketplace)
                .distributeRoyalty(
                    seller.address,
                    recipients,
                    100_000_000
                )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "TooManyRecipients"
);
    });

});
