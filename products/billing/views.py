"""
SaaS billing checkout APIs — Razorpay / PayU (one active preferred gateway).
"""
import json
import logging

from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.permissions import IsTenantOwner

from products.models import ProductInvoice
from products.serializers import ProductInvoiceSerializer, TenantProductSubscriptionSerializer
from products.services import subscribe
from products.models import ProductPlan

from .registry import (
    GATEWAY_PAYU,
    GATEWAY_RAZORPAY,
    get_available_gateways,
    get_preferred_gateway_code,
    set_preferred_gateway,
)
from .services import (
    BillingError,
    create_invoice_checkout,
    find_invoice_for_payu_txn,
    find_invoice_for_razorpay_order,
    verify_and_settle,
)

logger = logging.getLogger(__name__)


class BillingGatewaysView(APIView):
    """List Razorpay / PayU availability and which one is preferred."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'preferred': get_preferred_gateway_code(),
            'gateways': get_available_gateways(),
            'note': 'Set BILLING_GATEWAY=razorpay|payu (or Constance) to choose one over the other.',
        })


class PreferGatewayView(APIView):
    """
    Switch the platform preferred SaaS gateway (Razorpay XOR PayU).

    Superuser only — persists via Constance BILLING_GATEWAY.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        code = (request.data.get('gateway') or '').strip().lower()
        if code not in (GATEWAY_RAZORPAY, GATEWAY_PAYU):
            return Response(
                {'detail': 'gateway must be "razorpay" or "payu"'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        set_preferred_gateway(code)
        return Response({
            'preferred': get_preferred_gateway_code(),
            'gateways': get_available_gateways(),
        })


class CheckoutView(APIView):
    """
    Start checkout for a pending ProductInvoice.

    POST {
      "invoice_id": 12,
      "gateway": "razorpay" | "payu"   // optional one-shot override
    }

    Or combine subscribe + checkout:
    POST {
      "plan_code": "pms_pro",
      "billing_cycle": "monthly",
      "gateway": "payu"
    }
    """
    permission_classes = [IsAuthenticated, IsTenantOwner]

    def post(self, request):
        tenant = request.user.tenant
        if not tenant:
            return Response({'detail': 'No tenant'}, status=status.HTTP_400_BAD_REQUEST)

        gateway_code = (request.data.get('gateway') or '').strip().lower() or None
        invoice_id = request.data.get('invoice_id')
        plan_code = request.data.get('plan_code')

        invoice = None
        subscription = None

        if invoice_id:
            try:
                invoice = ProductInvoice.objects.select_related(
                    'subscription', 'plan', 'tenant'
                ).get(pk=invoice_id, tenant=tenant)
            except ProductInvoice.DoesNotExist:
                return Response({'detail': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
            subscription = invoice.subscription
        elif plan_code:
            try:
                plan = ProductPlan.objects.get(code=plan_code, is_active=True)
            except ProductPlan.DoesNotExist:
                return Response({'detail': 'Unknown plan_code'}, status=status.HTTP_404_NOT_FOUND)
            billing_cycle = request.data.get('billing_cycle', 'monthly')
            subscription, invoice = subscribe(
                tenant, plan, billing_cycle=billing_cycle, actor=request.user,
            )
        else:
            return Response(
                {'detail': 'Provide invoice_id or plan_code'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer = {
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email or tenant.email,
            'phone': getattr(request.user, 'phone', '') or tenant.phone or '',
        }
        callback_url = request.data.get('callback_url', '')

        try:
            session = create_invoice_checkout(
                invoice,
                gateway_code=gateway_code,
                customer=customer,
                callback_url=callback_url,
            )
        except (BillingError, RuntimeError, ValueError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'invoice': ProductInvoiceSerializer(invoice).data,
            'subscription': TenantProductSubscriptionSerializer(subscription).data if subscription else None,
            'checkout': {
                'gateway': session.gateway,
                'amount': str(session.amount),
                'currency': session.currency,
                'gateway_order_id': session.gateway_order_id,
                'payload': session.payload,
            },
        })


class VerifyPaymentView(APIView):
    """
    Client-side payment verification after Checkout.js / PayU redirect.

    Razorpay body:
      { "invoice_id": 1, "razorpay_order_id": "...", "razorpay_payment_id": "...", "razorpay_signature": "..." }

    PayU body: full callback field map + invoice_id (or udf1).
    """
    permission_classes = [IsAuthenticated, IsTenantOwner]

    def post(self, request):
        invoice_id = request.data.get('invoice_id') or request.data.get('udf1')
        if not invoice_id:
            return Response({'detail': 'invoice_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            invoice = ProductInvoice.objects.select_related(
                'subscription', 'plan', 'tenant'
            ).get(pk=invoice_id, tenant=request.user.tenant)
        except ProductInvoice.DoesNotExist:
            return Response({'detail': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

        gateway_code = request.data.get('gateway') or invoice.payment_gateway or None
        invoice, result = verify_and_settle(invoice, dict(request.data), gateway_code=gateway_code)
        if not result.success:
            return Response({
                'paid': False,
                'error': result.error,
                'invoice': ProductInvoiceSerializer(invoice).data,
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'paid': True,
            'invoice': ProductInvoiceSerializer(invoice).data,
            'subscription': TenantProductSubscriptionSerializer(invoice.subscription).data
            if invoice.subscription_id else None,
        })


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        from .razorpay_gateway import RazorpayGateway

        gw = RazorpayGateway()
        signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')
        body = request.body
        if gw.webhook_secret and not gw.verify_webhook_signature(body, signature):
            return Response({'detail': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            return Response({'detail': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        event = payload.get('event', '')
        if event not in ('payment.captured', 'order.paid'):
            return Response({'ok': True, 'ignored': event})

        entity = (
            payload.get('payload', {}).get('payment', {}).get('entity')
            or payload.get('payload', {}).get('order', {}).get('entity')
            or {}
        )
        order_id = entity.get('order_id') or entity.get('id')
        payment_id = entity.get('id') if event == 'payment.captured' else entity.get('id', '')
        invoice = find_invoice_for_razorpay_order(order_id)
        if not invoice:
            notes = entity.get('notes') or {}
            inv_id = notes.get('invoice_id')
            if inv_id:
                invoice = ProductInvoice.objects.filter(pk=inv_id).first()
        if not invoice:
            logger.warning('Razorpay webhook: invoice not found for order %s', order_id)
            return Response({'ok': True, 'matched': False})

        if invoice.status == 'paid':
            return Response({'ok': True, 'already_paid': True})

        from .base import PaymentResult
        result = PaymentResult(
            success=True,
            gateway=GATEWAY_RAZORPAY,
            gateway_order_id=order_id or '',
            transaction_id=payment_id or order_id or '',
            payment_method='razorpay',
            raw=entity,
        )
        from .services import mark_invoice_paid
        mark_invoice_paid(invoice, result)
        return Response({'ok': True, 'invoice_id': invoice.id})


@method_decorator(csrf_exempt, name='dispatch')
class PayUReturnView(APIView):
    """PayU surl/furl — verifies hash and redirects to app billing result page."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        return self._handle(request)

    def get(self, request):
        return self._handle(request)

    def _handle(self, request):
        data = request.data if request.method == 'POST' else request.query_params
        data = dict(data)
        invoice = find_invoice_for_payu_txn(
            txnid=data.get('txnid', ''),
            invoice_id=data.get('udf1', ''),
        )
        site = getattr(
            __import__('django.conf', fromlist=['settings']).settings,
            'SITE_URL',
            'http://127.0.0.1:8000',
        ).rstrip('/')

        if not invoice:
            return HttpResponseRedirect(f'{site}/pricing/?billing=payu_mismatch')

        invoice, result = verify_and_settle(invoice, data, gateway_code=GATEWAY_PAYU)
        if result.success:
            return HttpResponseRedirect(
                f'{site}/tenants/dashboard/?billing=success&invoice={invoice.id}'
            )
        return HttpResponseRedirect(
            f'{site}/pricing/?billing=failed&invoice={invoice.id}'
        )
