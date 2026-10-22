"""Find confirmed on-chain content without trusting a client-supplied token ID."""
def find_mint(registry, block, file_cid, metadata_cid, creator):
    count = registry.functions.totalMinted().call(block_identifier=block)
    # shortcut: bounded demo catalog scan; use an indexed mint lookup above 100 assets.
    if count > 100:
        raise ValueError("Automatic recovery requires an indexed lookup for this catalog. Use the confirmed token ID under advanced recovery.")
    for token in range(1, count + 1):
        asset = registry.functions.getAsset(token).call(block_identifier=block)
        if asset[0] == file_cid and asset[1] == metadata_cid and asset[3].lower() == creator.lower():
            return token
    return None
