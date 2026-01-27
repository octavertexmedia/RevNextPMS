"""
Serializers for Integrations API
"""
from rest_framework import serializers
from .models import IntegrationPlatform, PropertyIntegration, SyncLog


class IntegrationPlatformSerializer(serializers.ModelSerializer):
    """Serializer for Integration Platforms"""
    
    class Meta:
        model = IntegrationPlatform
        fields = [
            'id', 'name', 'display_name', 'platform_type',
            'api_base_url', 'auth_type',
            'rate_limit_rpm', 'rate_limit_rps',
            'supports_webhooks', 'supports_polling', 'supports_batch_updates',
            'is_active', 'is_connected', 'last_sync_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'last_sync_at', 'created_at', 'updated_at']


class PropertyIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for Property Integrations"""
    property_name = serializers.CharField(source='property.name', read_only=True)
    platform_name = serializers.CharField(source='platform.display_name', read_only=True)
    
    class Meta:
        model = PropertyIntegration
        fields = [
            'id', 'property', 'property_name',
            'platform', 'platform_name',
            'provider_property_id',
            'sync_availability', 'sync_rates', 'sync_inventory', 'sync_reservations',
            'availability_sync_interval', 'rates_sync_interval',
            'inventory_sync_interval', 'reservations_sync_interval',
            'is_active',
            'last_availability_sync', 'last_rates_sync',
            'last_inventory_sync', 'last_reservations_sync',
            'error_count', 'last_error',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'last_availability_sync', 'last_rates_sync',
            'last_inventory_sync', 'last_reservations_sync',
            'error_count', 'last_error', 'created_at', 'updated_at',
        ]


class SyncLogSerializer(serializers.ModelSerializer):
    """Serializer for Sync Logs"""
    platform_name = serializers.CharField(source='platform.display_name', read_only=True)
    property_name = serializers.CharField(source='property_integration.property.name', read_only=True)
    
    class Meta:
        model = SyncLog
        fields = [
            'id', 'platform', 'platform_name',
            'property_integration', 'property_name',
            'sync_type', 'status',
            'started_at', 'completed_at', 'duration_seconds',
            'records_processed', 'records_succeeded', 'records_failed',
            'error_message', 'error_details',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
