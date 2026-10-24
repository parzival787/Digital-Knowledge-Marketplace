"""Bounded, read-only fixed-price activity from the configured Marketplace."""
from web3 import Web3
import os
from . import blockchain
from .payments.settlement import SETTLEMENT_ABI

PURCHASE_EVENT = {"type": "event", "name": "PurchaseCompleted", "anonymous": False, "inputs": [
    {"name": "listingId", "type": "uint256", "indexed": True},
    {"name": "tokenId", "type": "uint256", "indexed": True},
    {"name": "buyer", "type": "address", "indexed": True},
    {"name": "amount", "type": "uint256", "indexed": False},
]}


def account_activity(wallet: str, before_block: int | None = None):
    w3 = blockchain.w3
    if w3.eth.chain_id != 80002:
        raise ValueError("Unexpected network")
    head = max(0, w3.eth.block_number - 2)
    end = min(head, before_block) if before_block is not None else head
    page_size = max(1, min(2000, int(os.getenv("RPC_LOG_PAGE_SIZE", "10"))))
    start = max(0, end - page_size + 1)
    rows = []
    markets = blockchain.entitlement_markets()
    event_count = 0
    for configured in markets:
        market = w3.eth.contract(address=configured.address, abi=SETTLEMENT_ABI + [PURCHASE_EVENT])
        events = market.events.PurchaseCompleted().get_logs(from_block=start, to_block=end)
        event_count += len(events)
        # shortcut: bounded RPC pages, use an event indexer for lifetime totals.
        if event_count > 200:
            raise ValueError("Activity page is too busy")
        for event in events:
            args = event["args"]
            if not blockchain.market_token_supported(market.address, args["tokenId"]):
                continue
            listing = market.functions.listings(args["listingId"]).call()
            selling = listing[2].lower() == wallet.lower()
            buying = args["buyer"].lower() == wallet.lower()
            if not (selling or buying):
                continue
            rows.append({"token_id": int(args["tokenId"]), "kind": "sale" if selling else "purchase",
                "amount_base_units": str(args["amount"]), "block": event["blockNumber"],
                "transaction_hash": Web3.to_hex(event["transactionHash"]), "log_index": event["logIndex"],
                "marketplace": market.address})
    rows.sort(key=lambda row: (row["block"], row["log_index"]), reverse=True)
    return {"activity": rows, "from_block": start, "to_block": end,
        "next_before_block": start - 1 if start else None,
        "marketplace": blockchain.marketplace.address, "marketplaces": [market.address for market in markets], "chain_id": 80002}
