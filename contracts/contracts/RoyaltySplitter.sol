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

/// @title RoyaltySplitter
/// @notice Holds USDC forwarded from Marketplace for a sale, deducts a
///         platform fee, pays royalty recipients their configured
///         shares, and sends the remainder to the seller.
/// @dev `distributeRoyalty` is restricted to the configured
///      `marketplace` address — see that variable's doc comment.
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
    error InvalidAmount();
    error TooManyRecipients();
    error DuplicateRecipient();
    error InvalidSeller();
    error SellerCannotBeRecipient();
    error RoyaltyExceedsMaximum();
    error InvalidMarketplace();
    error NotMarketplace();

    /*//////////////////////////////////////////////////////////////
                              CONSTANTS
    //////////////////////////////////////////////////////////////*/

    /// @notice 100%
    uint16 public constant BPS_DENOMINATOR = 10_000;

    /// @notice Maximum platform fee = 10%
    uint16 public constant MAX_PLATFORM_FEE = 1_000;

    /// @notice Maximum royalty recipients
    uint8 public constant MAX_RECIPIENTS = 10;

    /// @notice Maximum total royalty share = 20% of the royalty pool.
    ///         The seller receives whatever remains after the platform
    ///         fee and royalty recipients are paid.
    uint16 public constant MAX_ROYALTY_BPS = 2_000;

    /*//////////////////////////////////////////////////////////////
                               STORAGE
    //////////////////////////////////////////////////////////////*/

    /// @notice ERC20 payment token (MockUSDC / USDC)
    IERC20 public immutable usdc;

    /// @inheritdoc IRoyaltySplitter
    address public override treasury;

    /// @inheritdoc IRoyaltySplitter
    uint16 public override platformFeeBps;

    /// @inheritdoc IRoyaltySplitter
    /// @dev Not set in the constructor because of a circular deployment
    ///      dependency: Marketplace's constructor takes this contract's
    ///      address, so this contract must exist first and can't yet
    ///      know Marketplace's address. Set it once via
    ///      `updateMarketplace` right after Marketplace is deployed.
    ///      `distributeRoyalty` reverts for any other caller until then.
    address public override marketplace;

    /*//////////////////////////////////////////////////////////////
                                EVENTS
    //////////////////////////////////////////////////////////////*/

    /*//////////////////////////////////////////////////////////////
                              MODIFIERS
    //////////////////////////////////////////////////////////////*/

    /// @dev Restricts `distributeRoyalty` to the configured Marketplace.
    ///      Without this, `distributeRoyalty` had no access control at
    ///      all: anyone could call it directly and redirect whatever
    ///      USDC balance this contract happened to hold (e.g. dust,
    ///      or a not-yet-distributed transfer) to a `seller` and
    ///      `recipients` of their own choosing.
    modifier onlyMarketplace() {
        if (msg.sender != marketplace)
            revert NotMarketplace();
        _;
    }

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

    /// @notice Calculates the platform fee for a sale amount.
    /// @param amount Purchase amount, in USDC base units.
    /// @return The platform's cut, in USDC base units.
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

    /// @notice Calculates the royalty pool for a sale amount, i.e.
    ///         `amount` minus the platform fee.
    /// @dev This is NOT the seller's take-home amount — royalty
    ///      recipients are paid out of this pool first, and the seller
    ///      receives whatever remains after that (see
    ///      `distributeRoyalty`). Renamed from `calculateSellerAmount`,
    ///      which was misleading: the seller does not receive the full
    ///      pool.
    /// @param amount Purchase amount, in USDC base units.
    /// @return The royalty pool, in USDC base units.
    function calculateRoyaltyPool(
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

    /// @notice Updates the treasury wallet that receives platform fees.
    /// @dev Only callable by the owner.
    /// @param newTreasury New treasury address; must be non-zero.
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

    /// @notice Updates the platform fee.
    /// @dev Fee is stored in basis points. Only callable by the owner.
    /// @param newFeeBps New fee, in basis points; must not exceed
    ///        `MAX_PLATFORM_FEE`.
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

    /// @notice Updates the only address allowed to call
    ///         `distributeRoyalty`.
    /// @dev Only callable by the owner. Must be called once, after
    ///      Marketplace is deployed, before any sale can settle — see
    ///      the `marketplace` storage variable's doc comment for why
    ///      this can't just be a constructor argument.
    /// @param newMarketplace New authorized caller; must be non-zero.
    function updateMarketplace(
        address newMarketplace
    )
        external
        override
        onlyOwner
    {
        if (newMarketplace == address(0))
            revert InvalidMarketplace();

        address oldMarketplace = marketplace;

        marketplace = newMarketplace;

        emit MarketplaceUpdated(
            oldMarketplace,
            newMarketplace
        );
    }

    /*//////////////////////////////////////////////////////////////
                        INTERNAL VALIDATION
    //////////////////////////////////////////////////////////////*/

    /// @dev Validates royalty recipients: non-empty, within
    ///      `MAX_RECIPIENTS`, no zero addresses, no duplicates, none
    ///      equal to `seller`, no zero shares, and total shares within
    ///      `MAX_ROYALTY_BPS`.
    /// @param seller The address that will receive the remainder of the
    ///        royalty pool; recipients may not also be the seller.
    /// @param recipients Royalty recipients and their basis-point
    ///        shares.
    function _validateRecipients(
        address seller,
        RoyaltyRecipient[] calldata recipients
    )
        internal
        pure
    {
        uint256 length = recipients.length;

        if (length > MAX_RECIPIENTS)
    revert TooManyRecipients();

        uint256 totalShares;

        for (uint256 i = 0; i < length;) {

            if (
                recipients[i].wallet
                == address(0)
            )
                revert InvalidRecipient();

            if (
                recipients[i].wallet
                == seller
            )
                revert SellerCannotBeRecipient();

            if (
                recipients[i].shareBps == 0
            )
                revert InvalidRoyaltyShare();

            totalShares +=
                recipients[i].shareBps;

            // Duplicate wallet check. Bounded by MAX_RECIPIENTS (10),
            // so this is at most 45 comparisons — not a DoS vector.
            for (
                uint256 j = i + 1;
                j < length;
                j++
            ) {

                if (
                    recipients[i].wallet
                    ==
                    recipients[j].wallet
                )
                    revert DuplicateRecipient();
            }

            unchecked {
                // Bounded by `length <= MAX_RECIPIENTS`; can't overflow.
                ++i;
            }
        }

        // Royalty recipients may not claim more than
        // MAX_ROYALTY_BPS of the royalty pool. Whatever
        // is left over goes to the seller.
        if (
            totalShares
            >
            MAX_ROYALTY_BPS
        )
            revert RoyaltyExceedsMaximum();
    }

    /*//////////////////////////////////////////////////////////////
                     ROYALTY DISTRIBUTION ENGINE
    //////////////////////////////////////////////////////////////*/

    /// @notice Distributes a sale's proceeds: platform fee to treasury,
    ///         royalty shares to recipients, and the remainder to the
    ///         seller.
    /// @dev Caller must be the configured `marketplace`, and must have
    ///      already transferred `totalAmount` of `usdc` to this
    ///      contract before calling.
    /// @param seller Receives the royalty pool remainder after
    ///        recipients are paid. Must be non-zero and must not also
    ///        appear in `recipients`.
    /// @param recipients Royalty recipients and their basis-point
    ///        shares of the royalty pool; total must not exceed
    ///        `MAX_ROYALTY_BPS`.
    /// @param totalAmount Total sale amount, in USDC base units.
    function distributeRoyalty(
        address seller,
        RoyaltyRecipient[] calldata recipients,
        uint256 totalAmount
    )
        external
        override
        onlyMarketplace
        nonReentrant
    {
        if (seller == address(0))
            revert InvalidSeller();

        if (totalAmount == 0)
            revert InvalidAmount();

        _validateRecipients(seller, recipients);

        //----------------------------------------------------------
        // Calculate amounts
        //----------------------------------------------------------

        uint256 platformFee =
            calculatePlatformFee(totalAmount);

        uint256 royaltyAmount =
            totalAmount - platformFee;

        uint256 recipientsPaid;

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

        uint256 length = recipients.length;

        for (uint256 i = 0; i < length;) {

            uint256 payment =
                (royaltyAmount *
                    recipients[i].shareBps)
                / BPS_DENOMINATOR;

            recipientsPaid += payment;

            usdc.safeTransfer(
                recipients[i].wallet,
                payment
            );

            emit RecipientPaid(
                recipients[i].wallet,
                payment
            );

            unchecked {
                // Bounded by `length <= MAX_RECIPIENTS`; can't overflow.
                ++i;
            }
        }

        //----------------------------------------------------------
        // Pay Seller (remainder of the royalty pool)
        //----------------------------------------------------------

        uint256 sellerAmount =
            royaltyAmount - recipientsPaid;

        if (sellerAmount > 0) {

            usdc.safeTransfer(
                seller,
                sellerAmount
            );

            emit SellerPaid(
                seller,
                sellerAmount
            );
        }

        //----------------------------------------------------------
        // Emit Final Event
        //----------------------------------------------------------

        emit RoyaltyDistributed(
            totalAmount
        );
    }
}
