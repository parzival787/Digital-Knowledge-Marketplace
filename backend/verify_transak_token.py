"""Read-only Amoy staging token verification; never signs or broadcasts."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

TOKEN = "0x0c86A754A29714C4Fe9C6F1359fa7099eD174c0b"
PROBE = "0x0000000000000000000000000000000000000001"


def abi(name, inputs, outputs, state="view"):
    return {"type": "function", "name": name, "stateMutability": state,
            "inputs": [{"name": "", "type": t} for t in inputs],
            "outputs": [{"name": "", "type": t} for t in outputs]}


def verify(w3):
    if w3.eth.chain_id != 80002:
        raise ValueError("Wrong network")
    block = w3.eth.block_number - 2
    header = w3.eth.get_block(block)
    code = w3.eth.get_code(Web3.to_checksum_address(TOKEN), block_identifier=block)
    if not code:
        raise ValueError("Token code missing")
    token = w3.eth.contract(address=Web3.to_checksum_address(TOKEN), abi=[
        abi("symbol", [], ["string"]), abi("decimals", [], ["uint8"]),
        abi("balanceOf", ["address"], ["uint256"]),
        abi("allowance", ["address", "address"], ["uint256"]),
        abi("approve", ["address", "uint256"], ["bool"], "nonpayable"),
        abi("transfer", ["address", "uint256"], ["bool"], "nonpayable")])
    def read(fn):
        return fn.call({"from": PROBE}, block_identifier=block)
    symbol, decimals = read(token.functions.symbol()), read(token.functions.decimals())
    if symbol != "TRNSK" or decimals != 18:
        raise ValueError("Unexpected token metadata")
    balance = read(token.functions.balanceOf(PROBE))
    allowance = read(token.functions.allowance(PROBE, TOKEN))
    if read(token.functions.approve(TOKEN, 0)) is not True:
        raise ValueError("Approve simulation failed")
    if read(token.functions.transfer(TOKEN, 0)) is not True:
        raise ValueError("Transfer simulation failed")
    if w3.eth.get_block(block)["hash"] != header["hash"]:
        raise ValueError("Canonical block changed")
    return {"verified": True, "chain_id": 80002, "token": TOKEN,
            "symbol": symbol, "decimals": decimals, "block": block,
            "block_hash": Web3.to_hex(header["hash"]), "code_hash": Web3.to_hex(Web3.keccak(code)),
            "probe_balance": str(balance), "probe_allowance": str(allowance),
            "approve_zero_eth_call": True, "transfer_zero_eth_call": True,
            "broadcast": False, "checked_at": datetime.now(timezone.utc).isoformat(),
            "limitation": "Zero-value eth_call checks ABI behavior, not funded delivery or settlement."}


if __name__ == "__main__":
    load_dotenv(Path(__file__).with_name(".env"))
    try:
        rpc = os.environ["BLOCKCHAIN_RPC_URL"]
        client = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 25}))
        client.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        result = verify(client)
    except Exception as exc:
        # RPC exceptions can contain authenticated endpoints; expose only the class.
        print(json.dumps({"verified": False, "error_type": type(exc).__name__, "broadcast": False}))
        raise SystemExit(1) from None
    Path(__file__).resolve().parents[1].joinpath("transak_token_evidence.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
