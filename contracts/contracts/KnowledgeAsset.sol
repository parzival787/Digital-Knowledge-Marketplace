// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract KnowledgeAsset is ERC721, Ownable {

    uint256 private _tokenIds;

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

    mapping(uint256 => Asset) public assets;

    event AssetMinted(
        uint256 indexed tokenId,
        address indexed seller,
        string ipfsCID,
        uint256 priceUSDC,
        License license
    );

    event AssetDeactivated(uint256 indexed tokenId);

    event PriceUpdated(
        uint256 indexed tokenId,
        uint256 newPrice
    );

    constructor()
        ERC721("KnowledgeAsset", "KNOW")
        
    {}

    function mint(
        string memory ipfsCID,
        string memory metadataCID,
        uint256 priceUSDC,
        License license,
        uint256 qualityScore
    ) external returns (uint256) {

        require(bytes(ipfsCID).length > 0, "IPFS CID cannot be empty");
        require(priceUSDC >= 1_000_000, "Minimum price is 1 USDC");
        require(priceUSDC <= 100_000_000, "Maximum price is 100 USDC");
        require(qualityScore <= 100, "Quality score must be 0 to 100");

        _tokenIds++;
        uint256 newId = _tokenIds;

        _safeMint(msg.sender, newId);

        assets[newId] = Asset({
            ipfsCID: ipfsCID,
            metadataCID: metadataCID,
            priceUSDC: priceUSDC,
            license: license,
            seller: msg.sender,
            qualityScore: qualityScore,
            mintedAt: block.timestamp,
            active: true
        });

        emit AssetMinted(
            newId,
            msg.sender,
            ipfsCID,
            priceUSDC,
            license
        );

        return newId;
    }

    function getAsset(
        uint256 tokenId
    ) external view returns (Asset memory) {

        require(ownerOf(tokenId) != address(0), "Token does not exist");

        return assets[tokenId];
    }

    function updatePrice(
        uint256 tokenId,
        uint256 newPrice
    ) external {

        require(
            ownerOf(tokenId) == msg.sender,
            "Only the NFT owner can update the price"
        );

        require(
            newPrice >= 1_000_000,
            "Minimum price is 1 USDC"
        );

        assets[tokenId].priceUSDC = newPrice;

        emit PriceUpdated(tokenId, newPrice);
    }

    function deactivate(
        uint256 tokenId
    ) external {

        require(
            ownerOf(tokenId) == msg.sender,
            "Only the NFT owner can deactivate"
        );

        assets[tokenId].active = false;

        emit AssetDeactivated(tokenId);
    }

    function totalMinted()
        external
        view
        returns (uint256)
    {
        return _tokenIds;
    }
}