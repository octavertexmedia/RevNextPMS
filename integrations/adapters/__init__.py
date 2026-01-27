"""
Platform Adapters
"""
from .booking_com_adapter import BookingComAdapter
from .expedia_adapter import ExpediaAdapter
from .agoda_adapter import AgodaAdapter

__all__ = [
    'BookingComAdapter',
    'ExpediaAdapter',
    'AgodaAdapter',
]

