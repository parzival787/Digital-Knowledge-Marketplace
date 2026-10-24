// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./KnowledgeAsset.sol";

/// @notice Read-through registry for a fixed legacy prefix; new NFTs start after it.
/// @dev Original NFTs and licenses remain at their original contract addresses.
contract KnowledgeAssetSuccessor is KnowledgeAsset {
    KnowledgeAsset public immutable legacyRegistry;
    uint256 public immutable legacyTokenLimit;

    constructor(address previous) {
        require(previous.code.length > 0, "Missing legacy registry");
        legacyRegistry = KnowledgeAsset(previous);
        uint256 count = legacyRegistry.totalMinted();
        require(count <= 1000, "Legacy prefix too large");
        legacyTokenLimit = count;
        _tokenIds = count;
    }

    function _ownerOf(uint256 id) internal view override returns (address) {
        if (id > 0 && id <= legacyTokenLimit) return legacyRegistry.ownerOf(id);
        return super._ownerOf(id);
    }

    function balanceOf(address owner) public view override returns (uint256 count) {
        count = super.balanceOf(owner);
        for (uint256 id = 1; id <= legacyTokenLimit; ++id) {
            if (legacyRegistry.ownerOf(id) == owner) ++count;
        }
    }

    function getAsset(uint256 id) public view override returns (Asset memory) {
        if (id > 0 && id <= legacyTokenLimit) return legacyRegistry.getAsset(id);
        return super.getAsset(id);
    }

    function tokenURI(uint256 id) public view override returns (string memory) {
        if (id > 0 && id <= legacyTokenLimit) return legacyRegistry.tokenURI(id);
        return super.tokenURI(id);
    }
}
