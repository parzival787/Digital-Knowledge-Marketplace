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

    function calculatePlatformFee(
        uint256 amount
    )
        external
        view
        returns (uint256);

    function calculateSellerAmount(
        uint256 amount
    )
        external
        view
        returns (uint256);

    function distributeRoyalty(
        RoyaltyRecipient[] calldata recipients,
        uint256 totalAmount
    )
        external;

    function updatePlatformFee(
        uint16 newFeeBps
    )
        external;

    function updateTreasury(
        address newTreasury
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
}