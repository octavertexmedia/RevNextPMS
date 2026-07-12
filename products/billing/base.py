"""Shared billing gateway interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional


@dataclass
class CheckoutSession:
    gateway: str
    invoice_id: int
    amount: Decimal
    currency: str = 'INR'
    # Razorpay: order_id + key_id for Checkout.js
    # PayU: form action URL + posted fields
    payload: dict = field(default_factory=dict)
    gateway_order_id: str = ''


@dataclass
class PaymentResult:
    success: bool
    gateway: str
    transaction_id: str = ''
    gateway_order_id: str = ''
    payment_method: str = ''
    raw: dict = field(default_factory=dict)
    error: str = ''


class BillingGateway(ABC):
    code: str = ''
    display_name: str = ''

    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    def create_checkout(self, invoice, *, customer: Optional[dict] = None, callback_url: str = '') -> CheckoutSession:
        ...

    @abstractmethod
    def verify_payment(self, data: dict) -> PaymentResult:
        ...

    def public_config(self) -> dict[str, Any]:
        """Non-secret fields safe to send to the browser."""
        return {
            'code': self.code,
            'display_name': self.display_name,
            'configured': self.is_configured(),
        }
