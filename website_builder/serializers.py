from rest_framework import serializers
from .models import PropertyWebsite, SiteTemplate


class SiteTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteTemplate
        fields = ['id', 'name', 'slug', 'description', 'thumbnail_url', 'is_active']
        read_only_fields = fields


class PropertyWebsiteSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True, allow_null=True)

    class Meta:
        model = PropertyWebsite
        fields = [
            'id', 'property', 'property_name', 'template', 'template_name',
            'meta_title', 'meta_description', 'custom_domain', 'subdomain',
            'ssl_enabled', 'is_published', 'published_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields
