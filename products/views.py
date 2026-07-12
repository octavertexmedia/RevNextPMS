from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.permissions import IsTenantMember, IsTenantOwner

from .models import Product, ProductInvoice, ProductPlan, TenantProductSubscription
from .serializers import (
    ProductInvoiceSerializer,
    ProductPlanSerializer,
    ProductSerializer,
    SubscribeSerializer,
    TenantProductSubscriptionSerializer,
)
from .services import (
    cancel_subscription,
    start_product_trial,
    subscribe,
    tenant_entitlements_summary,
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Public product catalog (hosts + positioning)."""
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    queryset = Product.objects.filter(is_active=True)
    lookup_field = 'code'
    filterset_fields = ['is_billable']


class ProductPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """Public plans — filter by ?product=pms or ?packages=1."""
    serializer_class = ProductPlanSerializer
    permission_classes = [AllowAny]
    lookup_field = 'code'

    def get_queryset(self):
        qs = ProductPlan.objects.filter(is_active=True, is_visible=True).select_related(
            'product'
        ).prefetch_related('package_products')
        product = self.request.query_params.get('product')
        if product:
            qs = qs.filter(product__code=product, is_package=False)
        if self.request.query_params.get('packages') in ('1', 'true', 'yes'):
            qs = qs.filter(is_package=True)
        return qs


class MyEntitlementsView(APIView):
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        return Response(tenant_entitlements_summary(request.user.tenant))


class MySubscriptionsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TenantProductSubscriptionSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return TenantProductSubscription.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('plan', 'product').prefetch_related('plan__package_products')


class MyInvoicesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductInvoiceSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return ProductInvoice.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('plan', 'subscription')


class SubscribeView(APIView):
    """
    Subscribe the current tenant to a product plan or the suite package.

    POST {
      "plan_code": "pms_pro" | "revnext_suite",
      "billing_cycle": "monthly" | "yearly",
      "start_trial": false,
      "mark_paid": false
    }
    """
    permission_classes = [IsAuthenticated, IsTenantOwner]

    def post(self, request):
        ser = SubscribeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        try:
            plan = ProductPlan.objects.get(code=data['plan_code'], is_active=True)
        except ProductPlan.DoesNotExist:
            return Response({'detail': 'Unknown plan_code'}, status=status.HTTP_404_NOT_FOUND)

        tenant = request.user.tenant
        if not tenant:
            return Response({'detail': 'No tenant'}, status=status.HTTP_400_BAD_REQUEST)

        # Only superusers may mark_paid without a real gateway
        mark_paid = data['mark_paid'] and request.user.is_superuser

        if data['start_trial']:
            sub = start_product_trial(tenant, plan)
            return Response(
                TenantProductSubscriptionSerializer(sub).data,
                status=status.HTTP_201_CREATED,
            )

        sub, invoice = subscribe(
            tenant,
            plan,
            billing_cycle=data['billing_cycle'],
            mark_paid=mark_paid,
            actor=request.user,
        )
        payload = {
            'subscription': TenantProductSubscriptionSerializer(sub).data,
            'invoice': ProductInvoiceSerializer(invoice).data,
            'payment_required': invoice.status == 'pending',
            'message': (
                'Subscription created. Complete payment to activate.'
                if invoice.status == 'pending'
                else 'Subscription active.'
            ),
        }

        if invoice.status == 'pending' and data.get('checkout', True):
            try:
                from products.billing.services import create_invoice_checkout
                customer = {
                    'name': request.user.get_full_name() or request.user.username,
                    'email': request.user.email or tenant.email,
                    'phone': getattr(request.user, 'phone', '') or tenant.phone or '',
                }
                session = create_invoice_checkout(
                    invoice,
                    gateway_code=data.get('gateway'),
                    customer=customer,
                )
                payload['checkout'] = {
                    'gateway': session.gateway,
                    'amount': str(session.amount),
                    'currency': session.currency,
                    'gateway_order_id': session.gateway_order_id,
                    'payload': session.payload,
                }
            except (RuntimeError, ValueError) as exc:
                payload['checkout_error'] = str(exc)

        return Response(payload, status=status.HTTP_201_CREATED)


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    def post(self, request, pk):
        try:
            sub = TenantProductSubscription.objects.get(pk=pk, tenant=request.user.tenant)
        except TenantProductSubscription.DoesNotExist:
            return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        at_period_end = request.data.get('at_period_end', True)
        cancel_subscription(sub, at_period_end=bool(at_period_end))
        return Response(TenantProductSubscriptionSerializer(sub).data)


class CatalogBootstrapView(APIView):
    """One-shot marketing/checkout payload for pricing pages & product hosts."""
    permission_classes = [AllowAny]

    def get(self, request):
        products = ProductSerializer(
            Product.objects.filter(is_active=True), many=True
        ).data
        plans = ProductPlanSerializer(
            ProductPlan.objects.filter(is_active=True, is_visible=True)
            .select_related('product')
            .prefetch_related('package_products'),
            many=True,
        ).data
        suite = next((p for p in plans if p.get('is_package')), None)
        from products.billing.registry import get_available_gateways, get_preferred_gateway_code
        return Response({
            'products': products,
            'plans': plans,
            'suite': suite,
            'hosts': {p['code']: p['primary_host'] for p in products},
            'billing_cycles': ['monthly', 'yearly'],
            'billing': {
                'preferred': get_preferred_gateway_code(),
                'gateways': get_available_gateways(),
            },
        })
