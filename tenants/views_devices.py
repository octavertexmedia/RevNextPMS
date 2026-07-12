"""
Device registration API for mobile push notifications.
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.permissions import IsTenantMember

from .models import DeviceRegistration


class DeviceRegisterView(APIView):
    """
    Register or refresh an FCM/APNs device token.

    POST body: {
      "token": "...",
      "platform": "ios"|"android"|"web",
      "device_name": "optional"
    }
    """
    permission_classes = [IsAuthenticated, IsTenantMember]

    def post(self, request):
        token = (request.data.get('token') or '').strip()
        platform = (request.data.get('platform') or 'android').strip().lower()
        device_name = (request.data.get('device_name') or '').strip()[:100]

        if not token:
            return Response({'detail': 'token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if platform not in ('ios', 'android', 'web'):
            return Response(
                {'detail': 'platform must be ios, android, or web.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        tenant = getattr(user, 'tenant', None)
        device, created = DeviceRegistration.objects.update_or_create(
            token=token,
            defaults={
                'user': user,
                'tenant': tenant,
                'platform': platform,
                'device_name': device_name,
                'is_active': True,
                'last_seen_at': timezone.now(),
            },
        )
        return Response(
            {
                'id': device.id,
                'token': device.token,
                'platform': device.platform,
                'device_name': device.device_name,
                'is_active': device.is_active,
                'created': created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class DeviceUnregisterView(APIView):
    """Deactivate a device token. POST body: {"token": "..."}"""
    permission_classes = [IsAuthenticated, IsTenantMember]

    def post(self, request):
        token = (request.data.get('token') or '').strip()
        if not token:
            return Response({'detail': 'token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        updated = DeviceRegistration.objects.filter(
            token=token,
            user=request.user,
        ).update(is_active=False, updated_at=timezone.now())
        return Response({'deactivated': updated > 0})


class DeviceListView(APIView):
    """List active devices for the authenticated user."""
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        devices = DeviceRegistration.objects.filter(
            user=request.user,
            is_active=True,
        ).order_by('-updated_at')
        return Response([
            {
                'id': d.id,
                'platform': d.platform,
                'device_name': d.device_name,
                'token_preview': f'{d.token[:12]}…' if len(d.token) > 12 else d.token,
                'last_seen_at': d.last_seen_at,
                'updated_at': d.updated_at,
            }
            for d in devices
        ])
