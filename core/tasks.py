"""
Celery tasks for core app - pricing automation
"""
from celery import shared_task
from django.utils import timezone
from datetime import date, timedelta
import logging

from .models import Property, PricingRule, RatePlan
from .pricing_engine import PricingEngine

logger = logging.getLogger(__name__)


@shared_task
def apply_seasonal_pricing_adjustments():
    """Apply seasonal pricing adjustments to all active properties"""
    today = date.today()
    end_date = today + timedelta(days=365)
    
    properties = Property.objects.filter(is_active=True)
    total_applied = 0
    
    for property_obj in properties:
        try:
            engine = PricingEngine(property_obj)
            applied = engine.apply_seasonal_adjustments(today, end_date)
            total_applied += applied
        except Exception as e:
            logger.error(f"Error applying seasonal pricing for {property_obj.name}: {e}", exc_info=True)
    
    logger.info(f"Applied seasonal pricing adjustments to {total_applied} rate plans")
    return total_applied


@shared_task
def optimize_rates_for_demand():
    """Optimize rates based on current demand and occupancy"""
    today = date.today()
    end_date = today + timedelta(days=90)  # Optimize for next 90 days
    
    properties = Property.objects.filter(is_active=True)
    total_optimized = 0
    
    for property_obj in properties:
        try:
            engine = PricingEngine(property_obj)
            
            # Get all active rate plans
            rate_plans = RatePlan.objects.filter(
                property=property_obj,
                is_active=True
            )
            
            for rate_plan in rate_plans:
                current_date = today
                optimized_count = 0
                
                while current_date <= end_date:
                    optimized_rate = engine.optimize_rates_for_demand(
                        current_date,
                        rate_plan.room_type,
                        target_occupancy=80.0
                    )
                    
                    if optimized_rate:
                        # Here you would typically update the rate in the system
                        # For now, we just track that optimization was calculated
                        optimized_count += 1
                    
                    current_date += timedelta(days=1)
                
                if optimized_count > 0:
                    total_optimized += optimized_count
                    logger.info(
                        f"Optimized {optimized_count} rates for {property_obj.name} - {rate_plan.name}"
                    )
        
        except Exception as e:
            logger.error(f"Error optimizing rates for {property_obj.name}: {e}", exc_info=True)
    
    logger.info(f"Optimized rates for {total_optimized} date/rate combinations")
    return total_optimized


@shared_task
def apply_pricing_rules():
    """Apply all active automatic pricing rules"""
    today = date.today()
    
    # Get all active automatic pricing rules
    rules = PricingRule.objects.filter(
        is_active=True,
        is_automatic=True
    )
    
    applied_count = 0
    for rule in rules:
        try:
            # Check if rule should be applied today
            if rule.start_date and rule.end_date:
                if not (rule.start_date <= today <= rule.end_date):
                    continue
            
            # Apply rule (this would typically update rates)
            # For now, we just track application
            rule.last_applied_at = timezone.now()
            rule.times_applied += 1
            rule.save()
            
            applied_count += 1
        
        except Exception as e:
            logger.error(f"Error applying pricing rule {rule.id}: {e}", exc_info=True)
    
    logger.info(f"Applied {applied_count} pricing rules")
    return applied_count
