// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/* ============================================================
 * RoyaltySplitter v2.0
 * Decentralized Knowledge Marketplace (DKM)
 *
 * Responsibilities:
 * - Hold USDC received from Marketplace
 * - Deduct platform fee
 * - Distribute remaining royalty pool
 * - Emit payment events
 * ============================================================
 */

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

import "./interfaces/IRoyaltySplitter.sol";

contract RoyaltySplitter is
    Ownable,
    ReentrancyGuard,
    IRoyaltySplitter
{
    using SafeERC20 for IERC20;

    /*//////////////////////////////////////////////////////////////
                            CUSTOM ERRORS
    //////////////////////////////////////////////////////////////*/

    error InvalidTreasury();
    error InvalidUSDC();
    error InvalidPlatformFee();
    error InvalidRecipient();
    error InvalidRoyaltyShare();
    error InvalidTotalShares();
    error InvalidAmount();
    error TooManyRecipients();
    error DuplicateRecipient();

    /*//////////////////////////////////////////////////////////////
                              CONSTANTS
    //////////////////////////////////////////////////////////////*/

    /// @notice 100%
    uint16 public constant BPS_DENOMINATOR = 10_000;

    /// @notice Maximum platform fee = 10%
    uint16 public constant MAX_PLATFORM_FEE = 1_000;

    /// @notice Maximum royalty recipients
    uint8 public constant MAX_RECIPIENTS = 10;

    /*//////////////////////////////////////////////////////////////
                               STORAGE
    //////////////////////////////////////////////////////////////*/

    /// @notice ERC20 payment token (MockUSDC / USDC)
    IERC20 public immutable usdc;

    /// @inheritdoc IRoyaltySplitter
    address public override treasury;

    /// @inheritdoc IRoyaltySplitter
    uint16 public override platformFeeBps;



    /*//////////////////////////////////////////////////////////////
                              CONSTRUCTOR
    //////////////////////////////////////////////////////////////*/

    constructor(
        address usdcAddress,
        address treasuryAddress,
        uint16 feeBps
    ) {
        if (usdcAddress == address(0))
            revert InvalidUSDC();

        if (treasuryAddress == address(0))
            revert InvalidTreasury();

        if (feeBps > MAX_PLATFORM_FEE)
            revert InvalidPlatformFee();

        usdc = IERC20(usdcAddress);
        treasury = treasuryAddress;
        platformFeeBps = feeBps;
    }

    /*//////////////////////////////////////////////////////////////
                         FEE CALCULATIONS
    //////////////////////////////////////////////////////////////*/

    /**
     * @notice Calculates platform fee.
     * @param amount Purchase amount.
     */
    function calculatePlatformFee(
        uint256 amount
    )
        public
        view
        override
        returns (uint256)
    {
        return (amount * platformFeeBps)
            / BPS_DENOMINATOR;
    }

    /**
     * @notice Calculates royalty pool after
     *         platform fee deduction.
     */
    function calculateSellerAmount(
        uint256 amount
    )
        public
        view
        override
        returns (uint256)
    {
        return amount
            - calculatePlatformFee(amount);
    }

        /*//////////////////////////////////////////////////////////////
                         ADMIN FUNCTIONS
    //////////////////////////////////////////////////////////////*/

    /**
     * @notice Updates the treasury wallet.
     * @dev Only callable by the owner.
     */
    function updateTreasury(
        address newTreasury
    )
        external
        override
        onlyOwner
    {
        if (newTreasury == address(0))
            revert InvalidTreasury();

        address oldTreasury = treasury;

        treasury = newTreasury;

        emit TreasuryUpdated(
            oldTreasury,
            newTreasury
        );
    }

    /**
     * @notice Updates platform fee.
     * @dev Fee is stored in Basis Points.
     */
    function updatePlatformFee(
        uint16 newFeeBps
    )
        external
        override
        onlyOwner
    {
        if (newFeeBps > MAX_PLATFORM_FEE)
            revert InvalidPlatformFee();

        uint16 oldFee = platformFeeBps;

        platformFeeBps = newFeeBps;

        emit PlatformFeeUpdated(
            oldFee,
            newFeeBps
        );
    }

    /*//////////////////////////////////////////////////////////////
                        INTERNAL VALIDATION
    //////////////////////////////////////////////////////////////*/

    /**
     * @dev Validates royalty recipients.
     */
    function _validateRecipients(
        RoyaltyRecipient[] calldata recipients
    )
        internal
        pure
    {
        uint256 totalShares;

        if (recipients.length == 0)
            revert InvalidRecipient();

        if (recipients.length > MAX_RECIPIENTS)
            revert TooManyRecipients();

        for (uint256 i = 0; i < recipients.length; i++) {

            if (
                recipients[i].wallet
                == address(0)
            )
                revert InvalidRecipient();

            if (
                recipients[i].shareBps == 0
            )
                revert InvalidRoyaltyShare();

            totalShares +=
                recipients[i].shareBps;

            // Duplicate wallet check
            for (
                uint256 j = i + 1;
                j < recipients.length;
                j++
            ) {

                if (
                    recipients[i].wallet
                    ==
                    recipients[j].wallet
                )
                    revert DuplicateRecipient();
            }
        }

        if (
            totalShares
            !=
            BPS_DENOMINATOR
        )
            revert InvalidTotalShares();
    }

    /**
     * @dev Calculates royalty pool after
     *      deducting platform fee.
     */
    function _royaltyPool(
        uint256 amount
    )
        internal
        view
        returns (uint256)
    {
        return amount
            - calculatePlatformFee(amount);
    }

    /*//////////////////////////////////////////////////////////////
                     ROYALTY DISTRIBUTION ENGINE
    //////////////////////////////////////////////////////////////*/

    /**
     * @notice Distributes royalty payments.
     * @dev Marketplace must transfer the payment tokens
     *      to this contract before calling this function.
     */
    function distributeRoyalty(
        RoyaltyRecipient[] calldata recipients,
        uint256 totalAmount
    )
        external
        override
        nonReentrant
    {
        if (totalAmount == 0)
            revert InvalidAmount();

        _validateRecipients(recipients);

        //----------------------------------------------------------
        // Calculate amounts
        //----------------------------------------------------------

        uint256 platformFee =
            calculatePlatformFee(totalAmount);

        uint256 royaltyAmount =
            totalAmount - platformFee;

        //----------------------------------------------------------
        // Pay Platform
        //----------------------------------------------------------

        if (platformFee > 0) {

            usdc.safeTransfer(
                treasury,
                platformFee
            );

            emit PlatformFeePaid(
                treasury,
                platformFee
            );
        }

        //----------------------------------------------------------
        // Pay Royalty Recipients
        //----------------------------------------------------------

        for (
            uint256 i = 0;
            i < recipients.length;
            i++
        ) {

            uint256 payment =
                (royaltyAmount *
                    recipients[i].shareBps)
                / BPS_DENOMINATOR;

            usdc.safeTransfer(
                recipients[i].wallet,
                payment
            );

            emit RecipientPaid(
                recipients[i].wallet,
                payment
            );
        }

        //----------------------------------------------------------
        // Emit Final Event
        //----------------------------------------------------------

        emit RoyaltyDistributed(
            totalAmount
        );
    }
        /*//////////////////////////////////////////////////////////////
                            VIEW FUNCTIONS
    //////////////////////////////////////////////////////////////*/

    /**
     * @notice Returns the USDC token address used for payments.
     */
    function usdcToken()
        external
        view
        returns (address)
    {
        return address(usdc);
    }

    /**
     * @notice Returns the royalty pool after deducting
     *         the platform fee.
     * @param totalAmount Purchase amount.
     */
    function getroyaltyPool(
        uint256 totalAmount
    )
        external
        view
        returns (uint256)
    {
        return _royaltyPool(totalAmount);
    }
}
