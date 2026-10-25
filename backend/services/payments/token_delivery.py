"""Verify ERC20 delivery independently of provider completion; never grant access."""
import re
from web3 import Web3

TRNSK = "0x0c86A754A29714C4Fe9C6F1359fa7099eD174c0b"
TRANSFER = Web3.keccak(text="Transfer(address,address,uint256)")


def verify_delivery(w3, transaction_hash, recipient, required_amount, sender=None):
    if not isinstance(transaction_hash, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", transaction_hash):
        raise ValueError("Provider has no verifiable transaction hash")
    if w3.eth.chain_id != 80002 or not Web3.is_address(recipient) or int(recipient, 16) == 0:
        raise ValueError("Wrong delivery network or recipient")
    if type(required_amount) is not int or not 0 < required_amount < 2**256:
        raise ValueError("Invalid delivery amount")
    receipt = w3.eth.get_transaction_receipt(transaction_hash)
    if receipt.status != 1 or Web3.to_hex(receipt.transactionHash).lower() != transaction_hash.lower():
        raise ValueError("Delivery transaction failed or mismatched")
    if w3.eth.block_number < receipt.blockNumber + 1:
        raise ValueError("Delivery confirmations pending")
    canonical = w3.eth.get_block(receipt.blockNumber)
    if canonical.hash != receipt.blockHash:
        raise ValueError("Delivery receipt is not canonical")
    total = 0
    for log in receipt.logs:
        topics = log["topics"]
        if log["address"].lower() != TRNSK.lower() or len(topics) != 3 or topics[0] != TRANSFER:
            continue
        if log.get("removed") or log["blockHash"] != receipt.blockHash or log["transactionHash"] != receipt.transactionHash:
            raise ValueError("Delivery event identity changed")
        if len(topics[1]) != 32 or len(topics[2]) != 32 or len(log["data"]) != 32:
            raise ValueError("Invalid Transfer encoding")
        if int.from_bytes(topics[2]) != int(recipient, 16):
            continue
        if sender is not None and int.from_bytes(topics[1]) != int(sender, 16):
            continue
        total += int.from_bytes(log["data"])
    if total < required_amount:
        raise ValueError("Insufficient matching TRNSK delivery")
    fresh = w3.eth.get_transaction_receipt(transaction_hash)
    if dict(fresh) != dict(receipt) or w3.eth.get_block(receipt.blockNumber).hash != receipt.blockHash:
        raise ValueError("Delivery changed during verification")
    return {"chain_delivery_state": "verified", "chain_id": 80002, "token": TRNSK,
            "recipient": recipient, "amount_base_units": str(total),
            "transaction_hash": transaction_hash, "block": receipt.blockNumber,
            "block_hash": Web3.to_hex(receipt.blockHash), "grants_access": False}
