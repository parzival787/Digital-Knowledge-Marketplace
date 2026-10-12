"""Public, secret-free route availability. Availability is not a purchase quote."""
import os

from web3 import Web3

from . import transak
from .razorpay_provider import RazorpayProvider
from .settlement import SETTLEMENT_ABI, function_abi
from .market_profiles import market_profile
from web3.middleware import ExtraDataToPOAMiddleware


def chain_routes():
    """Read deployed wiring; never infer deployed features from local artifacts."""
    w3 = Web3(Web3.HTTPProvider(os.environ["BLOCKCHAIN_RPC_URL"], request_kwargs={"timeout": 5}, exception_retry_configuration=None))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if w3.eth.chain_id != 80002:
        raise ValueError("Demo requires Amoy")
    abi = SETTLEMENT_ABI + [function_abi("paused", [], ["bool"])]
    addresses = [os.environ["MARKETPLACE_ADDRESS"]] + os.getenv("LEGACY_MARKETPLACE_ADDRESSES", "").split(",")
    markets = []
    block = w3.eth.block_number
    for value in dict.fromkeys(a.strip().lower() for a in addresses if a.strip()):
        markets.append(market_profile(w3, value, os.environ["KNOWLEDGE_ASSET_ADDRESS"],
                                      os.environ["MARKETPLACE_ADDRESS"], block))
    funded = False
    if os.getenv("SETTLEMENT_ENABLED") == "true" and os.getenv("SETTLEMENT_PRIVATE_KEY"):
        # Only probe the feature. Per-listing validation still checks funds/allowance.
        try:
            current = w3.eth.contract(address=markets[0]["address"], abi=abi)
            current.functions.settledPayments("0x" + "00" * 20, bytes(32)).call()
            funded = True
        except Exception:
            pass
    return markets, funded


def payment_capabilities():
    try:
        transak.configuration()
        transak_ready = True
    except (ValueError, TypeError):
        transak_ready = False
    try:
        markets, funded = chain_routes()
        chain_ready = bool(markets)
    except Exception:
        markets, funded, chain_ready = [], False, False
    try:
        RazorpayProvider().quote(1)
        razorpay_ready = funded and chain_ready and not markets[0]["paused"]
    except (ValueError, TypeError):
        razorpay_ready = False

    def route(enabled, state, message, purpose, **extra):
        return {"enabled": enabled, "state": state, "message": message,
                "purpose": purpose, "sandbox_only": True, **extra}

    purchase_ready = chain_ready and not markets[0]["paused"]
    routes = {
        "fixed_price": route(purchase_ready, "available" if purchase_ready else "unavailable",
            "Verified wallet, matching deployment, balance, allowance and fresh listing checks are required." if purchase_ready else
            "Marketplace is paused or its deployment could not be verified. Retry before paying.", "purchase", chain_id=80002),
        "auction": route(chain_ready, "available" if chain_ready else "unavailable",
            "Use verified marketplace auctions. Paused markets may still allow refunds/finalization; new bids are checked separately.", "auction", chain_id=80002),
        "transak_buy": route(transak_ready, "sandbox" if transak_ready else "configuration_required",
            "USDC on Polygon staging delivers TRNSK on Amoy. Start from a TRNSK listing for a bound funding quote; legacy MockUSDC listings require their original token. Funding never purchases an asset.", "funding",
            selected_token="USDC", delivered_token="TRNSK", provider_network="polygon", grants_access=False),
        "transak_sell": route(transak_ready, "sandbox" if transak_ready else "configuration_required",
            "Hosted sandbox entry only. SELL enablement and actual payout eligibility are determined by the provider.", "payout",
            payout_verified=False, grants_access=False),
        "razorpay": route(razorpay_ready, "sandbox" if razorpay_ready else "configuration_required",
            "Test checkout; listing and settlement funding are checked before creating an order." if razorpay_ready else
            "Test checkout requires provider credentials, a test rate and a deployed funded-settlement interface.", "purchase"),
        "upi": route(False, "unverified", "Actual UPI funding and payout are not verified for this demo. Razorpay test simulations are separate.", "funding"),
        "crypto_route": route(False, "unsupported", "No executable swap/bridge route supports this Amoy test-token deployment.", "funding"),
        "receipt_registry": route(False, "configuration_required", "Durable audit recorder is implemented; registry deployment and recorder activation require review. Never an access authority.", "audit"),
    }
    return {"version": 1, "environment": "local_demo", "chain_id": 80002,
            "markets": markets, "routes": routes,
            "fiat_configured": razorpay_ready, "fiat_message": routes["razorpay"]["message"],
            "bridge_available": False, "bridge_message": routes["crypto_route"]["message"]}
