"""
Integration Platform Models

Schema Mapping Overview:
-----------------------
This generic schema connects internal core models to external OTA platforms.

1. IntegrationPlatform: The external channel itself (e.g., Booking.com, Expedia).

2. PropertyIntegration:
   - Connects a local 'Property' to an 'IntegrationPlatform'.
   - Stores 'provider_property_id' (e.g., Hotel ID on Booking.com).
   - "The Bridge" for all other mappings.

3. RoomTypeMapping:
   - Maps internal 'RoomType' <-> External 'provider_room_type_id'.
   - Linked via PropertyIntegration.

4. RatePlanMapping:
   - Maps internal 'RatePlan' <-> External 'provider_rate_plan_id'.
   - Linked via PropertyIntegration.
   - Allows pricing adjustments (e.g., +15% for this channel).

"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from simple_history.models import HistoricalRecords
from core.models import Property, TimeStampedModel, RoomType, RatePlan


class IntegrationPlatform(TimeStampedModel):
    """Platform/OTA integration configuration"""
    
    PLATFORM_TYPES = [
        ('OTA', 'Online Travel Agency'),
        ('GDS', 'Global Distribution System'),
        ('METASEARCH', 'Metasearch Engine'),
        ('BEDBANK', 'Bedbank'),
        ('AGGREGATOR', 'Aggregator'),
        ('OTHER', 'Other'),
    ]
    
    AUTH_TYPES = [
        ('API_KEY', 'API Key'),
        ('OAUTH2', 'OAuth 2.0'),
        ('BASIC_AUTH', 'Basic Authentication'),
        ('SIGNATURE', 'Signature-based'),
        ('TOKEN', 'Token-based'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, help_text="Platform name, e.g., 'booking.com', 'expedia'")
    display_name = models.CharField(max_length=255)
    platform_type = models.CharField(max_length=20, choices=PLATFORM_TYPES)
    
    # API Configuration
    api_base_url = models.URLField(blank=True)
    api_version = models.CharField(max_length=20, blank=True)
    auth_type = models.CharField(max_length=20, choices=AUTH_TYPES, default='API_KEY')
    
    # Credentials — prefer OpenBao via secret_ref; DB fields are fallback
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    additional_credentials = models.JSONField(default=dict, blank=True)
    secret_ref = models.CharField(
        max_length=255,
        blank=True,
        help_text='OpenBao KV path for platform credentials',
    )
    
    # Rate Limiting
    rate_limit_rpm = models.PositiveIntegerField(
        default=1000,
        help_text="Rate limit: requests per minute"
    )
    rate_limit_rps = models.PositiveIntegerField(
        default=100,
        help_text="Rate limit: requests per second"
    )
    
    # Features
    supports_webhooks = models.BooleanField(default=False)
    supports_polling = models.BooleanField(default=True)
    supports_batch_updates = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_connected = models.BooleanField(default=False)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    
    # Configuration
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Platform-specific configuration"
    )
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.display_name

    def resolved_credentials(self) -> dict:
        from channel_manager.openbao.credentials import resolve_mapping
        return resolve_mapping(
            secret_ref=self.secret_ref,
            local={
                'api_key': self.api_key,
                'api_secret': self.api_secret,
                **(self.additional_credentials or {}),
            },
        )


class PropertyIntegration(TimeStampedModel):
    """Property-specific integration configuration"""
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='integrations')
    platform = models.ForeignKey(IntegrationPlatform, on_delete=models.CASCADE, related_name='property_integrations')
    
    # Provider-specific IDs
    provider_property_id = models.CharField(max_length=255, db_index=True)
    provider_room_type_mappings = models.JSONField(
        default=dict,
        help_text="Mapping of internal room_type_id to provider room_type_id"
    )
    provider_rate_plan_mappings = models.JSONField(
        default=dict,
        help_text="Mapping of internal rate_plan_id to provider rate_plan_id"
    )
    
    # Sync Settings
    sync_availability = models.BooleanField(default=True)
    sync_rates = models.BooleanField(default=True)
    sync_inventory = models.BooleanField(default=True)
    sync_reservations = models.BooleanField(default=True)
    
    # Sync Frequency (in minutes)
    availability_sync_interval = models.PositiveIntegerField(default=5)
    rates_sync_interval = models.PositiveIntegerField(default=15)
    inventory_sync_interval = models.PositiveIntegerField(default=5)
    reservations_sync_interval = models.PositiveIntegerField(default=10)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_availability_sync = models.DateTimeField(null=True, blank=True)
    last_rates_sync = models.DateTimeField(null=True, blank=True)
    last_inventory_sync = models.DateTimeField(null=True, blank=True)
    last_reservations_sync = models.DateTimeField(null=True, blank=True)
    
    # Error Tracking
    last_error = models.TextField(blank=True)
    error_count = models.PositiveIntegerField(default=0)
    last_error_at = models.DateTimeField(null=True, blank=True)
    
    # Configuration + OpenBao secret path for property-level OTA credentials
    config = models.JSONField(default=dict, blank=True)
    secret_ref = models.CharField(
        max_length=255,
        blank=True,
        help_text='OpenBao KV path for this property↔platform credential set',
    )
    
    history = HistoricalRecords()

    class Meta:
        unique_together = ['property', 'platform']
        indexes = [
            models.Index(fields=['property', 'platform']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.property.name} - {self.platform.display_name}"

    def ensure_secret_ref(self):
        if self.secret_ref:
            return self.secret_ref
        tenant_id = self.property.tenant_id
        if not tenant_id:
            return ''
        from channel_manager.openbao.credentials import openbao_path_for_integration
        code = self.platform.name.replace('.', '_').lower()
        self.secret_ref = openbao_path_for_integration(tenant_id, self.property_id, code)
        return self.secret_ref

    def resolved_credentials(self) -> dict:
        """Property credentials overlay platform credentials; OpenBao wins when set."""
        from channel_manager.openbao.credentials import resolve_mapping
        base = self.platform.resolved_credentials()
        self.ensure_secret_ref()
        local = {**(self.config or {})}
        overlay = resolve_mapping(secret_ref=self.secret_ref, local=local)
        merged = dict(base)
        merged.update({k: v for k, v in overlay.items() if v not in (None, '')})
        return merged


class RoomTypeMapping(TimeStampedModel):
    """
    Mapping between internal RoomType and provider-specific room type ID.
    Replaces JSON-based mapping.
    """
    id = models.BigAutoField(primary_key=True)
    property_integration = models.ForeignKey(
        PropertyIntegration, 
        on_delete=models.CASCADE, 
        related_name='room_type_mappings'
    )
    room_type = models.ForeignKey(
        RoomType, 
        on_delete=models.CASCADE, 
        related_name='provider_mappings_rel'
    )
    
    # Provider-side details
    provider_room_type_id = models.CharField(max_length=255)
    provider_room_name = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Room Type Mapping'
        verbose_name_plural = 'Room Type Mappings'
        unique_together = [
            ('property_integration', 'room_type'),
            ('property_integration', 'provider_room_type_id'),
        ]
        ordering = ['ordering', 'room_type__name']

    def __str__(self):
        return f"{self.property_integration.platform.name} - {self.room_type.name} -> {self.provider_room_type_id}"


class RatePlanMapping(TimeStampedModel):
    """
    Mapping between internal RatePlan and provider-specific rate plan ID.
    Allows for price adjustments per channel.
    """
    PRICING_MODES = [
        ('SAME_AS_BASE', 'Same as Base'),
        ('PERCENTAGE_ADJUSTMENT', 'Percentage Adjustment'),
        ('FIXED_ADJUSTMENT', 'Fixed Amount Adjustment'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    property_integration = models.ForeignKey(
        PropertyIntegration, 
        on_delete=models.CASCADE, 
        related_name='rate_plan_mappings'
    )
    rate_plan = models.ForeignKey(
        RatePlan, 
        on_delete=models.CASCADE, 
        related_name='provider_mappings_rel'
    )
    
    # Provider-side details
    provider_rate_plan_id = models.CharField(max_length=255)
    provider_rate_plan_name = models.CharField(max_length=255, blank=True)
    
    # Price Management
    pricing_mode = models.CharField(
        max_length=50, 
        choices=PRICING_MODES, 
        default='SAME_AS_BASE'
    )
    pricing_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Percentage or fixed amount to add/subtract"
    )
    
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Rate Plan Mapping'
        verbose_name_plural = 'Rate Plan Mappings'
        unique_together = [
            ('property_integration', 'rate_plan'),
            ('property_integration', 'provider_rate_plan_id'),
        ]

    def __str__(self):
        return f"{self.property_integration.platform.name} - {self.rate_plan.name} -> {self.provider_rate_plan_id}"


class SyncLog(TimeStampedModel):
    """Log of synchronization operations"""
    
    SYNC_TYPES = [
        ('AVAILABILITY', 'Availability'),
        ('RATES', 'Rates'),
        ('INVENTORY', 'Inventory'),
        ('RESERVATIONS', 'Reservations'),
        ('CONTENT', 'Content'),
        ('FULL', 'Full Sync'),
    ]
    
    STATUS = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partial Success'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    property_integration = models.ForeignKey(
        PropertyIntegration,
        on_delete=models.CASCADE,
        related_name='sync_logs',
        null=True,
        blank=True
    )
    platform = models.ForeignKey(
        IntegrationPlatform,
        on_delete=models.CASCADE,
        related_name='sync_logs',
        null=True,
        blank=True
    )
    
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    
    # Results
    records_processed = models.PositiveIntegerField(default=0)
    records_succeeded = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    
    # Error Details
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    # Request/Response
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property_integration', 'sync_type', 'status']),
            models.Index(fields=['platform', 'status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.get_status_display()} - {self.created_at}"

