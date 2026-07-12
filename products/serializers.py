from rest_framework import serializers

from .models import Product, ProductInvoice, ProductPlan, TenantProductSubscription


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'code', 'name', 'short_name', 'tagline', 'description',
            'subdomain', 'primary_host', 'path_prefixes', 'api_prefixes',
            'app_label', 'is_active', 'is_billable', 'sort_order', 'marketing_url',
        ]


class ProductPlanSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True, default=None)
    package_product_codes = serializers.SerializerMethodField()
    monthly_price_amount = serializers.SerializerMethodField()
    yearly_price_amount = serializers.SerializerMethodField()

    class Meta:
        model = ProductPlan
        fields = [
            'id', 'code', 'display_name', 'description', 'tier',
            'product', 'product_code', 'is_package', 'package_product_codes',
            'monthly_price', 'yearly_price', 'monthly_price_amount', 'yearly_price_amount',
            'limits', 'features', 'trial_days', 'is_active', 'is_visible', 'sort_order',
        ]

    def get_package_product_codes(self, obj):
        if not obj.is_package:
            return []
        return list(obj.package_products.values_list('code', flat=True))

    def get_monthly_price_amount(self, obj):
        return float(obj.monthly_price.amount) if obj.monthly_price else 0

    def get_yearly_price_amount(self, obj):
        return float(obj.yearly_price.amount) if obj.yearly_price else 0


class TenantProductSubscriptionSerializer(serializers.ModelSerializer):
    plan_detail = ProductPlanSerializer(source='plan', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True, default=None)
    entitles = serializers.SerializerMethodField()
    is_active_now = serializers.BooleanField(read_only=True)

    class Meta:
        model = TenantProductSubscription
        fields = [
            'id', 'tenant', 'plan', 'plan_detail', 'product', 'product_code',
            'status', 'billing_cycle', 'auto_renew',
            'trial_end_date', 'starts_at', 'ends_at',
            'limits_snapshot', 'features_snapshot',
            'entitles', 'is_active_now', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_entitles(self, obj):
        return obj.entitled_product_codes()


class ProductInvoiceSerializer(serializers.ModelSerializer):
    plan_code = serializers.CharField(source='plan.code', read_only=True)
    amount_value = serializers.SerializerMethodField()

    class Meta:
        model = ProductInvoice
        fields = [
            'id', 'tenant', 'subscription', 'plan', 'plan_code',
            'amount', 'amount_value', 'billing_cycle', 'status',
            'period_start', 'period_end', 'transaction_id',
            'payment_gateway', 'payment_method', 'paid_at', 'created_at',
        ]
        read_only_fields = fields

    def get_amount_value(self, obj):
        return float(obj.amount.amount) if obj.amount else 0


class SubscribeSerializer(serializers.Serializer):
    plan_code = serializers.SlugField()
    billing_cycle = serializers.ChoiceField(choices=['monthly', 'yearly'], default='monthly')
    start_trial = serializers.BooleanField(default=False)
    mark_paid = serializers.BooleanField(
        default=False,
        help_text='Admin/offline only — completes invoice immediately',
    )
    gateway = serializers.ChoiceField(
        choices=['razorpay', 'payu'],
        required=False,
        allow_null=True,
        help_text='Optional one-shot gateway override for checkout',
    )
    checkout = serializers.BooleanField(
        default=True,
        help_text='If true and payment required, create gateway checkout session',
    )
