"""
Utility functions for GST calculations and India-specific features
"""
from django.db.models import Q
from djmoney.money import Money
from typing import Dict, Tuple


def calculate_gst(base_amount: Money, property_state: str, guest_state: str = None) -> Dict[str, Money]:
    """
    Calculate GST components (CGST, SGST, IGST) based on place of supply rules
    
    Args:
        base_amount: Base amount before tax
        property_state: State where property is located
        guest_state: State where guest is located (optional, defaults to property_state)
    
    Returns:
        Dictionary with 'cgst', 'sgst', 'igst' amounts
    """
    currency = base_amount.currency
    
    # If guest state not provided, assume intra-state
    if not guest_state:
        guest_state = property_state
    
    # Determine if intra-state or inter-state
    is_intra_state = (property_state.upper() == guest_state.upper())
    
    # GST rate (typically 12% or 18% for hotel services)
    # This should be configurable per property/tax fee
    gst_rate = 0.12  # 12% - can be overridden
    
    if is_intra_state:
        # Intra-state: CGST + SGST (each 50% of total GST)
        total_gst = base_amount.amount * gst_rate
        cgst_amount = Money(total_gst / 2, currency)
        sgst_amount = Money(total_gst / 2, currency)
        igst_amount = Money(0, currency)
    else:
        # Inter-state: IGST (full GST)
        total_gst = base_amount.amount * gst_rate
        cgst_amount = Money(0, currency)
        sgst_amount = Money(0, currency)
        igst_amount = Money(total_gst, currency)
    
    return {
        'cgst': cgst_amount,
        'sgst': sgst_amount,
        'igst': igst_amount,
        'total_gst': Money(cgst_amount.amount + sgst_amount.amount + igst_amount.amount, currency)
    }


def generate_gst_invoice_data(reservation) -> Dict:
    """
    Generate GST-compliant invoice data for a reservation
    
    Args:
        reservation: Reservation instance
    
    Returns:
        Dictionary with invoice data
    """
    property_obj = reservation.property
    
    invoice_data = {
        'supplier': {
            'legal_name': property_obj.legal_name or property_obj.name,
            'address': {
                'line1': property_obj.address_line1,
                'line2': property_obj.address_line2,
                'city': property_obj.city,
                'state': property_obj.state,
                'postal_code': property_obj.postal_code,
                'country': property_obj.country,
            },
            'gstin': property_obj.gstin,
            'pan': property_obj.pan,
        },
        'recipient': {
            'name': reservation.guest_name,
            'address': {
                'line1': reservation.guest_address or '',
                'city': reservation.guest_city or '',
                'state': reservation.guest_state or '',
                'country': reservation.guest_country or '',
            },
            'gstin': reservation.guest_gstin or None,
        },
        'invoice_details': {
            'invoice_number': f"INV-{reservation.id}",
            'invoice_date': reservation.created_at.date(),
            'reservation_id': str(reservation.id),
            'provider_reservation_id': reservation.provider_reservation_id,
        },
        'service_details': {
            'description': f"Hotel accommodation - {reservation.check_in} to {reservation.check_out}",
            'hsn_sac_code': '9963',  # Accommodation services SAC code
            'nights': reservation.nights,
        },
        'financial_breakdown': {
            'base_amount': float(reservation.base_room_rate.amount),
            'taxes_fees': float(reservation.total_taxes_fees.amount),
            'cgst_amount': float(reservation.cgst_amount.amount),
            'sgst_amount': float(reservation.sgst_amount.amount),
            'igst_amount': float(reservation.igst_amount.amount),
            'total_amount': float(reservation.total_amount.amount),
            'currency': str(reservation.currency),
        },
        'place_of_supply': {
            'state': property_obj.state,
            'is_intra_state': reservation.cgst_amount.amount > 0 or reservation.sgst_amount.amount > 0,
        },
    }
    
    return invoice_data

