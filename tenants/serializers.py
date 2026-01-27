"""
Serializers for Tenant API
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tenant, TenantUser, SubscriptionPlan, SubscriptionPayment

User = get_user_model()


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for Subscription Plans"""
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'display_name', 'description',
            'monthly_price', 'yearly_price',
            'max_properties', 'max_integrations_per_property',
            'max_users', 'max_api_calls_per_month',
            'features', 'is_active', 'is_visible',
        ]
        read_only_fields = ['id']


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant"""
    subscription_plan_detail = SubscriptionPlanSerializer(source='subscription_plan', read_only=True)
    property_count = serializers.IntegerField(read_only=True)
    user_count = serializers.IntegerField(read_only=True)
    is_subscription_active = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True, allow_null=True)
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'email', 'phone',
            'business_name', 'gstin', 'pan',
            'address', 'city', 'state', 'country', 'postal_code',
            'is_active', 'subscription_plan', 'subscription_plan_detail',
            'subscription_start_date', 'subscription_end_date',
            'subscription_status', 'trial_end_date',
            'payment_method', 'billing_cycle', 'auto_renew',
            'max_properties', 'max_integrations_per_property',
            'max_users', 'max_api_calls_per_month',
            'api_calls_this_month', 'api_calls_reset_date',
            'property_count', 'user_count',
            'is_subscription_active', 'days_until_expiry',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'slug', 'created_at', 'updated_at',
            'property_count', 'user_count',
            'is_subscription_active', 'days_until_expiry',
        ]


class TenantUserSerializer(serializers.ModelSerializer):
    """Serializer for Tenant Users"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    is_owner = serializers.BooleanField(read_only=True)
    is_manager = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = TenantUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'tenant', 'tenant_name',
            'avatar', 'timezone', 'language',
            'is_active', 'is_staff', 'is_superuser',
            'is_owner', 'is_manager',
            'last_login', 'date_joined', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'last_login', 'date_joined',
            'is_owner', 'is_manager', 'created_at', 'updated_at',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }
    
    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop('password', None)
        user = TenantUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user, handling password separately"""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    """Serializer for Subscription Payments"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    plan_name = serializers.CharField(source='subscription_plan.display_name', read_only=True)
    
    class Meta:
        model = SubscriptionPayment
        fields = [
            'id', 'tenant', 'tenant_name',
            'subscription_plan', 'plan_name',
            'amount', 'billing_cycle', 'payment_status',
            'transaction_id', 'payment_gateway', 'payment_method',
            'payment_date', 'period_start', 'period_end',
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
