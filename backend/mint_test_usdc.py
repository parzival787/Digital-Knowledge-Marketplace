"""Mint the deployed Amoy test token; never supports mainnet or real USDC."""
import argparse
from decimal import Decimal
from pathlib import Path
import json
from dotenv import dotenv_values
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719"
ABI = [
    {"type": "function", "name": name, "stateMutability": mutability, "inputs": inputs, "outputs": outputs}
    for name, mutability, inputs, outputs in [
        ("decimals", "view", [], [{"type": "uint8"}]),
        ("symbol", "view", [], [{"type": "string"}]),
        ("balanceOf", "view", [{"name": "owner", "type": "address"}], [{"type": "uint256"}]),
        ("mint", "nonpayable", [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], []),
    ]
]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wallet")
    parser.add_argument("amount")
    parser.add_argument("--send", action="store_true", help="Actually sign and mint; otherwise only preview")
    args = parser.parse_args()
    recipient = Web3.to_checksum_address(args.wallet)
    amount = Decimal(args.amount)
    if not amount.is_finite() or not 0 < amount <= 100 or amount * 10**6 != (amount * 10**6).to_integral_value():
        raise ValueError("Use a positive amount up to 100 with at most six decimal places")
    config = {**dotenv_values(ROOT / "backend/.env"), **dotenv_values(ROOT / "contracts/.env")}
    w3 = Web3(Web3.HTTPProvider(config["ALCHEMY_AMOY_URL"], request_kwargs={"timeout": 30}))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if w3.eth.chain_id != 80002:
        raise ValueError("Only Polygon Amoy is allowed")
    token = w3.eth.contract(address=TOKEN, abi=ABI)
    if token.functions.decimals().call() != 6 or token.functions.symbol().call() != "USDC":
        raise ValueError("Unexpected test token")
    signer = w3.eth.account.from_key(config["PRIVATE_KEY"])
    before = token.functions.balanceOf(recipient).call()
    print(json.dumps({"wallet": recipient, "before": str(Decimal(before) / 10**6), "mint_amount": str(amount), "signer": signer.address}), flush=True)
    if not args.send:
        return
    tip = max(w3.eth.max_priority_fee, w3.to_wei(25, "gwei"))
    fee = w3.eth.get_block("latest")["baseFeePerGas"] * 2 + tip
    call = token.functions.mint(recipient, int(amount * 10**6))
    tx = call.build_transaction({"from": signer.address, "chainId": 80002,
        "nonce": w3.eth.get_transaction_count(signer.address, "pending"),
        "maxPriorityFeePerGas": tip, "maxFeePerGas": fee,
        "gas": (call.estimate_gas({"from": signer.address, "maxPriorityFeePerGas": tip, "maxFeePerGas": fee}) * 120 + 99) // 100})
    if w3.eth.get_balance(signer.address) < tx["gas"] * fee:
        raise ValueError("Signer needs Amoy test POL for gas")
    tx_hash = w3.eth.send_raw_transaction(signer.sign_transaction(tx).raw_transaction)
    print("Submitted: " + w3.to_hex(tx_hash), flush=True)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise ValueError("Mint reverted")
    after = token.functions.balanceOf(recipient).call(block_identifier=receipt.blockNumber)
    print(json.dumps({"status": "confirmed", "transaction": w3.to_hex(tx_hash), "block": receipt.blockNumber, "balance": str(Decimal(after) / 10**6)}))

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Provider exception strings can contain credential-bearing RPC URLs.
        print("Mint did not complete: " + type(error).__name__ + ". Check any submitted hash before retrying.")
        raise SystemExit(1)
