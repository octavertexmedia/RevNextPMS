from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.clickjacking import xframe_options_exempt
from datetime import timedelta
from core.models import Property, RoomType, RatePlan, Inventory
from bookings.models import Reservation
from .models import DirectBooking
from .forms import AvailabilityForm, GuestDetailsForm


def _get_available_room_types(property_obj, check_in, check_out):
    """Return room types with availability for the full date range."""
    dates = []
    d = check_in
    while d < check_out:
        dates.append(d)
        d += timedelta(days=1)
    if not dates:
        return []
    # Room types that have available_rooms > 0 for ALL dates
    from django.db.models import Count
    inv = Inventory.objects.filter(
        property=property_obj,
        date__in=dates,
        available_rooms__gt=0
    ).values('room_type_id').annotate(
        cnt=Count('date')
    ).filter(cnt=len(dates))
    rt_ids = [x['room_type_id'] for x in inv]
    return RoomType.objects.filter(id__in=rt_ids, is_active=True).select_related('property')


def _get_rates_for_room(room_type, check_in, check_out, nights):
    """Get rate plans for room type with calculated total."""
    plans = RatePlan.objects.filter(room_type=room_type, is_active=True).select_related('meal_plan')
    result = []
    for rp in plans:
        # Simple: base_rate * nights
        total = rp.base_rate.amount * nights
        result.append({
            'plan': rp,
            'total': total,
            'currency': rp.base_rate.currency,
            'per_night': rp.base_rate.amount,
        })
    return result


@xframe_options_exempt
def booking_widget(request, property_id):
    """Public booking widget - embeddable on property websites"""
    property_obj = get_object_or_404(Property, id=property_id)
    context = {
        'property': property_obj,
        'page_title': 'Book Now',
    }
    return render(request, 'booking_engine/widget.html', context)


@login_required
def booking_dashboard(request):
    tenant = getattr(request, 'tenant', None)
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    bookings = DirectBooking.objects.filter(property__tenant=tenant).order_by('-created_at')[:30] if tenant else []
    total_direct = DirectBooking.objects.filter(property__tenant=tenant, status='CONFIRMED').count() if tenant else 0
    
    context = {
        'page_title': 'Booking Engine',
        'properties': properties,
        'bookings': bookings,
        'total_direct': total_direct,
    }
    return render(request, 'booking_engine/dashboard.html', context)


@login_required
def booking_settings(request):
    from .models import BookingEngineConfig

    tenant = getattr(request, 'tenant', None)
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    configs = []
    if tenant:
        for prop in properties:
            cfg, _ = BookingEngineConfig.objects.get_or_create(property=prop)
            configs.append(cfg)

        if request.method == 'POST':
            prop_id = request.POST.get('property_id')
            cfg = BookingEngineConfig.objects.filter(
                property_id=prop_id, property__tenant=tenant,
            ).first()
            if cfg:
                cfg.is_enabled = request.POST.get('is_enabled') == 'on'
                cfg.default_currency = request.POST.get('default_currency') or cfg.default_currency
                cfg.deposit_percent = request.POST.get('deposit_percent') or 0
                cfg.require_phone = request.POST.get('require_phone') == 'on'
                cfg.google_hotel_ads_enabled = request.POST.get('google_hotel_ads_enabled') == 'on'
                cfg.widget_primary_color = request.POST.get('widget_primary_color') or cfg.widget_primary_color
                cfg.save()
                messages.success(request, f'Saved booking settings for {cfg.property.name}.')
                return redirect('booking_engine:settings')

    context = {
        'page_title': 'Booking Engine Settings',
        'properties': properties,
        'configs': configs,
        'product_host': 'booking.revnext.in',
        'public_api_base': '/api/booking-engine/public/',
    }
    return render(request, 'booking_engine/settings.html', context)


# --- Task 13: Availability check ---
@login_required
def availability_check(request):
    """Step 1: Check availability by property and dates"""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('booking_engine:dashboard')
    if request.method == 'POST':
        form = AvailabilityForm(request.POST, tenant=tenant)
        if form.is_valid():
            cd = form.cleaned_data
            request.session['booking'] = {
                'property_id': cd['property'].id,
                'check_in': cd['check_in'].isoformat(),
                'check_out': cd['check_out'].isoformat(),
                'adults': cd['adults'],
                'children': cd['children'],
                'display_currency': cd.get('display_currency', cd['property'].currency or 'INR'),
            }
            return redirect('booking_engine:availability_results')
    else:
        form = AvailabilityForm(tenant=tenant)
    return render(request, 'booking_engine/availability_form.html', {
        'form': form, 'page_title': 'Check Availability'
    })


@login_required
def availability_results(request):
    """Step 2: Show available room types and rates"""
    tenant = getattr(request, 'tenant', None)
    data = request.session.get('booking')
    if not data:
        messages.warning(request, 'Please check availability first.')
        return redirect('booking_engine:availability_check')
    from datetime import datetime
    check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
    check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
    nights = (check_out - check_in).days
    property_obj = get_object_or_404(Property, id=data['property_id'], tenant=tenant)
    room_types = _get_available_room_types(property_obj, check_in, check_out)
    results = []
    for rt in room_types:
        rates = _get_rates_for_room(rt, check_in, check_out, nights)
        for r in rates:
            results.append({
                'room_type': rt,
                'rate_plan': r['plan'],
                'total': r['total'],
                'currency': r['currency'],
                'per_night': r['per_night'],
                'nights': nights,
            })
    display_currency = data.get('display_currency', property_obj.currency or 'INR')
    context = {
        'page_title': 'Available Rooms',
        'property': property_obj,
        'check_in': check_in,
        'check_out': check_out,
        'nights': nights,
        'results': results,
        'adults': data.get('adults', 1),
        'children': data.get('children', 0),
        'display_currency': display_currency,
    }
    return render(request, 'booking_engine/availability_results.html', context)


@login_required
def booking_select_rate(request):
    """Step 3: Select rate - store in session and go to guest form"""
    tenant = getattr(request, 'tenant', None)
    data = request.session.get('booking')
    if not data:
        messages.warning(request, 'Session expired. Please start again.')
        return redirect('booking_engine:availability_check')
    room_type_id = request.POST.get('room_type_id')
    rate_plan_id = request.POST.get('rate_plan_id')
    if not room_type_id or not rate_plan_id:
        messages.error(request, 'Please select a room and rate.')
        return redirect('booking_engine:availability_results')
    room_type = get_object_or_404(RoomType, id=room_type_id, property__tenant=tenant)
    rate_plan = get_object_or_404(RatePlan, id=rate_plan_id, room_type=room_type)
    from datetime import datetime
    check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
    check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
    nights = (check_out - check_in).days
    total = rate_plan.base_rate.amount * nights
    data['room_type_id'] = int(room_type_id)
    data['rate_plan_id'] = int(rate_plan_id)
    data['total_amount'] = float(total)
    data['currency'] = rate_plan.base_rate.currency
    request.session['booking'] = data
    request.session.modified = True
    return redirect('booking_engine:guest_form')


@login_required
def guest_form(request):
    """Step 4: Guest details form"""
    tenant = getattr(request, 'tenant', None)
    data = request.session.get('booking')
    if not data or 'room_type_id' not in data:
        messages.warning(request, 'Please select a room first.')
        return redirect('booking_engine:availability_results')
    if request.method == 'POST':
        form = GuestDetailsForm(request.POST)
        if form.is_valid():
            data['guest_name'] = form.cleaned_data['guest_name']
            data['guest_email'] = form.cleaned_data['guest_email']
            data['guest_phone'] = form.cleaned_data.get('guest_phone', '')
            request.session['booking'] = data
            request.session.modified = True
            return redirect('booking_engine:booking_confirm')
    else:
        form = GuestDetailsForm()
    from datetime import datetime
    check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
    check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
    nights = (check_out - check_in).days
    property_obj = get_object_or_404(Property, id=data['property_id'], tenant=tenant)
    room_type = get_object_or_404(RoomType, id=data['room_type_id'], property=property_obj)
    rate_plan = get_object_or_404(RatePlan, id=data['rate_plan_id'], room_type=room_type)
    context = {
        'form': form,
        'page_title': 'Guest Details',
        'property': property_obj,
        'room_type': room_type,
        'rate_plan': rate_plan,
        'check_in': check_in,
        'check_out': check_out,
        'nights': nights,
        'total': data['total_amount'],
        'currency': data['currency'],
    }
    return render(request, 'booking_engine/guest_form.html', context)


@login_required
def booking_confirm(request):
    """Step 5: Confirmation page - show summary"""
    tenant = getattr(request, 'tenant', None)
    data = request.session.get('booking')
    if not data or 'guest_name' not in data:
        messages.warning(request, 'Please complete guest details.')
        return redirect('booking_engine:guest_form')
    property_obj = get_object_or_404(Property, id=data['property_id'], tenant=tenant)
    room_type = get_object_or_404(RoomType, id=data['room_type_id'], property=property_obj)
    rate_plan = get_object_or_404(RatePlan, id=data['rate_plan_id'], room_type=room_type)
    from datetime import datetime
    check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
    check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
    nights = (check_out - check_in).days
    context = {
        'page_title': 'Confirm Booking',
        'property': property_obj,
        'room_type': room_type,
        'rate_plan': rate_plan,
        'check_in': check_in,
        'check_out': check_out,
        'nights': nights,
        'total': data['total_amount'],
        'currency': data['currency'],
        'guest_name': data['guest_name'],
        'guest_email': data['guest_email'],
        'guest_phone': data.get('guest_phone', ''),
        'adults': data.get('adults', 1),
        'children': data.get('children', 0),
    }
    return render(request, 'booking_engine/booking_confirm.html', context)


@login_required
def booking_create(request):
    """Step 6: Create DirectBooking and optionally Reservation"""
    tenant = getattr(request, 'tenant', None)
    data = request.session.get('booking')
    if not data or 'guest_name' not in data:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('booking_engine:availability_check')
    from datetime import datetime
    from djmoney.money import Money
    import uuid
    check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
    check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
    nights = (check_out - check_in).days
    property_obj = get_object_or_404(Property, id=data['property_id'], tenant=tenant)
    room_type = get_object_or_404(RoomType, id=data['room_type_id'], property=property_obj)
    rate_plan = get_object_or_404(RatePlan, id=data['rate_plan_id'], room_type=room_type)
    total = Money(float(data['total_amount']), data['currency'])
    confirmation_code = f'BE-{uuid.uuid4().hex[:8].upper()}'
    booking = DirectBooking.objects.create(
        property=property_obj,
        room_type=room_type,
        rate_plan=rate_plan,
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        guest_name=data['guest_name'],
        guest_email=data['guest_email'],
        guest_phone=data.get('guest_phone', ''),
        adults=data.get('adults', 1),
        children=data.get('children', 0),
        total_amount=total,
        currency=data['currency'],
        status='CONFIRMED',
        confirmation_code=confirmation_code,
        source='booking_engine',
    )
    # Create Reservation for unified view
    reservation = Reservation.objects.create(
        provider_name='booking_engine',
        provider_reservation_id=confirmation_code,
        provider_confirmation_code=confirmation_code,
        property=property_obj,
        room_type=room_type,
        rate_plan=rate_plan,
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        guest_name=data['guest_name'],
        guest_email=data['guest_email'],
        guest_phone=data.get('guest_phone', ''),
        adults=data.get('adults', 1),
        children=data.get('children', 0),
        base_room_rate=total,
        total_amount=total,
        currency=data['currency'],
        status='CONFIRMED',
    )
    booking.reservation = reservation
    booking.save(update_fields=['reservation'])
    # Decrement inventory (simplified - one room for the stay)
    from django.db.models import F
    Inventory.objects.filter(
        property=property_obj,
        room_type=room_type,
        date__gte=check_in,
        date__lt=check_out,
        available_rooms__gt=0
    ).update(available_rooms=F('available_rooms') - 1)
    request.session.pop('booking', None)
    messages.success(request, f'Booking confirmed! Code: {confirmation_code}')
    return redirect('booking_engine:booking_detail', booking_id=booking.id)


@login_required
def booking_detail(request, booking_id):
    tenant = getattr(request, 'tenant', None)
    booking = get_object_or_404(DirectBooking, id=booking_id, property__tenant=tenant)
    context = {'page_title': f'Booking {booking.confirmation_code}', 'booking': booking}
    return render(request, 'booking_engine/booking_detail.html', context)
