// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IKnowledgeAsset {

    enum License {
        OpenAccess,
        SingleUse,
        Commercial
    }

    struct Asset {
        string ipfsCID;
        string metadataCID;
        uint256 priceUSDC;
        License license;
        address seller;
        uint256 qualityScore;
        uint256 mintedAt;
        bool active;
    }

    function mint(
        string calldata ipfsCID,
        string calldata metadataCID,
        uint256 priceUSDC,
        License license,
        uint256 qualityScore
    ) external returns (uint256);

    function getAsset(
        uint256 tokenId
    ) external view returns (Asset memory);

    function ownerOf(
        uint256 tokenId
    ) external view returns (address);

    function safeTransferFrom(
        address from,
        address to,
        uint256 tokenId
    ) external;

    function updatePrice(
        uint256 tokenId,
        uint256 newPrice
    ) external;

    function deactivate(
        uint256 tokenId
    ) external;

    function totalMinted()
        external
        view
        returns (uint256);
}