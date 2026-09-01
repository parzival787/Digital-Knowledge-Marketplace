import os

from web3 import Web3
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


def has_purchased(
    token_id: int,
    buyer_address: str
) -> bool:

    buyer = Web3.to_checksum_address(
        buyer_address
    )

    return marketplace.functions.hasPurchased(
        token_id,
        buyer
    ).call()


def get_purchase_count(
    token_id: int,
    buyer_address: str
) -> int:

    buyer = Web3.to_checksum_address(
        buyer_address
    )

    return marketplace.functions.purchaseCount(
        token_id,
        buyer
    ).call()


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



