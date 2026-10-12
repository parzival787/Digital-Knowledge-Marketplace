"""Block-pinned market denomination; KnowledgeAsset's reference price stays USDC."""
import re

from web3 import Web3

from .settlement import SETTLEMENT_ABI, function_abi

TOKEN_ABI = [function_abi("symbol", [], ["string"]), function_abi("name", [], ["string"]),
             function_abi("decimals", [], ["uint8"])]


def parse_units(value, decimals):
    """Exact unsigned decimal parsing without float or Decimal context rounding."""
    if type(decimals) is not int or not 0 <= decimals <= 77:
        raise ValueError("Invalid token decimals")
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value):
        raise ValueError("Invalid token amount")
    whole, _, fraction = value.partition(".")
    if len(fraction) > decimals:
        raise ValueError("Too many fractional digits")
    amount = int(whole) * 10**decimals + int(fraction.ljust(decimals, "0") or "0")
    if amount >= 2**256:
        raise ValueError("Token amount exceeds uint256")
    return amount


def market_profile(w3, address, registry_address, current_address, block=None):
    if w3.eth.chain_id != 80002:
        raise ValueError("Unexpected chain")
    block = w3.eth.block_number if block is None else block
    market = w3.eth.contract(address=Web3.to_checksum_address(address), abi=SETTLEMENT_ABI + [
        function_abi("paused", [], ["bool"]), function_abi("royaltySplitter", [], ["address"]),
        function_abi("totalAuctionsCreated", [], ["uint256"])])
    def read(fn):
        return fn.call(block_identifier=block)
    if not w3.eth.get_code(market.address, block_identifier=block):
        raise ValueError("Missing marketplace code")
    if read(market.functions.knowledgeAsset()).lower() != registry_address.lower():
        raise ValueError("Registry mismatch")
    token_address = read(market.functions.usdc())
    if not w3.eth.get_code(token_address, block_identifier=block):
        raise ValueError("Missing payment token code")
    token = w3.eth.contract(address=token_address, abi=TOKEN_ABI)
    decimals = read(token.functions.decimals())
    if type(decimals) is not int or not 0 <= decimals <= 77:
        raise ValueError("Unsupported payment token decimals")
    symbol, name = read(token.functions.symbol()), read(token.functions.name())
    if not isinstance(symbol, str) or not 0 < len(symbol) <= 32 or not isinstance(name, str) or not 0 < len(name) <= 128:
        raise ValueError("Invalid token metadata")
    paused = read(market.functions.paused())
    splitter_address = read(market.functions.royaltySplitter())
    if not w3.eth.get_code(splitter_address, block_identifier=block):
        raise ValueError("Missing royalty splitter code")
    splitter = w3.eth.contract(address=splitter_address, abi=[function_abi("usdc", [], ["address"]), function_abi("marketplace", [], ["address"])])
    if read(splitter.functions.usdc()).lower() != token_address.lower() or read(splitter.functions.marketplace()).lower() != market.address.lower():
        raise ValueError("Royalty splitter wiring mismatch")
    auction_count = read(market.functions.totalAuctionsCreated())
    if type(auction_count) is not int or auction_count < 0:
        raise ValueError("Auction interface unavailable")
    return {"address": market.address, "chain_id": 80002, "token_address": token_address,
            "symbol": symbol, "name": name, "decimals": decimals,
            "splitter_address": splitter_address,
            "environment": "sandbox", "current": market.address.lower() == current_address.lower(),
            "legacy": market.address.lower() != current_address.lower(), "paused": paused,
            "purchase_enabled": not paused, "auction_enabled": True, "new_bids_enabled": not paused}
