"""
Serializers for Reports app
"""
from rest_framework import serializers
from .models import ReportTemplate, GeneratedReport, ScheduledReport


class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'report_type', 'description', 'format',
            'fields', 'filters', 'can_schedule', 'default_schedule',
            'is_active', 'is_public', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GeneratedReportSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = GeneratedReport
        fields = [
            'id', 'tenant', 'tenant_name', 'template', 'template_name',
            'report_type', 'format', 'date_range_start', 'date_range_end',
            'filters', 'status', 'file_path', 'file_size', 'error_message',
            'generated_by', 'generated_at', 'expires_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'file_path', 'file_size', 'error_message',
            'generated_at', 'created_at', 'updated_at',
        ]


class ScheduledReportSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = ScheduledReport
        fields = [
            'id', 'tenant', 'tenant_name', 'template', 'template_name',
            'frequency', 'cron_expression', 'next_run_at', 'default_filters',
            'recipients', 'is_active', 'last_run_at', 'last_run_status',
            'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'last_run_at', 'last_run_status', 'created_at', 'updated_at',
        ]
