// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IRoyaltySplitter {

    struct RoyaltyRecipient {
        address wallet;
        uint16 shareBps;
    }

    event RoyaltyDistributed(
        uint256 totalAmount
    );

    event RecipientPaid(
        address indexed recipient,
        uint256 amount
    );

    event PlatformFeePaid(
        address indexed treasury,
        uint256 amount
    );

    event PlatformFeeUpdated(
        uint16 oldFee,
        uint16 newFee
    );

    event TreasuryUpdated(
        address indexed oldTreasury,
        address indexed newTreasury
    );

    /// @notice Emitted when the seller is paid the remainder of the
    ///         royalty pool after the platform fee and recipients.
    event SellerPaid(
        address indexed seller,
        uint256 amount
    );

    /// @notice Emitted when the authorized marketplace caller changes.
    event MarketplaceUpdated(
        address indexed oldMarketplace,
        address indexed newMarketplace
    );

    function calculatePlatformFee(
        uint256 amount
    )
        external
        view
        returns (uint256);

    /// @notice Returns the royalty pool available to recipients + seller
    ///         for a given sale amount, i.e. `amount` minus the platform
    ///         fee. Does NOT return the seller's actual take-home amount
    ///         — recipients are paid out of this pool first, and the
    ///         seller receives whatever remains.
    function calculateRoyaltyPool(
        uint256 amount
    )
        external
        view
        returns (uint256);

    function distributeRoyalty(
    address seller,
    RoyaltyRecipient[] calldata recipients,
    uint256 totalAmount
    ) external;

    function updatePlatformFee(
        uint16 newFeeBps
    )
        external;

    function updateTreasury(
        address newTreasury
    )
        external;

    /// @notice Updates the only address allowed to call
    ///         `distributeRoyalty`.
    function updateMarketplace(
        address newMarketplace
    )
        external;

    function treasury()
        external
        view
        returns (address);

    function platformFeeBps()
        external
        view
        returns (uint16);

    /// @notice The only address allowed to call `distributeRoyalty`.
    function marketplace()
        external
        view
        returns (address);
}