"""Server-only runtime staging coverage and quotes; no inferred UPI support."""
import asyncio
import ipaddress
import re
import time
from decimal import Decimal, InvalidOperation

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from services.auth import wallet_user, throttle
from .transak import configuration, provider_json

router = APIRouter(prefix="/api/payments/transak", tags=["Sandbox funding"])
BASE = "https://api-gateway-stg.transak.com/api/v2/lookup"


def text(value, pattern=r"[^\x00-\x1f\x7f]{1,80}"):
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError("Invalid provider metadata")
    return value


def amount(value):
    try:
        result = Decimal(str(value))
        if not result.is_finite() or not 0 <= result <= 10**12 or result.as_tuple().exponent < -18:
            raise ValueError("Invalid provider amount")
        return format(result, "f")
    except (InvalidOperation, TypeError):
        raise ValueError("Invalid provider amount") from None


async def lookup(path, user_ip, params=None):
    key, _ = configuration()
    ipaddress.ip_address(user_ip)
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        return await provider_json(client, BASE + path, method="GET",
            headers={"x-api-key": key, "x-user-ip": user_ip},
            params=({} if path == "/currencies/crypto-currencies" else {"apiKey": key, **(params or {})}))


async def discover(user_ip):
    fiat, crypto = await asyncio.gather(lookup("/currencies/fiat-currencies", user_ip),
                                      crypto_coverage())
    currencies = []
    for currency in fiat["fiatCurrencies"]:
        if currency.get("isAllowed") is not True:
            continue
        options = []
        for option in currency.get("paymentOptions", []):
            buy = option.get("isBuyAllowed") is True
            sell = currency.get("isSellAllowed") is True and option.get("isSellAllowed") is True
            if buy or sell:
                options.append({"id": text(option["id"]), "name": text(option["name"]),
                    "buy": buy, "sell": sell, "minimum": amount(option["minAmount"]),
                    "maximum": amount(option["maxAmount"])})
        if options:
            currencies.append({"symbol": text(currency["symbol"], r"[A-Z]{3}"), "methods": options})
    routes = []
    for currency in crypto:
        if currency.get("isAllowed") is True:
            network = currency["network"]
            routes.append({"symbol": text(currency["symbol"]), "network": text(network["name"]),
                "buy": True, "sell": currency.get("isPayInAllowed") is True,
                "excluded_fiat": [{"currency": text(c["fiatCurrency"], r"[A-Z]{3}"), "method": text(c["paymentMethod"])}
                                  if isinstance(c, dict) else {"currency": text(c, r"[A-Z]{3}"), "method": None}
                                  for c in network.get("fiatCurrenciesNotSupported", [])]})
    return {"fiat": currencies, "crypto": routes, "checked_at": time.time(), "environment": "staging"}


async def crypto_coverage():
    key, _ = configuration()
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            response = await client.get("https://api-stg.transak.com/cryptocoverage/api/v1/public/crypto-currencies",
                                        headers={"x-api-key": key})
            response.raise_for_status()
            data = response.json()["response"]
            if not isinstance(data, list):
                raise ValueError()
            return data
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        raise ValueError("Transak staging crypto coverage unavailable") from None


async def quote(user_ip, direction, fiat, method, crypto_amount):
    coverage = await discover(user_ip)
    if direction not in ("BUY", "SELL"):
        raise ValueError("Invalid provider direction")
    allowed = direction.lower()
    if not any(c["symbol"] == "USDC" and c["network"] == "polygon" and c[allowed] and
               not any(e["currency"] == fiat and e["method"] in (None, method) for e in c["excluded_fiat"]) for c in coverage["crypto"]):
        raise ValueError("Provider does not offer this sandbox route")
    if not any(c["symbol"] == fiat and any(m["id"] == method and m[allowed] for m in c["methods"]) for c in coverage["fiat"]):
        raise ValueError("Provider does not offer this payment method")
    params = {"fiatCurrency": fiat, "cryptoCurrency": "USDC", "network": "polygon",
              "isBuyOrSell": direction, "paymentMethod": method, "cryptoAmount": amount(crypto_amount)}
    key, _ = configuration()
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            response = await client.get("https://api-stg.transak.com/api/v1/pricing/public/quotes",
                headers={"x-api-key": key}, params={"partnerApiKey": key, **params})
            response.raise_for_status()
            data = response.json(parse_float=Decimal)["response"]
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        raise ValueError("Provider staging quote unavailable") from None
    if any(data.get(key) != params[key] for key in ("fiatCurrency", "cryptoCurrency", "network", "isBuyOrSell", "paymentMethod")):
        raise ValueError("Provider quote route mismatch")
    result = {key: data[key] for key in ("fiatCurrency", "cryptoCurrency", "network", "isBuyOrSell", "paymentMethod")}
    result.update(quote_id=text(data["quoteId"], r"[A-Za-z0-9_-]{1,160}"), fetched_at=time.time(),
                  freshness_seconds=60, environment="staging")
    for key in ("fiatAmount", "cryptoAmount", "totalFee", "conversionPrice"):
        result[key] = amount(data[key])
    if any(Decimal(result[key]) <= 0 for key in ("fiatAmount", "cryptoAmount", "conversionPrice")):
        raise ValueError("Provider quote has no payable amount")
    if direction == "SELL" and Decimal(result["cryptoAmount"]) != Decimal(params["cryptoAmount"]):
        raise ValueError("Provider quoted a different sale amount")
    result["fees"] = [{"name": text(f["name"]), "amount": amount(f["value"])} for f in data.get("feeBreakdown", [])]
    return result


@router.get("/coverage")
async def coverage(request: Request, user=Depends(wallet_user)):
    await throttle(request, "transak-coverage:" + str(user["id"]))
    try:
        return await discover(request.client.host if request.client else "")
    except Exception:
        raise HTTPException(503, "Provider coverage could not be verified. No payment methods are enabled by assumption.") from None
