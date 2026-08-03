// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/* ============================================================
 * Marketplace v2.1
 * Decentralized Knowledge Marketplace
 *
 * Features:
 * - Fixed Price Sales
 * - Auctions
 * - Automatic Royalty Distribution
 * - ERC721 Transfer
 * - MockUSDC Payments
 * ============================================================
 */

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

import "./interfaces/IKnowledgeAsset.sol";
import "./interfaces/IRoyaltySplitter.sol";

/// @title Marketplace
/// @notice Fixed-price and auction sales for KnowledgeAsset NFTs, paid in
///         USDC, with royalties distributed via RoyaltySplitter.
/// @dev Does not implement `IMarketplace` — that interface's function
///      signatures (`listAsset`, `purchaseAsset`, `cancelListing(tokenId)`)
///      don't match this contract's actual API (`listFixedPrice`,
///      `buyAsset`, `cancelListing(listingId)`) and appear to be stale;
///      the import has been removed since it was unused dead weight.
///      If `IMarketplace` is meant to describe this contract, it needs
///      to be rewritten to match, not the other way around.
contract Marketplace is
    Ownable,
    ReentrancyGuard,
    Pausable
{
    using SafeERC20 for IERC20;

    /*//////////////////////////////////////////////////////////////
                            CUSTOM ERRORS
    //////////////////////////////////////////////////////////////*/

    error InvalidKnowledgeAsset();
    error InvalidRoyaltySplitter();
    error InvalidUSDC();

    error InvalidPrice();
    error NotNFTOwner();
    error MarketplaceNotApproved();
    error AlreadyListed();
    error NoRecipients();
    error InvalidRecipient();
    error InvalidShare();
    error TooManyRecipients();
    error RoyaltyExceedsMaximum();

    error ListingInactive();
    error NotSeller();
    error InvalidSaleType();
    error SellerCannotBuyOwnAsset();
    error SellerNoLongerOwnsNFT();

    error InvalidReservePrice();
    error InvalidAuctionDuration();
    error AuctionAlreadyExists();

    error AuctionInactive();
    error AuctionAlreadyFinalized();
    error AuctionNotStarted();
    error AuctionHasEnded();
    error SellerCannotBid();
    error BelowReservePrice();
    error BidTooLow();
    error AuctionStillRunning();

    error NoRefundOwed();

    /*//////////////////////////////////////////////////////////////
                              ENUMS
    //////////////////////////////////////////////////////////////*/

    enum SaleType {
        FixedPrice,
        Auction
    }

    /*//////////////////////////////////////////////////////////////
                              STRUCTS
    //////////////////////////////////////////////////////////////*/

    /// @dev `listingId` is intentionally not stored here — it's already
    ///      the key of the `listings` mapping, so storing it again would
    ///      just be redundant. `listingExists` uses `tokenId != 0` as
    ///      its existence check instead (KnowledgeAsset token ids start
    ///      at 1, so a real listing can never have `tokenId == 0`).
    /// @dev Field order packs `seller` + `saleType` + `active` +
    ///      `listedAt` (20 + 1 + 1 + 5 = 27 bytes) into one storage slot.
    struct Listing {
        uint256 tokenId;
        uint256 priceUSDC;
        address seller;
        SaleType saleType;
        bool active;
        uint40 listedAt;
    }

    /// @dev Same reasoning as `Listing`: no stored `auctionId`,
    ///      `auctionExists` uses `tokenId != 0` instead. Field order
    ///      packs `seller` + `active` + `finalized` + `startTime` +
    ///      `endTime` (20 + 1 + 1 + 5 + 5 = 32 bytes) into one slot.
    struct Auction {
        uint256 tokenId;
        uint256 reservePrice;
        uint256 highestBid;
        address highestBidder;
        address seller;
        bool active;
        bool finalized;
        uint40 startTime;
        uint40 endTime;
    }

    /// @dev Packs `bidder` + `timestamp` (20 + 5 = 25 bytes) into one
    ///      slot. `amount` keeps its own slot.
    struct Bid {
        uint256 amount;
        address bidder;
        uint40 timestamp;
    }

    /*//////////////////////////////////////////////////////////////
                        MARKETPLACE STORAGE
    //////////////////////////////////////////////////////////////*/

    /// @notice Maximum total royalty share = 20% of the royalty pool.
    /// @dev Mirrors RoyaltySplitter.MAX_ROYALTY_BPS. The seller receives
    ///      whatever remains after the platform fee and royalty recipients
    ///      are paid, so this must stay in sync with the splitter's cap.
    ///      Enforced here too (not just in RoyaltySplitter) so a bad
    ///      royalty config is rejected at listing time, not silently
    ///      accepted and only discovered — with funds and NFT approval
    ///      already committed — when a sale finally tries to settle.
    uint16 public constant MAX_ROYALTY_BPS = 2_000;

    /// @notice Maximum royalty recipients per listing/auction.
    /// @dev Mirrors RoyaltySplitter.MAX_RECIPIENTS. Same rationale as
    ///      `MAX_ROYALTY_BPS` above: without this, a listing could be
    ///      created with more recipients than RoyaltySplitter will ever
    ///      accept, producing a listing that can never actually be sold
    ///      — `buyAsset`/`endAuction` would revert every time.
    uint8 public constant MAX_RECIPIENTS = 10;

    IKnowledgeAsset public immutable knowledgeAsset;

    IRoyaltySplitter public royaltySplitter;

    IERC20 public immutable usdc;

    /// @dev Listing id counter and canonical listing count in one; see
    ///      `totalListingsCreated`. There used to be a separate
    ///      `totalListings` counter incremented in lockstep with this
    ///      one — pure duplication, since the two could never differ.
    ///      Removed to save an SSTORE on every listing.
    uint256 private _listingIds;

    /// @dev Same deal as `_listingIds`; see `totalAuctionsCreated`.
    uint256 private _auctionIds;

    /// listingId => Listing
    mapping(uint256 => Listing) public listings;

    /// tokenId => Active Listing
    mapping(uint256 => uint256) public tokenToListing;

    /// auctionId => Auction
    mapping(uint256 => Auction) public auctions;

    /// tokenId => Active Auction
    mapping(uint256 => uint256) public tokenToAuction;

    /// listingId => Royalty Recipients
    mapping(
        uint256 =>
        IRoyaltySplitter.RoyaltyRecipient[]
    ) private listingRecipients;

    mapping(
        uint256 =>
        IRoyaltySplitter.RoyaltyRecipient[]
    ) private auctionRecipients;

    /// auctionId => Bid History
    mapping(
        uint256 =>
        Bid[]
    ) private auctionBids;

    /// @notice Refunds owed to outbid bidders, withdrawable via
    ///         `withdrawRefund`.
    /// @dev Outbid refunds are no longer pushed automatically in
    ///      `placeBid` — see that function's doc comment for why.
    mapping(address => uint256) public pendingRefunds;

    /*//////////////////////////////////////////////////////////////
                              EVENTS
    //////////////////////////////////////////////////////////////*/

    event AssetListed(
        uint256 indexed listingId,
        uint256 indexed tokenId,
        address indexed seller,
        uint256 price
    );

    event ListingCancelled(
        uint256 indexed listingId
    );

    event PurchaseCompleted(
        uint256 indexed listingId,
        uint256 indexed tokenId,
        address indexed buyer,
        uint256 amount
    );

    event AuctionCreated(
        uint256 indexed tokenId,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime
    );

    event BidPlaced(
        uint256 indexed tokenId,
        address indexed bidder,
        uint256 amount
    );

    event AuctionEnded(
        uint256 indexed tokenId,
        address indexed winner,
        uint256 amount
    );

    /// @notice Emitted when an outbid bidder withdraws their refund.
    event RefundWithdrawn(
        address indexed bidder,
        uint256 amount
    );

    /*//////////////////////////////////////////////////////////////
                            CONSTRUCTOR
    //////////////////////////////////////////////////////////////*/

    constructor(
        address knowledgeAssetAddress,
        address royaltySplitterAddress,
        address usdcAddress
    ) {

        if (knowledgeAssetAddress == address(0))
            revert InvalidKnowledgeAsset();

        if (royaltySplitterAddress == address(0))
            revert InvalidRoyaltySplitter();

        if (usdcAddress == address(0))
            revert InvalidUSDC();

        knowledgeAsset = IKnowledgeAsset(knowledgeAssetAddress);
        royaltySplitter = IRoyaltySplitter(royaltySplitterAddress);
        usdc = IERC20(usdcAddress);
    }

    /*//////////////////////////////////////////////////////////////
                        FIXED PRICE LISTING
    //////////////////////////////////////////////////////////////*/

    /// @notice Lists an NFT for fixed-price sale.
    /// @dev Caller must own the token and have approved this contract
    ///      (directly or via `setApprovalForAll`).
    /// @param tokenId Token to list.
    /// @param priceUSDC Sale price, in USDC base units.
    /// @param recipients Royalty recipients and their basis-point
    ///        shares; total must not exceed `MAX_ROYALTY_BPS`.
    function listFixedPrice(
        uint256 tokenId,
        uint256 priceUSDC,
        IRoyaltySplitter.RoyaltyRecipient[] calldata recipients
    )
        external
        whenNotPaused
        nonReentrant
    {
        if (priceUSDC == 0)
            revert InvalidPrice();

        if (knowledgeAsset.ownerOf(tokenId) != msg.sender)
            revert NotNFTOwner();

        if (
            knowledgeAsset.getApproved(tokenId) != address(this)
            &&
            !knowledgeAsset.isApprovedForAll(msg.sender, address(this))
        )
            revert MarketplaceNotApproved();

        // Prevent duplicate active listing
        uint256 existingListing = tokenToListing[tokenId];

        if (existingListing != 0 && listings[existingListing].active)
            revert AlreadyListed();

        uint256 listingId = ++_listingIds;

        //------------------------------------------------------------
        // Validate + store royalty recipients in a single pass
        //------------------------------------------------------------

        uint256 length = recipients.length;

        if (length == 0)
            revert NoRecipients();

        if (length > MAX_RECIPIENTS)
            revert TooManyRecipients();

        uint256 totalShares;

        for (uint256 i = 0; i < length;) {

            if (recipients[i].wallet == address(0))
                revert InvalidRecipient();

            if (recipients[i].shareBps == 0)
                revert InvalidShare();

            totalShares += recipients[i].shareBps;

            listingRecipients[listingId].push(recipients[i]);

            unchecked {
                ++i;
            }
        }

        if (totalShares > MAX_ROYALTY_BPS)
            revert RoyaltyExceedsMaximum();

        //------------------------------------------------------------

        listings[listingId] = Listing({
            tokenId: tokenId,
            priceUSDC: priceUSDC,
            seller: msg.sender,
            saleType: SaleType.FixedPrice,
            active: true,
            listedAt: uint40(block.timestamp)
        });

        tokenToListing[tokenId] = listingId;

        emit AssetListed(
            listingId,
            tokenId,
            msg.sender,
            priceUSDC
        );
    }

    /// @notice Cancels an active listing.
    /// @dev Only the seller who created the listing may cancel it.
    /// @param listingId Listing to cancel.
    function cancelListing(
        uint256 listingId
    )
        external
        nonReentrant
    {
        Listing storage listing = listings[listingId];

        if (!listing.active)
            revert ListingInactive();

        if (listing.seller != msg.sender)
            revert NotSeller();

        listing.active = false;

        delete tokenToListing[listing.tokenId];

        emit ListingCancelled(listingId);
    }

    /*//////////////////////////////////////////////////////////////
                        BUY FIXED PRICE ASSET
    //////////////////////////////////////////////////////////////*/

    /// @notice Purchases a fixed-price listing.
    /// @dev Follows checks-effects-interactions: the listing is closed
    ///      out (state) before any external calls (payment transfer,
    ///      royalty distribution, NFT transfer) fire, rather than after.
    /// @param listingId Listing to purchase.
    function buyAsset(
        uint256 listingId
    )
        external
        whenNotPaused
        nonReentrant
    {
        Listing storage listing = listings[listingId];

        if (!listing.active)
            revert ListingInactive();

        if (listing.saleType != SaleType.FixedPrice)
            revert InvalidSaleType();

        if (listing.seller == msg.sender)
            revert SellerCannotBuyOwnAsset();

        if (knowledgeAsset.ownerOf(listing.tokenId) != listing.seller)
            revert SellerNoLongerOwnsNFT();

        uint256 price = listing.priceUSDC;
        address seller = listing.seller;
        uint256 tokenId = listing.tokenId;

        //------------------------------------------------------------
        // Effects: close out the listing before any external call
        //------------------------------------------------------------

        listing.active = false;

        delete tokenToListing[tokenId];

        //------------------------------------------------------------
        // Interactions
        //------------------------------------------------------------

        usdc.safeTransferFrom(
            msg.sender,
            address(royaltySplitter),
            price
        );

        royaltySplitter.distributeRoyalty(
            seller,
            listingRecipients[listingId],
            price
        );

        knowledgeAsset.safeTransferFrom(
            seller,
            msg.sender,
            tokenId
        );

        emit PurchaseCompleted(
            listingId,
            tokenId,
            msg.sender,
            price
        );
    }

    /*//////////////////////////////////////////////////////////////
                        CREATE AUCTION
    //////////////////////////////////////////////////////////////*/

    /// @notice Creates an auction for an NFT.
    /// @dev Caller must own the token and have approved this contract.
    /// @param tokenId Token to auction.
    /// @param reservePrice Minimum winning bid, in USDC base units.
    /// @param startTime Unix timestamp bidding opens.
    /// @param endTime Unix timestamp bidding closes; must be after
    ///        `startTime`.
    /// @param recipients Royalty recipients and their basis-point
    ///        shares; total must not exceed `MAX_ROYALTY_BPS`.
    function createAuction(
        uint256 tokenId,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime,
        IRoyaltySplitter.RoyaltyRecipient[] calldata recipients
    )
        external
        whenNotPaused
        nonReentrant
    {
        if (reservePrice == 0)
            revert InvalidReservePrice();

        if (endTime <= startTime)
            revert InvalidAuctionDuration();

        if (knowledgeAsset.ownerOf(tokenId) != msg.sender)
            revert NotNFTOwner();

        if (
            knowledgeAsset.getApproved(tokenId) != address(this)
            &&
            !knowledgeAsset.isApprovedForAll(msg.sender, address(this))
        )
            revert MarketplaceNotApproved();

        if (tokenToAuction[tokenId] != 0)
            revert AuctionAlreadyExists();

        uint256 auctionId = ++_auctionIds;

        //------------------------------------------------------------
        // Validate + store royalty recipients in a single pass
        //------------------------------------------------------------

        uint256 length = recipients.length;

        if (length == 0)
            revert NoRecipients();

        if (length > MAX_RECIPIENTS)
            revert TooManyRecipients();

        uint256 totalShares;

        for (uint256 i = 0; i < length;) {

            if (recipients[i].wallet == address(0))
                revert InvalidRecipient();

            if (recipients[i].shareBps == 0)
                revert InvalidShare();

            totalShares += recipients[i].shareBps;

            auctionRecipients[auctionId].push(recipients[i]);

            unchecked {
                ++i;
            }
        }

        if (totalShares > MAX_ROYALTY_BPS)
            revert RoyaltyExceedsMaximum();

        //------------------------------------------------------------

        auctions[auctionId] = Auction({
            tokenId: tokenId,
            reservePrice: reservePrice,
            highestBid: 0,
            highestBidder: address(0),
            seller: msg.sender,
            active: true,
            finalized: false,
            startTime: uint40(startTime),
            endTime: uint40(endTime)
        });

        tokenToAuction[tokenId] = auctionId;

        emit AuctionCreated(
            tokenId,
            reservePrice,
            startTime,
            endTime
        );
    }

    /*//////////////////////////////////////////////////////////////
                        PLACE BID
    //////////////////////////////////////////////////////////////*/

    /// @notice Places a bid on an active auction.
    /// @dev The previous highest bidder is NOT refunded automatically
    ///      here — their refund is credited to `pendingRefunds` and
    ///      must be withdrawn via `withdrawRefund`. A direct push
    ///      refund would let a single blocklisted address (a real
    ///      possibility with USDC, which supports issuer-level
    ///      blocklisting) permanently jam the auction: if that
    ///      address's `safeTransfer` reverts, this whole function
    ///      would revert, and no one could ever outbid them again.
    ///      The pull pattern decouples the auction's liveness from any
    ///      one bidder's ability to receive funds.
    /// @param auctionId Auction to bid on.
    /// @param amount Bid amount, in USDC base units.
    function placeBid(
        uint256 auctionId,
        uint256 amount
    )
        external
        whenNotPaused
        nonReentrant
    {
        Auction storage auction = auctions[auctionId];

        if (!auction.active)
            revert AuctionInactive();

        if (auction.finalized)
            revert AuctionAlreadyFinalized();

        if (block.timestamp < auction.startTime)
            revert AuctionNotStarted();

        if (block.timestamp >= auction.endTime)
            revert AuctionHasEnded();

        if (msg.sender == auction.seller)
            revert SellerCannotBid();

        if (auction.highestBid == 0) {

            if (amount < auction.reservePrice)
                revert BelowReservePrice();

        } else {

            if (amount <= auction.highestBid)
                revert BidTooLow();
        }

        //------------------------------------------------------------
        // Transfer bidder funds
        //------------------------------------------------------------

        usdc.safeTransferFrom(
            msg.sender,
            address(this),
            amount
        );

        //------------------------------------------------------------
        // Credit the previous highest bidder's refund (pull pattern)
        //------------------------------------------------------------

        if (auction.highestBidder != address(0)) {

            pendingRefunds[auction.highestBidder] +=
                auction.highestBid;
        }

        //------------------------------------------------------------
        // Update Auction
        //------------------------------------------------------------

        auction.highestBid = amount;
        auction.highestBidder = msg.sender;

        auctionBids[auctionId].push(
            Bid({
                amount: amount,
                bidder: msg.sender,
                timestamp: uint40(block.timestamp)
            })
        );

        emit BidPlaced(
            auction.tokenId,
            msg.sender,
            amount
        );
    }

    /// @notice Withdraws any refund owed from being outbid.
    function withdrawRefund()
        external
        nonReentrant
    {
        uint256 amount = pendingRefunds[msg.sender];

        if (amount == 0)
            revert NoRefundOwed();

        pendingRefunds[msg.sender] = 0;

        usdc.safeTransfer(msg.sender, amount);

        emit RefundWithdrawn(msg.sender, amount);
    }

    /*//////////////////////////////////////////////////////////////
                        END AUCTION
    //////////////////////////////////////////////////////////////*/

    /// @notice Settles an auction after its end time.
    /// @dev Already followed checks-effects-interactions correctly in
    ///      the original version — state is closed out before any
    ///      external calls. Left that ordering as-is.
    /// @param auctionId Auction to end.
    function endAuction(
        uint256 auctionId
    )
        external
        whenNotPaused
        nonReentrant
    {
        Auction storage auction = auctions[auctionId];

        if (!auction.active)
            revert AuctionInactive();

        if (auction.finalized)
            revert AuctionAlreadyFinalized();

        if (block.timestamp < auction.endTime)
            revert AuctionStillRunning();

        auction.active = false;
        auction.finalized = true;

        delete tokenToAuction[auction.tokenId];

        //------------------------------------------------------------
        // No bids
        //------------------------------------------------------------

        if (auction.highestBidder == address(0)) {

            emit AuctionEnded(
                auction.tokenId,
                address(0),
                0
            );

            return;
        }

        //------------------------------------------------------------
        // Transfer winning bid to RoyaltySplitter
        //------------------------------------------------------------

        usdc.safeTransfer(
            address(royaltySplitter),
            auction.highestBid
        );

        //------------------------------------------------------------
        // Distribute Royalties
        //------------------------------------------------------------

        royaltySplitter.distributeRoyalty(
            auction.seller,
            auctionRecipients[auctionId],
            auction.highestBid
        );

        //------------------------------------------------------------
        // Transfer NFT
        //------------------------------------------------------------

        knowledgeAsset.safeTransferFrom(
            auction.seller,
            auction.highestBidder,
            auction.tokenId
        );

        emit AuctionEnded(
            auction.tokenId,
            auction.highestBidder,
            auction.highestBid
        );
    }

    /*//////////////////////////////////////////////////////////////
                        ADMIN FUNCTIONS
    //////////////////////////////////////////////////////////////*/

    /// @notice Pauses listing, buying, auctions, and bidding.
    /// @dev Does not pause `cancelListing` or `withdrawRefund` — sellers
    ///      and outbid bidders can still get their own assets/funds back
    ///      while paused.
    function pause()
        external
        onlyOwner
    {
        _pause();
    }

    /// @notice Unpauses the marketplace.
    function unpause()
        external
        onlyOwner
    {
        _unpause();
    }

    /// @notice Points the marketplace at a new RoyaltySplitter.
    /// @dev The new RoyaltySplitter's owner must separately call
    ///      `updateMarketplace(address(this))` on it — that
    ///      authorization is not automatic. See `RoyaltySplitter`'s
    ///      `marketplace` storage variable doc comment.
    /// @param newRoyaltySplitter New RoyaltySplitter address; must be
    ///        non-zero.
    function updateRoyaltySplitter(
        address newRoyaltySplitter
    )
        external
        onlyOwner
    {
        if (newRoyaltySplitter == address(0))
            revert InvalidRoyaltySplitter();

        royaltySplitter = IRoyaltySplitter(newRoyaltySplitter);
    }

    /*//////////////////////////////////////////////////////////////
                        LISTING VIEWS
    //////////////////////////////////////////////////////////////*/

    /// @notice Whether `tokenId` currently has an active listing.
    function isListed(
        uint256 tokenId
    )
        public
        view
        returns (bool)
    {
        uint256 listingId = tokenToListing[tokenId];

        if (listingId == 0)
            return false;

        return listings[listingId].active;
    }

    /// @notice Whether `listingId` was ever created (active or not).
    /// @dev See the `Listing` struct's doc comment for why this checks
    ///      `tokenId != 0` instead of a dedicated id field.
    function listingExists(
        uint256 listingId
    )
        public
        view
        returns (bool)
    {
        return listings[listingId].tokenId != 0;
    }

    /*//////////////////////////////////////////////////////////////
                        AUCTION VIEWS
    //////////////////////////////////////////////////////////////*/

    /// @notice Whether `tokenId` currently has an active auction.
    function isAuctionActive(
        uint256 tokenId
    )
        public
        view
        returns (bool)
    {
        uint256 auctionId = tokenToAuction[tokenId];

        if (auctionId == 0)
            return false;

        return auctions[auctionId].active;
    }

    /// @notice Whether `auctionId` was ever created (active or not).
    /// @dev See the `Auction` struct's doc comment for why this checks
    ///      `tokenId != 0` instead of a dedicated id field.
    function auctionExists(
        uint256 auctionId
    )
        public
        view
        returns (bool)
    {
        return auctions[auctionId].tokenId != 0;
    }

    /*//////////////////////////////////////////////////////////////
                        BID HISTORY
    //////////////////////////////////////////////////////////////*/

    /// @notice Full bid history for an auction.
    function getAuctionBids(
        uint256 auctionId
    )
        external
        view
        returns (Bid[] memory)
    {
        return auctionBids[auctionId];
    }

    /*//////////////////////////////////////////////////////////////
                    ROYALTY RECIPIENTS
    //////////////////////////////////////////////////////////////*/

    /// @notice Royalty recipients configured for a listing.
    function getListingRecipients(
        uint256 listingId
    )
        external
        view
        returns (IRoyaltySplitter.RoyaltyRecipient[] memory)
    {
        return listingRecipients[listingId];
    }

    /// @notice Royalty recipients configured for an auction.
    function getAuctionRecipients(
        uint256 auctionId
    )
        external
        view
        returns (IRoyaltySplitter.RoyaltyRecipient[] memory)
    {
        return auctionRecipients[auctionId];
    }

    /*//////////////////////////////////////////////////////////////
                        STATISTICS
    //////////////////////////////////////////////////////////////*/

    /// @notice Total listings ever created (active or not).
    function totalListingsCreated()
        external
        view
        returns (uint256)
    {
        return _listingIds;
    }

    /// @notice Total auctions ever created (active or not).
    function totalAuctionsCreated()
        external
        view
        returns (uint256)
    {
        return _auctionIds;
    }
}
