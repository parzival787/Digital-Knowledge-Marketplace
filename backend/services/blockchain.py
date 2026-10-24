import os

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from dotenv import load_dotenv

from .knowledge_asset_abi import KNOWLEDGE_ASSET_ABI

from .marketplace_abi import MARKETPLACE_ABI


load_dotenv()


RPC_URL = os.getenv("BLOCKCHAIN_RPC_URL")
CHAIN_ID = int(os.getenv("BLOCKCHAIN_CHAIN_ID", "0"))

if not RPC_URL:
    raise RuntimeError("BLOCKCHAIN_RPC_URL is not configured")


w3 = Web3(
    Web3.HTTPProvider(RPC_URL)
)
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)


def check_blockchain_connection():

    if not w3.is_connected():
        raise RuntimeError(
            "Unable to connect to Polygon Amoy RPC"
        )

    actual_chain_id = w3.eth.chain_id

    if actual_chain_id != CHAIN_ID:
        raise RuntimeError(
            f"Wrong chain ID. Expected {CHAIN_ID}, got {actual_chain_id}"
        )

    return {
        "connected": True,
        "chain_id": actual_chain_id,
        "latest_block": w3.eth.block_number,
    }


MARKETPLACE_ADDRESS = os.getenv(
    "MARKETPLACE_ADDRESS"
)

if not MARKETPLACE_ADDRESS:
    raise RuntimeError(
        "MARKETPLACE_ADDRESS is not configured"
    )


marketplace = w3.eth.contract(
    address=Web3.to_checksum_address(
        MARKETPLACE_ADDRESS
    ),
    abi=MARKETPLACE_ABI,
)


def entitlement_markets(token_id=None):
    # Legacy markets retain purchases after a new marketplace becomes active.
    markets = [marketplace]
    seen = {marketplace.address.lower()}
    for value in os.getenv("LEGACY_MARKETPLACE_ADDRESSES", "").split(","):
        value = value.strip()
        if not value:
            continue
        address = Web3.to_checksum_address(value)
        if address.lower() in seen:
            continue
        if int(address, 16) == 0:
            raise ValueError("Invalid legacy marketplace")
        abi = MARKETPLACE_ABI + [{"type": "function", "name": "knowledgeAsset",
            "stateMutability": "view", "inputs": [], "outputs": [{"name": "", "type": "address"}]}]
        legacy = w3.eth.contract(address=address, abi=abi)
        if w3.eth.chain_id != CHAIN_ID or legacy.functions.knowledgeAsset().call().lower() != legacy_registry_address().lower():
            raise ValueError("Legacy marketplace belongs to a different registry or chain")
        if token_id is not None and not market_token_supported(legacy.address, token_id):
            continue
        markets.append(legacy)
        seen.add(address.lower())
    return markets


def has_purchased(token_id: int, buyer_address: str) -> bool:
    buyer = Web3.to_checksum_address(buyer_address)
    return any(market.functions.hasPurchased(token_id, buyer).call() for market in entitlement_markets(token_id))


def get_purchase_count(token_id: int, buyer_address: str) -> int:
    buyer = Web3.to_checksum_address(buyer_address)
    return sum(market.functions.purchaseCount(token_id, buyer).call() for market in entitlement_markets(token_id))


KNOWLEDGE_ASSET_ADDRESS = os.getenv(
    "KNOWLEDGE_ASSET_ADDRESS"
)

if not KNOWLEDGE_ASSET_ADDRESS:
    raise RuntimeError(
        "KNOWLEDGE_ASSET_ADDRESS is not configured"
    )

knowledge_asset = w3.eth.contract(
    address=Web3.to_checksum_address(
        KNOWLEDGE_ASSET_ADDRESS
    ),
    abi=KNOWLEDGE_ASSET_ABI,
)


def get_knowledge_asset(token_id: int):
    asset = knowledge_asset.functions.getAsset(
        token_id
    ).call()

    owner = knowledge_asset.functions.ownerOf(
        token_id
    ).call()

    return {
        "ipfs_cid": asset[0],
        "metadata_cid": asset[1],
        "price_usdc": int(asset[2]),
        "creator": asset[3],
        "license": int(asset[4]),
        "quality_score": int(asset[5]),
        "active": asset[6],
        "minted_at": int(asset[7]),
        "owner": owner,
    }





def legacy_registry_address():
    previous = os.getenv("LEGACY_KNOWLEDGE_ASSET_ADDRESS")
    if not previous:
        return KNOWLEDGE_ASSET_ADDRESS
    transition = w3.eth.contract(address=knowledge_asset.address, abi=[
        {"type":"function","name":"legacyRegistry","stateMutability":"view","inputs":[],"outputs":[{"type":"address","name":""}]},
        {"type":"function","name":"legacyTokenLimit","stateMutability":"view","inputs":[],"outputs":[{"type":"uint256","name":""}]}])
    if transition.functions.legacyRegistry().call().lower() != previous.lower() or transition.functions.legacyTokenLimit().call() != int(os.environ["LEGACY_TOKEN_LIMIT"]):
        raise ValueError("Registry transition mismatch")
    return previous


def market_token_supported(address, token_id):
    return (address.lower() == MARKETPLACE_ADDRESS.lower()
            or not os.getenv("LEGACY_KNOWLEDGE_ASSET_ADDRESS")
            or 0 < int(token_id) <= int(os.environ["LEGACY_TOKEN_LIMIT"]))
