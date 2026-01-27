"""
Pricing rules views for tenants
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db.models import Q

from core.models import Property, RatePlan, PricingRule, Inventory
from core.pricing_engine import PricingEngine
from djmoney.money import Money


@login_required
def tenant_pricing_rules(request):
    """List all pricing rules for the tenant"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    # Get all properties for the tenant
    properties = Property.objects.filter(tenant=tenant, is_active=True)
    
    # Get filter parameters
    property_id = request.GET.get('property')
    rule_type = request.GET.get('rule_type')
    is_active = request.GET.get('is_active')
    
    # Build query
    pricing_rules = PricingRule.objects.filter(property__tenant=tenant)
    
    if property_id:
        pricing_rules = pricing_rules.filter(property_id=property_id)
    
    if rule_type:
        pricing_rules = pricing_rules.filter(rule_type=rule_type)
    
    if is_active is not None:
        pricing_rules = pricing_rules.filter(is_active=(is_active == 'true'))
    
    pricing_rules = pricing_rules.order_by('-priority', 'name')
    
    context = {
        'tenant': tenant,
        'user': user,
        'pricing_rules': pricing_rules,
        'properties': properties,
        'selected_property': property_id,
        'selected_rule_type': rule_type,
        'selected_is_active': is_active,
    }
    
    return render(request, 'tenants/pricing_rules.html', context)


@login_required
def tenant_pricing_rule_add(request, rule_id=None):
    """Create or edit a pricing rule"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    # Get or create rule
    if rule_id:
        rule = get_object_or_404(PricingRule, id=rule_id, property__tenant=tenant)
        is_edit = True
    else:
        rule = None
        is_edit = False
    
    # Get tenant's properties and rate plans
    properties = Property.objects.filter(tenant=tenant, is_active=True).order_by('name')
    rate_plans = RatePlan.objects.filter(property__tenant=tenant, is_active=True).order_by('property__name', 'name')
    
    if request.method == 'POST':
        try:
            property_id = request.POST.get('property')
            rate_plan_id = request.POST.get('rate_plan') or None
            name = request.POST.get('name')
            rule_type = request.POST.get('rule_type')
            description = request.POST.get('description', '')
            adjustment_type = request.POST.get('adjustment_type')
            adjustment_value = request.POST.get('adjustment_value')
            priority = request.POST.get('priority', 0)
            is_active = request.POST.get('is_active') == 'on'
            is_automatic = request.POST.get('is_automatic') == 'on'
            
            # Get property
            property_obj = get_object_or_404(Property, id=property_id, tenant=tenant)
            
            # Get rate plan if specified
            rate_plan_obj = None
            if rate_plan_id:
                rate_plan_obj = get_object_or_404(RatePlan, id=rate_plan_id, property=property_obj)
            
            # Get optional fields
            start_date = request.POST.get('start_date') or None
            end_date = request.POST.get('end_date') or None
            occupancy_threshold = request.POST.get('occupancy_threshold') or None
            min_price = request.POST.get('min_price') or None
            max_price = request.POST.get('max_price') or None
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Create or update rule
            if is_edit:
                rule.property = property_obj
                rule.rate_plan = rate_plan_obj
                rule.name = name
                rule.rule_type = rule_type
                rule.description = description
                rule.adjustment_type = adjustment_type
                rule.adjustment_value = adjustment_value
                rule.priority = int(priority)
                rule.is_active = is_active
                rule.is_automatic = is_automatic
                rule.start_date = start_date
                rule.end_date = end_date
                if occupancy_threshold:
                    rule.occupancy_threshold = float(occupancy_threshold)
                if min_price:
                    rule.min_price = Money(float(min_price), 'INR')
                if max_price:
                    rule.max_price = Money(float(max_price), 'INR')
                rule.save()
                messages.success(request, 'Pricing rule updated successfully!')
            else:
                rule = PricingRule.objects.create(
                    property=property_obj,
                    rate_plan=rate_plan_obj,
                    name=name,
                    rule_type=rule_type,
                    description=description,
                    adjustment_type=adjustment_type,
                    adjustment_value=adjustment_value,
                    priority=int(priority),
                    is_active=is_active,
                    is_automatic=is_automatic,
                    start_date=start_date,
                    end_date=end_date,
                    occupancy_threshold=float(occupancy_threshold) if occupancy_threshold else None,
                    min_price=Money(float(min_price), 'INR') if min_price else None,
                    max_price=Money(float(max_price), 'INR') if max_price else None,
                )
                messages.success(request, 'Pricing rule created successfully!')
            
            return redirect('tenants:pricing_rules')
            
        except Exception as e:
            messages.error(request, f'Error saving pricing rule: {str(e)}')
    
    context = {
        'tenant': tenant,
        'user': user,
        'rule': rule,
        'properties': properties,
        'rate_plans': rate_plans,
        'is_edit': is_edit,
    }
    
    return render(request, 'tenants/pricing_rule_add.html', context)


@login_required
def tenant_rate_optimization(request):
    """View rate optimization dashboard"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    # Get filter parameters
    property_id = request.GET.get('property')
    room_type_id = request.GET.get('room_type')
    date_str = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()
    
    # Get properties and room types
    properties = Property.objects.filter(tenant=tenant, is_active=True).order_by('name')
    
    # Build query for rate plans
    rate_plans = RatePlan.objects.filter(property__tenant=tenant, is_active=True)
    
    if property_id:
        rate_plans = rate_plans.filter(property_id=property_id)
    
    if room_type_id:
        rate_plans = rate_plans.filter(room_type_id=room_type_id)
    
    rate_plans = rate_plans.select_related('property', 'room_type').order_by('property__name', 'room_type__name')
    
    # Calculate optimized rates for each rate plan
    optimization_data = []
    for rate_plan in rate_plans:
        try:
            engine = PricingEngine(rate_plan.property)
            
            # Get current occupancy
            try:
                inventory = Inventory.objects.get(
                    property=rate_plan.property,
                    room_type=rate_plan.room_type,
                    date=selected_date
                )
                if inventory.total_rooms > 0:
                    occupied = inventory.total_rooms - inventory.available_rooms - inventory.blocked_rooms
                    occupancy = (occupied / inventory.total_rooms) * 100
                else:
                    occupancy = 0
            except Inventory.DoesNotExist:
                occupancy = 0
            
            # Calculate optimized rate
            optimized_rate = engine.optimize_rates_for_demand(
                selected_date,
                rate_plan.room_type,
                target_occupancy=80.0
            )
            
            # Calculate rate with all rules applied
            check_out_date = selected_date + timedelta(days=1)
            final_rate = engine.calculate_rate(
                rate_plan,
                selected_date,
                check_out_date,
                occupancy=occupancy
            )
            
            optimization_data.append({
                'rate_plan': rate_plan,
                'base_rate': rate_plan.base_rate,
                'final_rate': final_rate,
                'optimized_rate': optimized_rate,
                'occupancy': round(occupancy, 2),
                'has_optimization': optimized_rate is not None and optimized_rate != rate_plan.base_rate,
            })
        except Exception as e:
            # Skip if error calculating
            continue
    
    context = {
        'tenant': tenant,
        'user': user,
        'properties': properties,
        'optimization_data': optimization_data,
        'selected_date': selected_date,
        'selected_property': property_id,
        'selected_room_type': room_type_id,
    }
    
    return render(request, 'tenants/rate_optimization.html', context)
