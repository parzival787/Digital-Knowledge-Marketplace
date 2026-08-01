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
            buyer
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
            await royaltySplitter.calculateSellerAmount(
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
                wallet: seller.address,
                shareBps: 8000
            },
            {
                wallet: professor.address,
                shareBps: 1000
            },
            {
                wallet: university.address,
                shareBps: 1000
            }
        ];

        await royaltySplitter.distributeRoyalty(
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
                seller.address
            )
        ).to.equal(
            76_000_000
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
            9_500_000
        );
    });

    it("rejects zero amount", async function () {

        const recipients = [
            {
                wallet: seller.address,
                shareBps: 10000
            }
        ];

        await expect(
            royaltySplitter.distributeRoyalty(
                recipients,
                0
            )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "InvalidAmount"
);
    });

    it("rejects invalid total shares", async function () {

        const recipients = [
            {
                wallet: seller.address,
                shareBps: 9000
            }
        ];

        await expect(
            royaltySplitter.distributeRoyalty(
                recipients,
                100_000_000
            )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "InvalidTotalShares"
);
    });

    it("rejects duplicate recipients", async function () {

        const recipients = [
            {
                wallet: seller.address,
                shareBps: 5000
            },
            {
                wallet: seller.address,
                shareBps: 5000
            }
        ];

        await expect(
            royaltySplitter.distributeRoyalty(
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
                shareBps: 10000
            }
        ];

        await expect(
            royaltySplitter.distributeRoyalty(
                recipients,
                100_000_000
            )
        ).to.be.revertedWithCustomError(
    royaltySplitter,
    "InvalidRecipient"
);
    });

});
