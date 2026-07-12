from rest_framework import serializers
from .models import HotelAdsConfig, FeedSubmission


class FeedSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedSubmission
        fields = [
            'id', 'property', 'status', 'rooms_count', 'rates_count',
            'submitted_at', 'response_data',
        ]
        read_only_fields = fields


class HotelAdsConfigSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)

    class Meta:
        model = HotelAdsConfig
        fields = [
            'id', 'property', 'property_name',
            'google_hotel_id', 'partner_hotel_id',
            'is_enabled', 'commission_model',
            'last_feed_submitted', 'feed_status',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields
