"""Razorpay test checkout. Never accepts live keys or treats provider success as access."""
import hashlib
import hmac
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import httpx

from .models import PaymentOrder
from .provider import PaymentProvider


class RazorpayProvider(PaymentProvider):
    def __init__(self):
        self.key = os.getenv("RAZORPAY_KEY_ID", "")
        self.secret = os.getenv("RAZORPAY_KEY_SECRET", "")

    def quote(self, amount_usdc: int) -> dict:
        if not self.key.startswith("rzp_test_") or not self.secret:
            raise ValueError("Razorpay test credentials are not configured")
        try:
            rate = Decimal(os.getenv("RAZORPAY_TEST_INR_PER_USDC", ""))
        except InvalidOperation:
            raise ValueError("Configure the test INR/USDC exchange rate") from None
        if not rate.is_finite() or rate <= 0:
            raise ValueError("Invalid test INR/USDC exchange rate")
        paise = int((Decimal(amount_usdc) * rate * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if not 100 <= paise <= 100_000_000:
            raise ValueError("Test payment amount is outside supported bounds")
        return dict(fiat_currency="INR", fiat_amount=paise, exchange_rate=str(rate), checkout_key=self.key)

    async def create_payment(self, order: PaymentOrder) -> dict:
        async with httpx.AsyncClient(timeout=20, auth=(self.key, self.secret)) as client:
            response = await client.post("https://api.razorpay.com/v1/orders", json={
                "amount": order.fiat_amount, "currency": order.fiat_currency, "receipt": order.order_id,
            })
            response.raise_for_status()
            result = response.json()
        if result.get("amount") != order.fiat_amount or result.get("currency") != order.fiat_currency:
            raise ValueError("Provider returned a different payment quote")
        return {"provider_order_id": result["id"]}

    async def verify_payment(self, order: PaymentOrder, confirmation: dict | None = None) -> dict:
        if not confirmation or confirmation.get("razorpay_order_id") != order.provider_order_id:
            raise ValueError("Payment confirmation does not match this order")
        payment_id = confirmation.get("razorpay_payment_id", "")
        signature = confirmation.get("razorpay_signature", "")
        expected = hmac.new(self.secret.encode(), f"{order.provider_order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise ValueError("Invalid payment signature")
        async with httpx.AsyncClient(timeout=20, auth=(self.key, self.secret)) as client:
            response = await client.get(f"https://api.razorpay.com/v1/payments/{payment_id}")
            response.raise_for_status()
            payment = response.json()
        if (payment.get("order_id") != order.provider_order_id
                or payment.get("amount") != order.fiat_amount
                or payment.get("currency") != order.fiat_currency):
            raise ValueError("Provider payment does not match the stored order")
        return {"success": payment.get("status") == "captured",
                "pending": payment.get("status") in ("created", "authorized"),
                "provider_payment_id": payment_id}
