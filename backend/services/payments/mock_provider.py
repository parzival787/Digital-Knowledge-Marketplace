import uuid

from .models import PaymentOrder
from .provider import PaymentProvider


class MockPaymentProvider(PaymentProvider):

    async def create_payment(
        self,
        order: PaymentOrder,
    ) -> dict:

        return {
            "provider_order_id": f"mock_order_{uuid.uuid4().hex}",
            "status": "pending",
        }

    async def verify_payment(
        self,
        order: PaymentOrder,
        confirmation: dict | None = None,
    ) -> dict:

        return {
            "success": True,
            "provider_payment_id": f"mock_payment_{uuid.uuid4().hex}",
        }
