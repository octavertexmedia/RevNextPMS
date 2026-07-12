"""
Token authentication endpoints for mobile / API clients.
"""
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import TenantUserSerializer

User = get_user_model()


class LoginView(APIView):
    """
    Obtain an auth token.

    Accepts username or email plus password.
    POST body: {"username": "...", "password": "..."}
    or {"email": "...", "password": "..."}
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        email = (request.data.get('email') or '').strip()
        password = request.data.get('password') or ''

        if not password or (not username and not email):
            return Response(
                {'detail': 'Provide username or email, and password.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not username and email:
            try:
                user_obj = User.objects.get(email__iexact=email)
                username = user_obj.get_username()
            except User.DoesNotExist:
                return Response(
                    {'detail': 'Invalid credentials.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {'detail': 'User account is disabled.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        token, _ = Token.objects.get_or_create(user=user)
        from rbac.access_payload import build_access_payload

        user_data = TenantUserSerializer(user).data
        user_data.update(build_access_payload(user))
        return Response({
            'token': token.key,
            'user': user_data,
        })


class LogoutView(APIView):
    """Invalidate the current user's auth token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)


class MeView(APIView):
    """Return the authenticated user profile plus RBAC + product entitlements."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from rbac.access_payload import build_access_payload
        from products.services import tenant_entitlements_summary

        data = TenantUserSerializer(request.user).data
        data.update(build_access_payload(request.user))
        if request.user.tenant_id:
            data['products'] = tenant_entitlements_summary(request.user.tenant)
        else:
            data['products'] = {'products': [], 'subscriptions': []}
        return Response(data)
