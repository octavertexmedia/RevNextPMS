"""REST API for Hotels Aggregator — staff + public discovery."""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.mobile_api import tenant_from_user
from core.models import Property
from products.services import has_product
from rbac.permissions import HasCapability
from tenants.permissions import IsTenantMember

from .models import (
    AggregatorListing,
    ListingClaim,
    MetasearchFeedJob,
    search_listings,
    sync_listing_from_property,
)
from .serializers import (
    AggregatorListingSerializer,
    ListingClaimSerializer,
    MetasearchFeedJobSerializer,
    PublicClaimSerializer,
    PublicSearchSerializer,
)


class AggregatorListingViewSet(viewsets.ModelViewSet):
    serializer_class = AggregatorListingSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'aggregator.listings.view',
        'retrieve': 'aggregator.listings.view',
        'create': 'aggregator.listings.manage',
        'update': 'aggregator.listings.manage',
        'partial_update': 'aggregator.listings.manage',
        'destroy': 'aggregator.listings.manage',
        'publish': 'aggregator.listings.manage',
        'sync_from_property': 'aggregator.listings.manage',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'city', 'is_featured']
    search_fields = ['headline', 'slug', 'city', 'summary']
    ordering = ['-is_featured', 'city']

    def get_queryset(self):
        qs = AggregatorListing.objects.select_related('property', 'tenant')
        if self.request.user.is_superuser:
            return qs
        tenant = tenant_from_user(self.request.user)
        return qs.filter(tenant=tenant) if tenant else qs.none()

    def perform_create(self, serializer):
        tenant = tenant_from_user(self.request.user)
        prop = serializer.validated_data['property']
        if prop.tenant_id != getattr(tenant, 'id', None) and not self.request.user.is_superuser:
            raise PermissionError('Property not in your tenant')
        serializer.save(tenant=tenant)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        listing = self.get_object()
        listing.status = 'PUBLISHED'
        listing.published_at = timezone.now()
        listing.save(update_fields=['status', 'published_at', 'updated_at'])
        return Response(AggregatorListingSerializer(listing).data)

    @action(detail=False, methods=['post'])
    def sync_from_property(self, request):
        property_id = request.data.get('property_id')
        publish = bool(request.data.get('publish'))
        tenant = tenant_from_user(request.user)
        prop = get_object_or_404(Property, id=property_id, tenant=tenant)
        if not has_product(tenant, 'aggregator'):
            return Response(
                {'error': 'product_entitlement_required', 'product': 'aggregator'},
                status=402,
            )
        listing = sync_listing_from_property(prop, publish=publish)
        return Response(AggregatorListingSerializer(listing).data)


class ListingClaimViewSet(viewsets.ModelViewSet):
    serializer_class = ListingClaimSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'aggregator.claims.review',
        'retrieve': 'aggregator.claims.review',
        'create': 'aggregator.listings.manage',
        'update': 'aggregator.claims.review',
        'partial_update': 'aggregator.claims.review',
        'approve': 'aggregator.claims.review',
        'reject': 'aggregator.claims.review',
    }
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    filterset_fields = ['status', 'listing']

    def get_queryset(self):
        qs = ListingClaim.objects.select_related('listing', 'claimant_tenant')
        if self.request.user.is_superuser:
            return qs
        tenant = tenant_from_user(self.request.user)
        return qs.filter(
            Q(listing__tenant=tenant) | Q(claimant_tenant=tenant)
        ).distinct()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        claim = self.get_object()
        claim.status = 'APPROVED'
        claim.reviewed_at = timezone.now()
        claim.review_notes = request.data.get('notes', '')
        claim.save(update_fields=['status', 'reviewed_at', 'review_notes', 'updated_at'])
        if claim.claimant_tenant_id:
            listing = claim.listing
            listing.tenant = claim.claimant_tenant
            listing.property.tenant = claim.claimant_tenant
            listing.property.save(update_fields=['tenant', 'updated_at'])
            listing.save(update_fields=['tenant', 'updated_at'])
        return Response(ListingClaimSerializer(claim).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        claim = self.get_object()
        claim.status = 'REJECTED'
        claim.reviewed_at = timezone.now()
        claim.review_notes = request.data.get('notes', '')
        claim.save(update_fields=['status', 'reviewed_at', 'review_notes', 'updated_at'])
        return Response(ListingClaimSerializer(claim).data)


class MetasearchFeedJobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MetasearchFeedJobSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'google_ads.view',
        'retrieve': 'google_ads.view',
        'run_hotel_list': 'google_ads.manage',
    }

    def get_queryset(self):
        qs = MetasearchFeedJob.objects.all()
        if self.request.user.is_superuser:
            return qs
        tenant = tenant_from_user(self.request.user)
        return qs.filter(tenant=tenant) if tenant else qs.none()

    @action(detail=False, methods=['post'])
    def run_hotel_list(self, request):
        tenant = tenant_from_user(request.user)
        listings = AggregatorListing.objects.filter(tenant=tenant, status='PUBLISHED')
        job = MetasearchFeedJob.objects.create(
            tenant=tenant,
            feed_type='HOTEL_LIST',
            partner=request.data.get('partner', 'google_hotel_ads'),
            status='SUCCESS',
            listings_count=listings.count(),
            payload_summary={
                'slugs': list(listings.values_list('slug', flat=True)[:200]),
                'generated_at': timezone.now().isoformat(),
            },
            completed_at=timezone.now(),
        )
        return Response(MetasearchFeedJobSerializer(job).data, status=201)


# ─── Public discovery (hotels.revnext.in) ───────────────────────────────────

def _serialize_search_item(item):
    listing = item['listing']
    price = item.get('from_price')
    return {
        **AggregatorListingSerializer(listing).data,
        'available': item['available'],
        'nights': item.get('nights'),
        'from_price': float(price.amount) if price else None,
        'currency': str(price.currency) if price else listing.property.currency if listing.property_id else 'INR',
        'book_url': listing.booking_engine_url or f'https://booking.revnext.in/booking/widget/{listing.property_id}/',
    }


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def public_search(request):
    if request.method == 'POST':
        ser = PublicSearchSerializer(data=request.data)
    else:
        ser = PublicSearchSerializer(data=request.query_params)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    results = search_listings(
        city=data.get('city') or '',
        q=data.get('q') or '',
        check_in=data.get('check_in'),
        check_out=data.get('check_out'),
        guests=data.get('guests') or 2,
        featured_only=bool(data.get('featured')),
    )
    # Hide listings whose tenant lost aggregator entitlement
    payload = []
    for item in results:
        if has_product(item['listing'].tenant, 'aggregator'):
            payload.append(_serialize_search_item(item))
    return Response({
        'count': len(payload),
        'results': payload,
        'host': 'hotels.revnext.in',
        'product': 'aggregator',
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def public_listing_detail(request, slug):
    listing = get_object_or_404(
        AggregatorListing.objects.select_related('property', 'tenant'),
        slug=slug, status='PUBLISHED',
    )
    if not has_product(listing.tenant, 'aggregator'):
        return Response({'error': 'product_entitlement_required', 'product': 'aggregator'}, status=402)

    item = {
        'listing': listing,
        'available': True,
        'from_price': listing.min_price_hint,
        'nights': None,
    }
    check_in = request.query_params.get('check_in')
    check_out = request.query_params.get('check_out')
    if check_in and check_out:
        from datetime import date
        try:
            ci = date.fromisoformat(check_in)
            co = date.fromisoformat(check_out)
            for f in search_listings(city=listing.city, check_in=ci, check_out=co):
                if f['listing'].id == listing.id:
                    item = f
                    break
        except ValueError:
            pass
    return Response(_serialize_search_item(item))


@api_view(['POST'])
@permission_classes([AllowAny])
def public_submit_claim(request):
    ser = PublicClaimSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    listing = get_object_or_404(AggregatorListing, slug=data['listing_slug'], status='PUBLISHED')
    if not listing.is_claimable:
        return Response({'error': 'Listing is not open for claims'}, status=400)
    claim = ListingClaim.objects.create(
        listing=listing,
        contact_email=data['contact_email'],
        contact_name=data['contact_name'],
        company_name=data.get('company_name') or '',
        evidence_url=data.get('evidence_url') or '',
        evidence_notes=data.get('evidence_notes') or '',
        claimant_user=request.user if request.user.is_authenticated else None,
        claimant_tenant=getattr(request.user, 'tenant', None) if request.user.is_authenticated else None,
    )
    return Response({
        'id': claim.id,
        'status': claim.status,
        'message': 'Claim submitted for review',
        'verification_token': claim.verification_token,
    }, status=201)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_cities(request):
    cities = (
        AggregatorListing.objects.filter(status='PUBLISHED')
        .exclude(city='')
        .values_list('city', flat=True)
        .distinct()
        .order_by('city')
    )
    return Response({'cities': list(cities)})
