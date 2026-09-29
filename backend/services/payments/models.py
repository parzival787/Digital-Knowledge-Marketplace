from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from web3 import Web3


class PaymentStatus(str, Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    PROVIDER_CONFIRMED = "PROVIDER_CONFIRMED"
    SETTLEMENT_PENDING = "SETTLEMENT_PENDING"
    SETTLED = "SETTLED"
    ENTITLEMENT_GRANTED = "ENTITLEMENT_GRANTED"
    FAILED = "FAILED"


class PaymentMethod(str, Enum):
    MOCK = "mock"
    UPI = "upi"
    CARD = "card"
    WEB3 = "web3"


class CreatePaymentRequest(BaseModel):
    token_id: int = Field(gt=0)
    buyer_address: str = Field(min_length=1)
    payment_method: PaymentMethod = PaymentMethod.MOCK

    @field_validator("buyer_address")
    @classmethod
    def validate_buyer(cls, value: str) -> str:
        if not Web3.is_address(value) or int(value, 16) == 0:
            raise ValueError("A valid non-zero wallet address is required")
        return Web3.to_checksum_address(value)


class PaymentOrder(BaseModel):
    order_id: str

    token_id: int
    buyer_address: str

    amount_usdc: int

    payment_method: PaymentMethod
    status: PaymentStatus

    provider_order_id: Optional[str] = None
    provider_payment_id: Optional[str] = None

    settlement_tx_hash: Optional[str] = None

    error: Optional[str] = None

    fiat_currency: Optional[str] = None
    fiat_amount: Optional[int] = None
    exchange_rate: Optional[str] = None
    checkout_key: Optional[str] = None
    listing_id: Optional[int] = None
    marketplace_address: Optional[str] = None
    chain_id: Optional[int] = None


class ConfirmPaymentRequest(BaseModel):
    razorpay_payment_id: str = Field(pattern=r"^pay_[A-Za-z0-9]+$", max_length=100)
    razorpay_order_id: str = Field(pattern=r"^order_[A-Za-z0-9]+$", max_length=100)
    razorpay_signature: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
