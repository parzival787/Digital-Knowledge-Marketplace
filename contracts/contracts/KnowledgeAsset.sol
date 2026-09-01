// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/* ============================================================
 * KnowledgeAsset v2.0
 * Decentralized Knowledge Marketplace (DKM)
 *
 * Responsibilities:
 * - Mint one NFT per knowledge asset (dataset / research / course)
 * - Store pricing, licensing, and quality metadata
 * - Let sellers manage price and active status of their listings
 * ============================================================
 */

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

/// @title KnowledgeAsset
/// @notice ERC721 representing a single sellable piece of knowledge
///         (dataset, paper, course, etc.) in the DKM marketplace.
/// @dev Each token's off-chain content lives on IPFS; only the CIDs
///      and sale-relevant metadata are stored on-chain.
/// @dev Intentionally has no owner/admin role: minting is permissionless
///      (anyone can mint their own asset) and every mutation (price
///      update, deactivation) is gated by NFT ownership via `ownerOf`,
///      not by a central admin. If moderation or global parameter
///      control is needed later, add `Ownable` back deliberately along
///      with the specific `onlyOwner` functions that need it.
contract KnowledgeAsset is ERC721 {

    /*//////////////////////////////////////////////////////////////
                                ERRORS
    //////////////////////////////////////////////////////////////*/

    error EmptyIPFSCID();
    error EmptyMetadataCID();
    error PriceTooLow(uint256 price, uint256 minimum);
    error PriceTooHigh(uint256 price, uint256 maximum);
    error QualityScoreTooHigh(uint256 score, uint256 maximum);
    error AssetDoesNotExist(uint256 tokenId);
    error NotAssetOwner();
    error AssetInactive();
    error AlreadyInactive();
    error NonTransferable();

    /*//////////////////////////////////////////////////////////////
                               CONSTANTS
    //////////////////////////////////////////////////////////////*/

    /// @notice Minimum listing price, in USDC base units (6 decimals).
    uint256 public constant MIN_PRICE_USDC = 1_000_000; // 1 USDC

    /// @notice Maximum listing price, in USDC base units (6 decimals).
    uint256 public constant MAX_PRICE_USDC = 100_000_000; // 100 USDC

    /// @notice Maximum allowed quality score (inclusive).
    uint8 public constant MAX_QUALITY_SCORE = 100;

    /*//////////////////////////////////////////////////////////////
                                TYPES
    //////////////////////////////////////////////////////////////*/

    /// @notice Licensing terms attached to an asset.
    enum License {
        OpenAccess,
        SingleUse,
        Commercial
    }

    /// @notice On-chain record for a single knowledge asset.
    /// @dev Field order is chosen so `creator`, `license`, `qualityScore`,
    ///      `active`, and `mintedAt` (20 + 1 + 1 + 1 + 5 = 28 bytes) pack
    ///      into a single 32-byte storage slot. `priceUSDC` gets its own
    ///      slot since USDC amounts need full-width headroom. `ipfsCID`
    ///      and `metadataCID` are dynamic types and always occupy their
    ///      own slot(s) regardless of position.
    struct Asset {
        string ipfsCID;
        string metadataCID;
        uint256 priceUSDC;
        address creator;
        License license;
        uint8 qualityScore;
        bool active;
        uint40 mintedAt;
    }

    /*//////////////////////////////////////////////////////////////
                                STORAGE
    //////////////////////////////////////////////////////////////*/

    /// @dev Sequential token id counter. Starts at 0; first minted
    ///      token is id 1.
    uint256 private _tokenIds;

    /// @dev Private so all reads go through `getAsset`, which performs
    ///      an explicit existence check. Use `getAsset(tokenId)` rather
    ///      than relying on an auto-generated mapping getter.
    mapping(uint256 => Asset) private _assets;

    /*//////////////////////////////////////////////////////////////
                                EVENTS
    //////////////////////////////////////////////////////////////*/

    event AssetMinted(
        uint256 indexed tokenId,
        address indexed creator,
        string ipfsCID,
        uint256 priceUSDC,
        License license
    );

    event AssetDeactivated(uint256 indexed tokenId);

    event PriceUpdated(
        uint256 indexed tokenId,
        uint256 newPrice
    );

    /*//////////////////////////////////////////////////////////////
                              CONSTRUCTOR
    //////////////////////////////////////////////////////////////*/

    constructor() ERC721("KnowledgeAsset", "KNOW") {}

    /*//////////////////////////////////////////////////////////////
                             CORE FUNCTIONS
    //////////////////////////////////////////////////////////////*/

    /// @notice Mints a new knowledge asset NFT to the caller.
    /// @dev Follows checks-effects-interactions: all state is written
    ///      before `_safeMint`'s external `onERC721Received` callback
    ///      fires, so a reentrant call during that callback always sees
    ///      fully-populated asset data.
    /// @param ipfsCID Content CID for the underlying data/content.
    /// @param metadataCID Content CID for the asset's metadata JSON.
    /// @param priceUSDC Listing price in USDC base units (6 decimals).
    /// @param license Licensing terms for buyers.
    /// @param qualityScore Self-reported or curated quality score, 0-100.
    /// @return newId The freshly minted token id.
    function mint(
        string memory ipfsCID,
        string memory metadataCID,
        uint256 priceUSDC,
        License license,
        uint256 qualityScore
    ) external returns (uint256 newId) {

        if (bytes(ipfsCID).length == 0)
            revert EmptyIPFSCID();

        if (bytes(metadataCID).length == 0)
            revert EmptyMetadataCID();

        if (priceUSDC < MIN_PRICE_USDC)
            revert PriceTooLow(priceUSDC, MIN_PRICE_USDC);

        if (priceUSDC > MAX_PRICE_USDC)
            revert PriceTooHigh(priceUSDC, MAX_PRICE_USDC);

        if (qualityScore > MAX_QUALITY_SCORE)
            revert QualityScoreTooHigh(qualityScore, MAX_QUALITY_SCORE);

        unchecked {
            // Cannot realistically overflow: would require ~2^256 mints.
            newId = ++_tokenIds;
        }

        // --- Effects: write all state before the external interaction ---

        _assets[newId] = Asset({
            ipfsCID: ipfsCID,
            metadataCID: metadataCID,
            priceUSDC: priceUSDC,
            creator: msg.sender,
            license: license,
            qualityScore: uint8(qualityScore),
            active: true,
            mintedAt: uint40(block.timestamp)
        });

        emit AssetMinted(
            newId,
            msg.sender,
            ipfsCID,
            priceUSDC,
            license
        );

        // --- Interaction: last, after all effects are committed ---

        _safeMint(msg.sender, newId);
    }

    /// @notice Returns the full on-chain record for `tokenId`.
    /// @dev Reverts with `AssetDoesNotExist` if the token was never
    ///      minted. Uses `_exists` directly rather than `ownerOf`,
    ///      since `ownerOf` already reverts on a missing token before
    ///      any comparison against `address(0)` could run.
    /// @param tokenId Token id to look up.
    /// @return The asset's stored data.
    function getAsset(
        uint256 tokenId
    ) external view returns (Asset memory) {

        if (!_exists(tokenId))
            revert AssetDoesNotExist(tokenId);

        return _assets[tokenId];
    }

    /// @notice Updates the listing price for a token the caller owns.
    /// @dev `ownerOf` reverts on a nonexistent token, so no separate
    ///      existence check is needed here. Reverts if the asset has
    ///      been deactivated.
    /// @param tokenId Token to update.
    /// @param newPrice New price in USDC base units (6 decimals).
    function updatePrice(
        uint256 tokenId,
        uint256 newPrice
    ) external {

        if (ownerOf(tokenId) != msg.sender)
            revert NotAssetOwner();

        if (!_assets[tokenId].active)
            revert AssetInactive();

        if (newPrice < MIN_PRICE_USDC)
            revert PriceTooLow(newPrice, MIN_PRICE_USDC);

        if (newPrice > MAX_PRICE_USDC)
            revert PriceTooHigh(newPrice, MAX_PRICE_USDC);

        _assets[tokenId].priceUSDC = newPrice;

        emit PriceUpdated(tokenId, newPrice);
    }

    /// @notice Marks a token's listing inactive. Does not burn the NFT.
    /// @dev Reverts if the asset is already inactive.
    /// @param tokenId Token to deactivate.
    function deactivate(
        uint256 tokenId    ) external {

        if (ownerOf(tokenId) != msg.sender)
            revert NotAssetOwner();

        if (!_assets[tokenId].active)
            revert AlreadyInactive();

        _assets[tokenId].active = false;

        emit AssetDeactivated(tokenId);
    }


/**
 * @dev Makes the NFT non-transferable.
 *
 * Minting is allowed:
 *      from == address(0)
 *
 * Burning is allowed:
 *      to == address(0)
 *
 * Normal transfers are NOT allowed:
 *      from != address(0)
 *      && to != address(0)
 */
function _beforeTokenTransfer(
    address from,
    address to,
    uint256 firstTokenId,
    uint256 batchSize
)
    internal
    virtual
    override
{
    super._beforeTokenTransfer(
        from,
        to,
        firstTokenId,
        batchSize
    );

    // Allow minting and burning.
    if (from == address(0) || to == address(0)) {
        return;
    }

    // Block normal NFT transfers.
    revert NonTransferable();
}


    /*//////////////////////////////////////////////////////////////
                              VIEW HELPERS
    //////////////////////////////////////////////////////////////*/

    /// @notice Total number of tokens ever minted.
    function totalMinted() external view returns (uint256) {
        return _tokenIds;
    }

    /// @notice ERC721 metadata URI, pointed at the asset's metadata CID.
    /// @dev Overrides the default OZ implementation (which returns
    ///      `baseURI + tokenId` and would otherwise be empty, since no
    ///      base URI is configured).
    /// @param tokenId Token to look up.
    /// @return IPFS URI for the token's metadata JSON.
    function tokenURI(
        uint256 tokenId
    ) public view virtual override returns (string memory) {

        if (!_exists(tokenId))
            revert AssetDoesNotExist(tokenId);

        return string.concat("ipfs://", _assets[tokenId].metadataCID);
    }
}
