"""
Gateway registry — pick Razorpay or PayU as the active SaaS billing provider.

Priority:
  1. Constance BILLING_GATEWAY (runtime switch in admin)
  2. settings.BILLING_GATEWAY / env
  3. First configured gateway (razorpay preferred if both set)
"""
from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings

from .payu_gateway import PayUGateway
from .razorpay_gateway import RazorpayGateway

logger = logging.getLogger(__name__)

GATEWAY_RAZORPAY = 'razorpay'
GATEWAY_PAYU = 'payu'
SUPPORTED = (GATEWAY_RAZORPAY, GATEWAY_PAYU)


def _constance_preferred() -> Optional[str]:
    """Return Constance value only if an admin has persisted it in the DB."""
    try:
        from constance import config
        from constance.models import Constance
        if not Constance.objects.filter(key='BILLING_GATEWAY').exists():
            return None
        value = (getattr(config, 'BILLING_GATEWAY', '') or '').strip().lower()
        if value in SUPPORTED:
            return value
    except Exception:
        pass
    return None


def get_preferred_gateway_code() -> str:
    # Runtime admin override (Constance) wins when explicitly set
    preferred = _constance_preferred()
    if preferred:
        return preferred
    preferred = (getattr(settings, 'BILLING_GATEWAY', '') or '').strip().lower()
    if preferred in SUPPORTED:
        return preferred
    return GATEWAY_RAZORPAY


def set_preferred_gateway(code: str) -> str:
    code = (code or '').strip().lower()
    if code not in SUPPORTED:
        raise ValueError(f'Unsupported gateway: {code}. Use razorpay or payu.')
    try:
        from constance import config
        config.BILLING_GATEWAY = code
    except Exception as exc:
        logger.warning('Could not persist BILLING_GATEWAY via Constance: %s', exc)
        # Fall through — caller should also set env for permanence
    return code


def get_gateway(code: Optional[str] = None):
    code = (code or get_preferred_gateway_code()).lower()
    if code == GATEWAY_PAYU:
        return PayUGateway()
    if code == GATEWAY_RAZORPAY:
        return RazorpayGateway()
    raise ValueError(f'Unknown billing gateway: {code}')


def get_available_gateways() -> list[dict]:
    preferred = get_preferred_gateway_code()
    items = []
    for code in SUPPORTED:
        gw = get_gateway(code)
        info = gw.public_config()
        info['active'] = code == preferred and gw.is_configured()
        info['preferred'] = code == preferred
        items.append(info)
    return items


def get_active_gateway(override: Optional[str] = None):
    """
    Return the gateway that should process the next checkout.

    If override is provided and configured, use it (one-shot choice).
    Otherwise use preferred; if preferred isn't configured, fall back to the other.
    """
    if override:
        gw = get_gateway(override)
        if not gw.is_configured():
            raise RuntimeError(f'{gw.display_name} is selected but not configured.')
        return gw

    preferred = get_preferred_gateway_code()
    primary = get_gateway(preferred)
    if primary.is_configured():
        return primary

    # Fallback to the other option
    other_code = GATEWAY_PAYU if preferred == GATEWAY_RAZORPAY else GATEWAY_RAZORPAY
    secondary = get_gateway(other_code)
    if secondary.is_configured():
        logger.warning(
            'Preferred gateway %s not configured; falling back to %s',
            preferred, other_code,
        )
        return secondary

    raise RuntimeError(
        'No SaaS billing gateway configured. Set Razorpay or PayU credentials in the environment.'
    )
