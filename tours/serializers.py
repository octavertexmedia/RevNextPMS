from rest_framework import serializers

from .models import Departure, ItineraryDay, TourAgent, TourBooking, TourPackage, ToursConfig


class ToursConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToursConfig
        fields = [
            'id', 'tenant', 'is_enabled', 'default_currency', 'brand_name',
            'support_email', 'cancellation_policy', 'require_phone',
            'allow_agent_bookings', 'widget_primary_color', 'terms_url',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class ItineraryDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItineraryDay
        fields = [
            'id', 'package', 'day_number', 'title', 'description',
            'location', 'meals', 'overnight',
        ]


class DepartureSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source='package.name', read_only=True)
    seats_remaining = serializers.IntegerField(read_only=True)
    is_bookable = serializers.BooleanField(read_only=True)
    adult_price_value = serializers.SerializerMethodField()
    child_price_value = serializers.SerializerMethodField()

    class Meta:
        model = Departure
        fields = [
            'id', 'package', 'package_name', 'start_date', 'end_date',
            'capacity', 'booked_seats', 'seats_remaining', 'is_bookable',
            'adult_price_value', 'child_price_value', 'status', 'cutoff_days',
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'booked_seats', 'seats_remaining', 'is_bookable',
                            'package_name', 'created_at', 'updated_at']

    def get_adult_price_value(self, obj):
        p = obj.effective_adult_price()
        return float(p.amount) if p else None

    def get_child_price_value(self, obj):
        p = obj.effective_child_price()
        return float(p.amount) if p else None


class TourPackageSerializer(serializers.ModelSerializer):
    itinerary_days = ItineraryDaySerializer(many=True, read_only=True)
    base_price_value = serializers.DecimalField(
        source='base_price.amount', max_digits=14, decimal_places=2, required=False,
    )
    upcoming_departures = serializers.SerializerMethodField()

    class Meta:
        model = TourPackage
        fields = [
            'id', 'tenant', 'property', 'name', 'slug', 'description', 'short_description',
            'category', 'difficulty', 'destinations', 'inclusions', 'exclusions', 'highlights',
            'duration_days', 'duration_nights', 'min_pax', 'max_pax',
            'base_price', 'base_price_value', 'currency', 'cover_image_url',
            'is_active', 'is_published', 'itinerary_days', 'upcoming_departures',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'tenant', 'itinerary_days', 'upcoming_departures',
            'created_at', 'updated_at',
        ]
        extra_kwargs = {'base_price': {'required': False}}

    def get_upcoming_departures(self, obj):
        qs = obj.departures.filter(status__in=('OPEN', 'GUARANTEED')).order_by('start_date')[:5]
        return DepartureSerializer(qs, many=True).data


class TourBookingSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source='package.name', read_only=True)
    departure_start = serializers.DateField(source='departure.start_date', read_only=True)
    total_amount_value = serializers.DecimalField(
        source='total_amount.amount', max_digits=14, decimal_places=2, read_only=True,
    )
    agent_name = serializers.CharField(source='agent.company_name', read_only=True, allow_null=True)

    class Meta:
        model = TourBooking
        fields = [
            'id', 'departure', 'package', 'package_name', 'departure_start',
            'agent', 'agent_name', 'guest_name', 'guest_email', 'guest_phone',
            'adults', 'children', 'total_pax', 'total_amount_value', 'currency',
            'status', 'confirmation_code', 'special_requests', 'channel_host',
            'source', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class TourAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourAgent
        fields = [
            'id', 'tenant', 'company_name', 'contact_email', 'contact_phone',
            'commission_percent', 'is_active', 'portal_enabled',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class PublicTourSearchSerializer(serializers.Serializer):
    destination = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True)
    start_from = serializers.DateField(required=False)
    start_to = serializers.DateField(required=False)
    min_days = serializers.IntegerField(required=False, min_value=1)
    max_days = serializers.IntegerField(required=False, min_value=1)


class PublicCreateTourBookingSerializer(serializers.Serializer):
    departure_id = serializers.IntegerField()
    guest_name = serializers.CharField(max_length=255)
    guest_email = serializers.EmailField()
    guest_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    adults = serializers.IntegerField(min_value=1, default=1)
    children = serializers.IntegerField(min_value=0, default=0)
    special_requests = serializers.CharField(required=False, allow_blank=True)
