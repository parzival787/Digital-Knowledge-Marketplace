import uuid
import asyncio
import os
import httpx

from services.pgvector_client import get_asset_by_token_id, get_conn

from .mock_provider import MockPaymentProvider
from .models import CreatePaymentRequest, PaymentMethod, PaymentOrder, PaymentStatus
from .razorpay_provider import RazorpayProvider


class PaymentService:
    def __init__(self):
        self.providers = {PaymentMethod.MOCK: MockPaymentProvider()}
        if os.getenv("RAZORPAY_KEY_ID", "").startswith("rzp_test_") and os.getenv("RAZORPAY_KEY_SECRET"):
            provider = RazorpayProvider()
            self.providers.update({PaymentMethod.UPI: provider, PaymentMethod.CARD: provider})

    async def create_order(self, request: CreatePaymentRequest, user_id: int | None = None) -> PaymentOrder:
        asset = await get_asset_by_token_id(request.token_id)
        if not asset:
            raise ValueError(f"Knowledge asset {request.token_id} not found")
        provider = self.providers.get(request.payment_method)
        if not provider:
            raise ValueError(f"Payment method '{request.payment_method.value}' is not available yet")
        amount = asset["price_usdc"]
        if not isinstance(amount, int) or amount <= 0:
            raise ValueError("Knowledge asset has no valid payment price")

        # Preserve the existing database amount convention; do not reinterpret
        # whole-USDC asset prices as six-decimal on-chain units here.
        order = PaymentOrder(
            order_id=str(uuid.uuid4()), token_id=request.token_id,
            buyer_address=request.buyer_address, amount_usdc=amount,
            payment_method=request.payment_method, status=PaymentStatus.CREATED,
        )
        if isinstance(provider, RazorpayProvider):
            from .settlement import validate_checkout
            context = await asyncio.to_thread(validate_checkout, order)
            order = order.model_copy(update={**context, **provider.quote(amount)})
        conn = await get_conn()
        try:
            # Save the identity before contacting a provider so failures leave
            # an audit record instead of silently losing the order.
            await conn.execute("""
                INSERT INTO payment_orders
                    (order_id, token_id, buyer_address, amount_usdc, payment_method, status,
                     fiat_currency, fiat_amount, exchange_rate, checkout_key, listing_id, marketplace_address, chain_id, user_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """, order.order_id, order.token_id, order.buyer_address,
                order.amount_usdc, order.payment_method.value, order.status.value,
                order.fiat_currency, order.fiat_amount, order.exchange_rate, order.checkout_key,
                order.listing_id, order.marketplace_address, order.chain_id, user_id)
            try:
                result = await provider.create_payment(order)
                provider_id = result.get("provider_order_id")
                if not isinstance(provider_id, str) or not provider_id.strip():
                    raise ValueError("Missing provider order ID")
                order.provider_order_id = provider_id
                order.status = PaymentStatus.PENDING
            except Exception:
                order.status = PaymentStatus.FAILED
                order.error = "Provider order creation failed"
            await self._save(conn, order)
            return order
        finally:
            await conn.close()

    async def get_order(self, order_id: str) -> PaymentOrder | None:
        conn = await get_conn()
        try:
            row = await conn.fetchrow("SELECT * FROM payment_orders WHERE order_id=$1", order_id)
            return PaymentOrder.model_validate(dict(row)) if row else None
        finally:
            await conn.close()

    async def confirm_order(self, order_id: str, confirmation: dict | None = None) -> PaymentOrder:
        conn = await get_conn()
        try:
            async with conn.transaction():
                # Per-order database locking works across processes and restarts.
                row = await conn.fetchrow(
                    "SELECT * FROM payment_orders WHERE order_id=$1 FOR UPDATE", order_id
                )
                if not row:
                    raise ValueError("Payment order not found")
                order = PaymentOrder.model_validate(dict(row))
                if order.status in (
                    PaymentStatus.PROVIDER_CONFIRMED, PaymentStatus.SETTLEMENT_PENDING,
                    PaymentStatus.SETTLED, PaymentStatus.ENTITLEMENT_GRANTED,
                ):
                    return order
                if order.status != PaymentStatus.PENDING:
                    raise ValueError(f"Cannot confirm payment in state {order.status.value}")
                provider = self.providers.get(order.payment_method)
                if not provider:
                    raise ValueError("Payment provider is unavailable")
                try:
                    result = await provider.verify_payment(order, confirmation)
                    payment_id = result.get("provider_payment_id")
                    if result.get("pending"):
                        return order
                    if result.get("success") and isinstance(payment_id, str) and payment_id.strip():
                        order.provider_payment_id = payment_id
                        order.status = PaymentStatus.PROVIDER_CONFIRMED
                        order.error = None
                    else:
                        order.status = PaymentStatus.FAILED
                        order.error = "Provider verification failed"
                except ValueError:
                    # An invalid callback must not let a stranger poison a real order.
                    raise
                except httpx.HTTPError:
                    raise ValueError("Payment provider is temporarily unavailable; retry verification") from None
                except Exception:
                    raise ValueError("Payment verification is temporarily unavailable") from None
                await self._save(conn, order)
                return order
        finally:
            await conn.close()

    @staticmethod
    async def _save(conn, order: PaymentOrder):
        await conn.execute("""
            UPDATE payment_orders SET status=$2, provider_order_id=$3,
                provider_payment_id=$4, error=$5, updated_at=clock_timestamp()
            WHERE order_id=$1
        """, order.order_id, order.status.value, order.provider_order_id,
            order.provider_payment_id, order.error)


payment_service = PaymentService()
