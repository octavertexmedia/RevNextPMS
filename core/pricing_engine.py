"""
Dynamic Pricing Engine
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List
from django.utils import timezone
from django.db import models
from djmoney.money import Money

from .models import RatePlan, PricingRule, Inventory, Property


class PricingEngine:
    """Engine for applying dynamic pricing rules"""
    
    def __init__(self, property_obj: Property):
        self.property = property_obj
    
    def calculate_rate(
        self,
        rate_plan: RatePlan,
        check_in_date: date,
        check_out_date: date,
        occupancy: Optional[float] = None,
        booking_date: Optional[date] = None
    ) -> Money:
        """
        Calculate final rate after applying all applicable pricing rules
        
        Args:
            rate_plan: The rate plan to calculate rate for
            check_in_date: Check-in date
            check_out_date: Check-out date
            occupancy: Current occupancy percentage (for demand-based pricing)
            booking_date: Date when booking is being made (for advance booking discounts)
        
        Returns:
            Final rate after applying all rules
        """
        base_rate = rate_plan.base_rate
        nights = (check_out_date - check_in_date).days
        
        # Get applicable pricing rules, ordered by priority
        rules = PricingRule.objects.filter(
            property=self.property,
            is_active=True,
            is_automatic=True
        ).filter(
            models.Q(rate_plan=rate_plan) | models.Q(rate_plan__isnull=True)
        ).order_by('-priority')
        
        # Apply rules for each night
        total_rate = Money(0, base_rate.currency)
        
        for night in range(nights):
            current_date = check_in_date + timedelta(days=night)
            night_rate = base_rate
            
            # Get occupancy for this date if not provided
            if occupancy is None:
                occupancy = self._get_occupancy_for_date(current_date, rate_plan.room_type)
            
            # Calculate advance booking days
            advance_days = None
            if booking_date:
                advance_days = (check_in_date - booking_date).days
            
            # Apply all applicable rules
            for rule in rules:
                night_rate = rule.apply_to_rate(
                    night_rate,
                    current_date,
                    occupancy=occupancy,
                    booking_date=booking_date
                )
            
            # Apply length of stay discount if applicable
            if rate_plan.los_based_rates:
                los_discount = self._get_los_discount(rate_plan, nights)
                if los_discount:
                    night_rate = Money(
                        night_rate.amount * (1 - los_discount / 100),
                        night_rate.currency
                    )
            
            total_rate += night_rate
        
        return total_rate
    
    def _get_occupancy_for_date(self, date_obj: date, room_type) -> float:
        """Get occupancy percentage for a specific date and room type"""
        try:
            inventory = Inventory.objects.get(
                property=self.property,
                room_type=room_type,
                date=date_obj
            )
            if inventory.total_rooms > 0:
                occupied = inventory.total_rooms - inventory.available_rooms - inventory.blocked_rooms
                return (occupied / inventory.total_rooms) * 100
        except Inventory.DoesNotExist:
            pass
        return 0.0
    
    def _get_los_discount(self, rate_plan: RatePlan, nights: int) -> Optional[float]:
        """Get length of stay discount percentage"""
        if not rate_plan.los_based_rates:
            return None
        
        # Find the best matching LOS discount
        best_discount = None
        best_nights = 0
        
        for los_nights_str, discount_config in rate_plan.los_based_rates.items():
            try:
                los_nights = int(los_nights_str)
                if los_nights <= nights and los_nights > best_nights:
                    best_nights = los_nights
                    best_discount = discount_config.get('discount_percent', 0)
            except (ValueError, KeyError):
                continue
        
        return best_discount
    
    def apply_seasonal_adjustments(self, start_date: date, end_date: date):
        """Apply seasonal pricing adjustments to rate plans"""
        from .models import RatePlan
        
        rate_plans = RatePlan.objects.filter(
            property=self.property,
            is_active=True
        )
        
        seasonal_rules = PricingRule.objects.filter(
            property=self.property,
            rule_type='seasonal',
            is_active=True,
            is_automatic=True,
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        applied_count = 0
        for rule in seasonal_rules:
            applicable_plans = rate_plans
            if rule.rate_plan:
                applicable_plans = rate_plans.filter(id=rule.rate_plan.id)
            
            for rate_plan in applicable_plans:
                # Apply rule to rate plan (this would typically update rates in the system)
                # For now, we just track that it was applied
                applied_count += 1
        
        return applied_count
    
    def optimize_rates_for_demand(
        self,
        date_obj: date,
        room_type,
        target_occupancy: float = 80.0
    ) -> Optional[Money]:
        """
        Optimize rates based on current demand and target occupancy
        
        Args:
            date_obj: Date to optimize rates for
            room_type: Room type to optimize
            target_occupancy: Target occupancy percentage
        
        Returns:
            Optimized rate or None if no optimization needed
        """
        current_occupancy = self._get_occupancy_for_date(date_obj, room_type)
        
        # Get base rate plan
        rate_plan = RatePlan.objects.filter(
            property=self.property,
            room_type=room_type,
            is_active=True
        ).first()
        
        if not rate_plan:
            return None
        
        base_rate = rate_plan.base_rate
        
        # If occupancy is below target, decrease price
        if current_occupancy < target_occupancy:
            # Calculate adjustment based on occupancy gap
            occupancy_gap = target_occupancy - current_occupancy
            # More aggressive discount for larger gaps
            discount_percent = min(occupancy_gap * 0.5, 20)  # Max 20% discount
            
            optimized_rate = Money(
                base_rate.amount * (1 - discount_percent / 100),
                base_rate.currency
            )
            
            # Apply min price constraint
            demand_rules = PricingRule.objects.filter(
                property=self.property,
                rule_type='demand',
                is_active=True,
                rate_plan=rate_plan
            )
            
            for rule in demand_rules:
                if rule.min_price and optimized_rate.amount < rule.min_price.amount:
                    optimized_rate = rule.min_price
            
            return optimized_rate
        
        # If occupancy is above target, increase price
        elif current_occupancy > target_occupancy:
            # Calculate adjustment based on occupancy excess
            occupancy_excess = current_occupancy - target_occupancy
            # More aggressive increase for higher occupancy
            increase_percent = min(occupancy_excess * 0.3, 15)  # Max 15% increase
            
            optimized_rate = Money(
                base_rate.amount * (1 + increase_percent / 100),
                base_rate.currency
            )
            
            # Apply max price constraint
            demand_rules = PricingRule.objects.filter(
                property=self.property,
                rule_type='demand',
                is_active=True,
                rate_plan=rate_plan
            )
            
            for rule in demand_rules:
                if rule.max_price and optimized_rate.amount > rule.max_price.amount:
                    optimized_rate = rule.max_price
            
            return optimized_rate
        
        return None  # No optimization needed
