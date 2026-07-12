from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from tenants.permissions import IsTenantMember
from core.mobile_api import property_tenant_qs

from .models import PropertyWebsite, SiteTemplate
from .serializers import PropertyWebsiteSerializer, SiteTemplateSerializer


class SiteTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SiteTemplateSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    queryset = SiteTemplate.objects.filter(is_active=True)
    ordering = ['name']


class PropertyWebsiteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PropertyWebsiteSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['property', 'is_published']

    def get_queryset(self):
        qs = PropertyWebsite.objects.select_related('property', 'template')
        return property_tenant_qs(qs, self.request.user)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        site = self.get_object()
        site.is_published = True
        site.published_at = timezone.now()
        site.save(update_fields=['is_published', 'published_at', 'updated_at'])
        return Response(PropertyWebsiteSerializer(site).data)

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        site = self.get_object()
        site.is_published = False
        site.save(update_fields=['is_published', 'updated_at'])
        return Response(PropertyWebsiteSerializer(site).data)
