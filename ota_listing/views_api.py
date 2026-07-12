from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from tenants.permissions import IsTenantMember
from core.mobile_api import property_tenant_qs

from .models import ListingProject
from .serializers import ListingProjectSerializer


class ListingProjectViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ListingProjectSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['property', 'status', 'platform']
    ordering = ['-updated_at']

    def get_queryset(self):
        qs = ListingProject.objects.select_related('property', 'platform')
        return property_tenant_qs(qs, self.request.user)

    @action(detail=True, methods=['post'])
    def set_status(self, request, pk=None):
        project = self.get_object()
        new_status = request.data.get('status')
        valid = [c[0] for c in ListingProject.STATUS]
        if new_status not in valid:
            return Response(
                {'detail': f'Invalid status. Choose from: {", ".join(valid)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        project.status = new_status
        update_fields = ['status', 'updated_at']
        if new_status in ('LIVE', 'OPTIMIZED'):
            project.completed_at = timezone.now()
            update_fields.append('completed_at')
        project.save(update_fields=update_fields)
        return Response(ListingProjectSerializer(project).data)
