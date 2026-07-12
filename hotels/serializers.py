from rest_framework import serializers

from .models import AggregatorListing, ListingClaim, MetasearchFeedJob


class AggregatorListingSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    min_price_value = serializers.DecimalField(
        source='min_price_hint.amount', max_digits=14, decimal_places=2,
        read_only=True, allow_null=True,
    )

    class Meta:
        model = AggregatorListing
        fields = [
            'id', 'property', 'property_name', 'tenant', 'slug', 'headline', 'summary',
            'amenities', 'star_rating', 'cover_image_url', 'gallery',
            'check_in_time', 'check_out_time', 'status', 'is_featured', 'is_claimable',
            'booking_engine_url', 'min_price_value', 'city', 'state', 'country',
            'published_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'tenant', 'property_name', 'min_price_value', 'published_at',
            'created_at', 'updated_at',
        ]


class ListingClaimSerializer(serializers.ModelSerializer):
    listing_slug = serializers.CharField(source='listing.slug', read_only=True)
    listing_headline = serializers.CharField(source='listing.headline', read_only=True)

    class Meta:
        model = ListingClaim
        fields = [
            'id', 'listing', 'listing_slug', 'listing_headline',
            'claimant_tenant', 'contact_email', 'contact_name', 'company_name',
            'evidence_url', 'evidence_notes', 'status', 'reviewed_at', 'review_notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'listing_slug', 'listing_headline', 'claimant_tenant',
            'status', 'reviewed_at', 'review_notes', 'created_at', 'updated_at',
        ]


class MetasearchFeedJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetasearchFeedJob
        fields = [
            'id', 'tenant', 'feed_type', 'partner', 'status', 'listings_count',
            'artifact_url', 'payload_summary', 'error_message', 'completed_at',
            'created_at',
        ]
        read_only_fields = fields


class PublicSearchSerializer(serializers.Serializer):
    city = serializers.CharField(required=False, allow_blank=True)
    q = serializers.CharField(required=False, allow_blank=True)
    check_in = serializers.DateField(required=False)
    check_out = serializers.DateField(required=False)
    guests = serializers.IntegerField(required=False, min_value=1, default=2)
    featured = serializers.BooleanField(required=False, default=False)


class PublicClaimSerializer(serializers.Serializer):
    listing_slug = serializers.SlugField()
    contact_name = serializers.CharField(max_length=255)
    contact_email = serializers.EmailField()
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    evidence_url = serializers.URLField(required=False, allow_blank=True)
    evidence_notes = serializers.CharField(required=False, allow_blank=True)
