from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from tenants.permissions import IsTenantMember
from core.mobile_api import property_tenant_qs
from core.models import RoomType, RatePlan

from .models import HotelAdsConfig, FeedSubmission
from .serializers import HotelAdsConfigSerializer, FeedSubmissionSerializer


class HotelAdsConfigViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HotelAdsConfigSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['property', 'is_enabled']

    def get_queryset(self):
        qs = HotelAdsConfig.objects.select_related('property')
        return property_tenant_qs(qs, self.request.user)

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        config = self.get_object()
        enabled = request.data.get('is_enabled')
        if enabled is None:
            config.is_enabled = not config.is_enabled
        else:
            config.is_enabled = bool(enabled)
        config.save(update_fields=['is_enabled', 'updated_at'])
        return Response(HotelAdsConfigSerializer(config).data)

    @action(detail=True, methods=['post'])
    def submit_feed(self, request, pk=None):
        config = self.get_object()
        prop = config.property
        rooms_count = RoomType.objects.filter(property=prop, is_active=True).count()
        rates_count = RatePlan.objects.filter(property=prop, is_active=True).count()
        feed = FeedSubmission.objects.create(
            property=prop,
            status='SUBMITTED',
            rooms_count=rooms_count,
            rates_count=rates_count,
            response_data={'source': 'mobile_api'},
        )
        config.last_feed_submitted = timezone.now()
        config.feed_status = 'SUBMITTED'
        config.save(update_fields=['last_feed_submitted', 'feed_status', 'updated_at'])
        return Response({
            'config': HotelAdsConfigSerializer(config).data,
            'feed': FeedSubmissionSerializer(feed).data,
        }, status=status.HTTP_201_CREATED)
