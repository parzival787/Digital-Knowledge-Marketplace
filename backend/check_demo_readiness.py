"""Read-only Amoy preflight. Never prints credentials or sends transactions."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

load_dotenv(Path(__file__).with_name(".env"))
from services.payments.settlement import SETTLEMENT_ABI, TOKEN_ABI


def main():
    checks = {}
    for name in ("RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET", "SETTLEMENT_PRIVATE_KEY", "CONTENT_MASTER_KEY", "TRANSAK_STAGING_API_KEY", "TRANSAK_STAGING_API_SECRET"):
        value = os.getenv(name)
        if name.startswith("TRANSAK_STAGING_"):
            value = value or os.getenv(name.replace("TRANSAK_STAGING_", "transak_").lower())
        checks[name] = "present" if value else "missing"
    checks["razorpay_test_mode"] = os.getenv("RAZORPAY_KEY_ID", "").startswith("rzp_test_")
    from services.payments.razorpay_provider import RazorpayProvider
    try:
        RazorpayProvider().quote(1)
        checks["test_quote"] = "configured"
    except Exception:
        checks["test_quote"] = "unavailable"
    try:
        from services.content_security import master_key
        master_key()
        checks["content_key_valid"] = True
    except Exception:
        checks["content_key_valid"] = False
    try:
        w3 = Web3(Web3.HTTPProvider(os.environ["BLOCKCHAIN_RPC_URL"], request_kwargs={"timeout": 10}))
        if w3.eth.chain_id != 80002:
            raise ValueError("Wrong chain")
        checks["amoy_rpc"] = "connected"
        market = w3.eth.contract(address=Web3.to_checksum_address(os.environ["MARKETPLACE_ADDRESS"]), abi=SETTLEMENT_ABI)
        checks["marketplace_code"] = bool(w3.eth.get_code(market.address))
        checks["registry_matches"] = market.functions.knowledgeAsset().call().lower() == os.environ["KNOWLEDGE_ASSET_ADDRESS"].lower()
        try:
            market.functions.settledPayments("0x0000000000000000000000000000000000000001", bytes(32)).call()
            checks["funded_settlement_interface"] = "available (E2E still required)"
        except Exception:
            checks["funded_settlement_interface"] = "unavailable"
        if os.getenv("SETTLEMENT_PRIVATE_KEY"):
            signer = w3.eth.account.from_key(os.environ["SETTLEMENT_PRIVATE_KEY"])
            token = w3.eth.contract(address=market.functions.usdc().call(), abi=TOKEN_ABI)
            checks["signer_has_pol"] = w3.eth.get_balance(signer.address) > 0
            checks["signer_mockusdc_units"] = token.functions.balanceOf(signer.address).call()
            checks["signer_allowance_units"] = token.functions.allowance(signer.address, market.address).call()
    except Exception:
        checks["rpc_or_configuration_check"] = "failed; inspect configuration locally (details redacted)"
    checks["live_e2e"] = "not certified by this read-only preflight"
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
