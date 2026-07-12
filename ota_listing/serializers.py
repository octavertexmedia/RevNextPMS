from rest_framework import serializers
from .models import ListingProject


class ListingProjectSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    platform_name = serializers.CharField(source='platform.name', read_only=True)

    class Meta:
        model = ListingProject
        fields = [
            'id', 'property', 'property_name', 'platform', 'platform_name',
            'status', 'provider_property_id', 'listing_score',
            'optimization_notes', 'completed_at', 'created_at', 'updated_at',
        ]
        read_only_fields = fields
