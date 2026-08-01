// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IMarketplace {

    event AssetListed(
        uint256 indexed tokenId,
        address indexed seller,
        uint256 priceUSDC
    );

    event AssetPurchased(
        uint256 indexed tokenId,
        address indexed buyer,
        uint256 priceUSDC
    );

    event ListingCancelled(
        uint256 indexed tokenId
    );

    function listAsset(
        uint256 tokenId,
        uint256 priceUSDC
    ) external;

    function purchaseAsset(
        uint256 tokenId
    ) external;

    function cancelListing(
        uint256 tokenId
    ) external;
}