"""Booking engine template tags"""
from django import template

# Simple approximate conversion rates (base: INR). Format: to_currency: rate_from_INR
RATES_FROM_INR = {'INR': 1, 'USD': 0.012, 'EUR': 0.011, 'GBP': 0.0095}

register = template.Library()


@register.filter
def convert_currency(amount, to_currency):
    """Convert amount (assumed INR) to display currency."""
    if amount is None or not to_currency:
        return amount
    rate = RATES_FROM_INR.get(str(to_currency).upper(), 1)
    return round(float(amount) * rate, 2)


@register.simple_tag
def convert_currency_tag(amount, from_currency, to_currency):
    """Convert amount from one currency to another."""
    if amount is None or not from_currency or not to_currency:
        return amount
    rate_from = RATES_FROM_INR.get(str(from_currency).upper(), 1)
    rate_to = RATES_FROM_INR.get(str(to_currency).upper(), 1)
    inr = float(amount) / rate_from
    return round(inr * rate_to, 2)


@register.filter
def currency_symbol(code):
    """Return symbol for currency code"""
    return {'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£'}.get(str(code).upper(), code)
