"""
Canonical Data Model for Channel Manager

Core Schema Overview:
--------------------
1. Property: Top-level entity (Source of Truth)
   - Maps to IntegrationPlatform via PropertyIntegration

2. RoomType: Specific category of rooms
   - Connects to Property (Many-to-One)
   - Maps to external channels via RoomTypeMapping (in integrations app)

3. RatePlan: Pricing strategy for a given RoomType
   - Connects to RoomType (Many-to-One)
   - Maps to external channels via RatePlanMapping (in integrations app)

Data Flow:
Core Models (Property, Room, Rate) <--> Mappings (PropertyIntegration, RoomTypeMapping) <--> External Platform
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from location_field.models.plain import PlainLocationField
from simple_history.models import HistoricalRecords


class TimeStampedModel(models.Model):
    """Abstract base model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Property(TimeStampedModel):
    """Hotel/Property entity - core of the canonical data model"""
    
    PROPERTY_TYPES = [
        ('hotel', 'Hotel'),
        ('resort', 'Resort'),
        ('apartment', 'Apartment'),
        ('hostel', 'Hostel'),
        ('guesthouse', 'Guesthouse'),
        ('villa', 'Villa'),
        ('other', 'Other'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    
    # Tenant relationship - each property belongs to a tenant
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='properties',
        null=True,
        blank=True,
        help_text="The hotel owner/tenant who owns this property"
    )
    
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default='hotel')
    
    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    location = PlainLocationField(based_fields=['city'], zoom=7, blank=True)
    
    # Contact
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Business Details
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    currency = models.CharField(max_length=3, default='INR')
    
    # GST Details (India-specific)
    gstin = models.CharField(max_length=15, blank=True, help_text="GST Identification Number")
    pan = models.CharField(max_length=10, blank=True, help_text="Permanent Account Number")
    
    # Provider Mappings - stores external platform IDs
    provider_mappings = models.JSONField(
        default=dict,
        help_text="Mapping of provider names to their property IDs, e.g., {'booking.com': '12345', 'expedia': '67890'}"
    )
    
    # Extensibility - store provider-specific data
    provider_specific_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Store any provider-specific attributes that don't fit the canonical schema"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = 'Properties'
        ordering = ['name']

    def __str__(self):
        return self.name


class RoomType(TimeStampedModel):
    """Room type definition"""
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='room_types')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Capacity
    max_occupancy = models.PositiveIntegerField(default=2)
    base_occupancy = models.PositiveIntegerField(default=2)
    max_adults = models.PositiveIntegerField(default=2)
    max_children = models.PositiveIntegerField(default=2)
    
    # Physical attributes
    size_sqm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    bed_type = models.CharField(max_length=100, blank=True)
    amenities = models.JSONField(
        default=list,
        help_text="List of amenities, e.g., ['wifi', 'ac', 'tv', 'minibar']"
    )
    
    # Provider Mappings
    provider_mappings = models.JSONField(default=dict)
    provider_specific_data = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['property', 'name']

    def __str__(self):
        return f"{self.property.name} - {self.name}"


class MealPlan(models.Model):
    """Meal plan definitions"""
    
    MEAL_PLAN_TYPES = [
        ('ROOM_ONLY', 'Room Only'),
        ('BREAKFAST', 'Breakfast'),
        ('HALF_BOARD', 'Half Board'),
        ('FULL_BOARD', 'Full Board'),
        ('ALL_INCLUSIVE', 'All Inclusive'),
    ]
    
    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Policy(TimeStampedModel):
    """Cancellation, prepayment, and no-show policies"""
    
    POLICY_TYPES = [
        ('CANCELLATION', 'Cancellation'),
        ('PREPAYMENT', 'Prepayment'),
        ('NO_SHOW', 'No Show'),
    ]
    
    PENALTY_TYPES = [
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
        ('NIGHTS', 'Number of Nights'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    
    # Flexible details stored as JSON
    details = models.JSONField(
        default=dict,
        help_text="Policy rules, e.g., {'cancellation_window_hours': 48, 'penalty_type': 'PERCENTAGE', 'penalty_value': 100}"
    )
    
    description = models.TextField(blank=True)
    
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = 'Policies'

    def __str__(self):
        return f"{self.get_policy_type_display()} - {self.name}"


class RatePlan(TimeStampedModel):
    """Rate plan definition with pricing rules"""
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rate_plans')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rate_plans')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Meal Plan
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.SET_NULL, null=True, blank=True)
    inclusions = models.JSONField(
        default=list,
        help_text="List of inclusions, e.g., ['wifi', 'breakfast', 'parking']"
    )
    
    # Base Pricing
    base_rate = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    base_occupancy = models.PositiveIntegerField(default=2)
    
    # Occupancy-based pricing
    extra_adult_charge = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    extra_child_charge = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    
    # Length of Stay (LOS) pricing
    los_based_rates = models.JSONField(
        default=dict,
        blank=True,
        help_text="LOS pricing rules, e.g., {'3': {'discount_percent': 5}, '7': {'discount_percent': 10}}"
    )
    
    # Derived/Linked Rates
    is_derived = models.BooleanField(default=False)
    parent_rate_plan = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='derived_rates'
    )
    derivation_rule = models.JSONField(
        default=dict,
        blank=True,
        help_text="Derivation rules, e.g., {'discount_percent': 10} for 10% off parent rate"
    )
    
    # Policies
    cancellation_policy = models.ForeignKey(
        Policy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rate_plans_cancellation',
        limit_choices_to={'policy_type': 'CANCELLATION'}
    )
    prepayment_policy = models.ForeignKey(
        Policy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rate_plans_prepayment',
        limit_choices_to={'policy_type': 'PREPAYMENT'}
    )
    no_show_policy = models.ForeignKey(
        Policy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rate_plans_no_show',
        limit_choices_to={'policy_type': 'NO_SHOW'}
    )
    
    # Provider Mappings
    provider_mappings = models.JSONField(default=dict)
    provider_specific_data = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['property', 'room_type', 'name']

    def __str__(self):
        return f"{self.property.name} - {self.room_type.name} - {self.name}"


class Inventory(TimeStampedModel):
    """Availability and inventory tracking per room type per date"""
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inventory')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='inventory')
    date = models.DateField()
    
    # Availability
    available_rooms = models.PositiveIntegerField(default=0)
    total_rooms = models.PositiveIntegerField(default=0)
    
    # Blocks
    blocked_rooms = models.PositiveIntegerField(default=0, help_text="Manually blocked rooms")
    
    # Version for conflict resolution
    version = models.PositiveIntegerField(default=1)
    
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = 'Inventories'
        unique_together = ['property', 'room_type', 'date']
        ordering = ['date']
        indexes = [
            models.Index(fields=['property', 'date']),
            models.Index(fields=['room_type', 'date']),
        ]

    def __str__(self):
        return f"{self.property.name} - {self.room_type.name} - {self.date} ({self.available_rooms}/{self.total_rooms})"


class PricingRule(TimeStampedModel):
    """Dynamic pricing rules for automated rate adjustments"""
    
    RULE_TYPES = [
        ('seasonal', 'Seasonal Adjustment'),
        ('demand', 'Demand-Based Pricing'),
        ('competitor', 'Competitor-Based Pricing'),
        ('length_of_stay', 'Length of Stay Discount'),
        ('advance_booking', 'Advance Booking Discount'),
        ('last_minute', 'Last Minute Pricing'),
        ('occupancy', 'Occupancy-Based Pricing'),
    ]
    
    ADJUSTMENT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('multiplier', 'Multiplier'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='pricing_rules')
    rate_plan = models.ForeignKey(
        RatePlan,
        on_delete=models.CASCADE,
        related_name='pricing_rules',
        null=True,
        blank=True,
        help_text="If null, applies to all rate plans for the property"
    )
    
    # Rule Configuration
    name = models.CharField(max_length=255)
    rule_type = models.CharField(max_length=50, choices=RULE_TYPES)
    description = models.TextField(blank=True)
    
    # Adjustment Configuration
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES, default='percentage')
    adjustment_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Percentage, fixed amount, or multiplier based on adjustment_type"
    )
    
    # Conditions
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Rule conditions, e.g., {'min_occupancy': 80, 'date_range': ['2024-12-01', '2024-12-31']}"
    )
    
    # Seasonal Configuration
    start_date = models.DateField(null=True, blank=True, help_text="Seasonal rule start date")
    end_date = models.DateField(null=True, blank=True, help_text="Seasonal rule end date")
    recurrence = models.JSONField(
        default=dict,
        blank=True,
        help_text="Recurrence pattern, e.g., {'type': 'yearly', 'months': [12, 1], 'days': [1, 31]}"
    )
    
    # Demand-Based Configuration
    occupancy_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Occupancy percentage threshold for demand-based pricing"
    )
    min_price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency='INR',
        null=True,
        blank=True,
        help_text="Minimum price after adjustment"
    )
    max_price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency='INR',
        null=True,
        blank=True,
        help_text="Maximum price after adjustment"
    )
    
    # Priority (higher priority rules are applied first)
    priority = models.IntegerField(default=0, help_text="Higher priority rules are applied first")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_automatic = models.BooleanField(
        default=True,
        help_text="If True, rule is automatically applied by scheduled task"
    )
    
    # Execution tracking
    last_applied_at = models.DateTimeField(null=True, blank=True)
    times_applied = models.PositiveIntegerField(default=0)
    
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['property', 'is_active', 'rule_type']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - {self.name} ({self.get_rule_type_display()})"
    
    def apply_to_rate(self, base_rate, date, occupancy=None, booking_date=None):
        """Apply pricing rule to a base rate"""
        if not self.is_active:
            return base_rate
        
        # Check conditions
        if not self._check_conditions(date, occupancy, booking_date):
            return base_rate
        
        # Apply adjustment
        if self.adjustment_type == 'percentage':
            adjustment = base_rate.amount * (self.adjustment_value / 100)
            new_rate = base_rate.amount + adjustment
        elif self.adjustment_type == 'fixed':
            new_rate = base_rate.amount + self.adjustment_value
        elif self.adjustment_type == 'multiplier':
            new_rate = base_rate.amount * self.adjustment_value
        else:
            return base_rate
        
        # Apply min/max constraints
        if self.min_price and new_rate < self.min_price.amount:
            new_rate = self.min_price.amount
        if self.max_price and new_rate > self.max_price.amount:
            new_rate = self.max_price.amount
        
        from djmoney.money import Money
        return Money(new_rate, base_rate.currency)
    
    def _check_conditions(self, date, occupancy=None, booking_date=None):
        """Check if rule conditions are met"""
        # Date range check
        if self.start_date and self.end_date:
            if not (self.start_date <= date <= self.end_date):
                return False
        
        # Occupancy check
        if self.occupancy_threshold and occupancy is not None:
            if occupancy < self.occupancy_threshold:
                return False
        
        # Custom conditions
        if self.conditions:
            # Check date range in conditions
            if 'date_range' in self.conditions:
                date_range = self.conditions['date_range']
                if not (date_range[0] <= str(date) <= date_range[1]):
                    return False
            
            # Check min occupancy
            if 'min_occupancy' in self.conditions and occupancy is not None:
                if occupancy < self.conditions['min_occupancy']:
                    return False
        
        return True


class Restrictions(TimeStampedModel):
    """Restrictions on rate plans (min/max LOS, closed to arrival/departure)"""
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='restrictions')
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.CASCADE, related_name='restrictions', null=True, blank=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='restrictions', null=True, blank=True)
    date = models.DateField()
    
    # Length of Stay restrictions
    min_los = models.PositiveIntegerField(null=True, blank=True, help_text="Minimum length of stay in nights")
    max_los = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum length of stay in nights")
    
    # Closed dates
    closed_to_arrival = models.BooleanField(default=False)
    closed_to_departure = models.BooleanField(default=False)
    
    # Minimum advance booking
    min_advance_booking_days = models.PositiveIntegerField(null=True, blank=True)
    
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = 'Restrictions'
        unique_together = ['property', 'rate_plan', 'date']
        indexes = [
            models.Index(fields=['property', 'date']),
        ]

    def __str__(self):
        return f"{self.property.name} - {self.date}"


class TaxFee(TimeStampedModel):
    """Tax and fee definitions"""
    
    TAX_TYPES = [
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
    ]
    
    GST_COMPONENTS = [
        ('CGST', 'Central GST'),
        ('SGST', 'State GST'),
        ('IGST', 'Integrated GST'),
        ('NONE', 'Not Applicable'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='taxes_fees', null=True, blank=True)
    name = models.CharField(max_length=255)
    tax_type = models.CharField(max_length=20, choices=TAX_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # GST Details (India-specific)
    is_inclusive = models.BooleanField(default=False, help_text="Is tax included in base price?")
    gst_component = models.CharField(max_length=10, choices=GST_COMPONENTS, default='NONE')
    hsn_sac_code = models.CharField(max_length=10, blank=True, help_text="HSN/SAC code for GST")
    
    description = models.TextField(blank=True)
    
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = 'Taxes and Fees'

    def __str__(self):
        return f"{self.name} ({self.get_tax_type_display()})"


class Promotion(TimeStampedModel):
    """Promotional offers and discounts"""
    
    PROMOTION_TYPES = [
        ('PERCENTAGE', 'Percentage Discount'),
        ('FIXED', 'Fixed Amount Discount'),
        ('FREE_NIGHT', 'Free Night'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='promotions', null=True, blank=True)
    name = models.CharField(max_length=255)
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPES)
    
    # Discount details
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Validity
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Eligibility rules stored as JSON
    eligibility_rules = models.JSONField(
        default=dict,
        help_text="Eligibility rules, e.g., {'min_los': 3, 'advance_booking_days': 7}"
    )
    
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.get_promotion_type_display()})"

