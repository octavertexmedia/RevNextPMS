"""
Platform SaaS billing gateways (RevNext subscription payments).

Guest/hotel checkout stays in payment_gateways (property credentials).
This package uses RevNext platform keys from environment / Constance.
"""
from .registry import (
    GATEWAY_RAZORPAY,
    GATEWAY_PAYU,
    get_active_gateway,
    get_available_gateways,
    get_gateway,
    get_preferred_gateway_code,
    set_preferred_gateway,
)

__all__ = [
    'GATEWAY_RAZORPAY',
    'GATEWAY_PAYU',
    'get_active_gateway',
    'get_available_gateways',
    'get_gateway',
    'get_preferred_gateway_code',
    'set_preferred_gateway',
]
