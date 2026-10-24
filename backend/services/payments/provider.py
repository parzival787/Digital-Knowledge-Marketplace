from abc import ABC, abstractmethod

from .models import PaymentOrder


class PaymentProvider(ABC):

    @abstractmethod
    async def create_payment(
        self,
        order: PaymentOrder,
    ) -> dict:
        """
        Create a payment with the external provider.
        """
        raise NotImplementedError

    @abstractmethod
    async def verify_payment(
        self,
        order: PaymentOrder,
        confirmation: dict | None = None,
    ) -> dict:
        """
        Verify whether the provider received the payment.
        """
        raise NotImplementedError
