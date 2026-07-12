from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CancelSubscriptionView,
    CatalogBootstrapView,
    MyEntitlementsView,
    MyInvoicesViewSet,
    MySubscriptionsViewSet,
    ProductPlanViewSet,
    ProductViewSet,
    SubscribeView,
)
from .billing.views import (
    BillingGatewaysView,
    CheckoutView,
    PayUReturnView,
    PreferGatewayView,
    RazorpayWebhookView,
    VerifyPaymentView,
)

router = DefaultRouter()
router.register(r'catalog', ProductViewSet, basename='product')
router.register(r'plans', ProductPlanViewSet, basename='product-plan')
router.register(r'my/subscriptions', MySubscriptionsViewSet, basename='my-product-sub')
router.register(r'my/invoices', MyInvoicesViewSet, basename='my-product-invoice')

urlpatterns = [
    path('bootstrap/', CatalogBootstrapView.as_view(), name='products-bootstrap'),
    path('entitlements/', MyEntitlementsView.as_view(), name='products-entitlements'),
    path('subscribe/', SubscribeView.as_view(), name='products-subscribe'),
    path(
        'subscriptions/<int:pk>/cancel/',
        CancelSubscriptionView.as_view(),
        name='products-cancel',
    ),
    # SaaS billing (Razorpay / PayU)
    path('billing/gateways/', BillingGatewaysView.as_view(), name='billing-gateways'),
    path('billing/prefer/', PreferGatewayView.as_view(), name='billing-prefer'),
    path('billing/checkout/', CheckoutView.as_view(), name='billing-checkout'),
    path('billing/verify/', VerifyPaymentView.as_view(), name='billing-verify'),
    path('billing/webhook/razorpay/', RazorpayWebhookView.as_view(), name='billing-webhook-razorpay'),
    path('billing/payu/return/', PayUReturnView.as_view(), name='billing-payu-return'),
    path('', include(router.urls)),
]
