"""
Admin configuration for Reports app
"""
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import ReportTemplate, GeneratedReport, ScheduledReport


@admin.register(ReportTemplate)
class ReportTemplateAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'report_type', 'format', 'is_active', 'is_public', 'created_at']
    list_filter = ['report_type', 'format', 'is_active', 'is_public']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'report_type', 'description', 'format')
        }),
        ('Configuration', {
            'fields': ('fields', 'filters')
        }),
        ('Scheduling', {
            'fields': ('can_schedule', 'default_schedule')
        }),
        ('Status', {
            'fields': ('is_active', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GeneratedReport)
class GeneratedReportAdmin(SimpleHistoryAdmin):
    list_display = ['template', 'tenant', 'report_type', 'format', 'status', 'generated_at', 'created_at']
    list_filter = ['status', 'report_type', 'format', 'generated_at']
    search_fields = ['template__name', 'tenant__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'generated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'template', 'report_type', 'format')
        }),
        ('Parameters', {
            'fields': ('date_range_start', 'date_range_end', 'filters')
        }),
        ('Generation Details', {
            'fields': ('status', 'file_path', 'file_size', 'error_message', 'generated_by', 'generated_at', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ScheduledReport)
class ScheduledReportAdmin(SimpleHistoryAdmin):
    list_display = ['template', 'tenant', 'frequency', 'is_active', 'next_run_at', 'last_run_at', 'last_run_status']
    list_filter = ['frequency', 'is_active', 'last_run_status']
    search_fields = ['template__name', 'tenant__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_run_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'template', 'created_by')
        }),
        ('Schedule Configuration', {
            'fields': ('frequency', 'cron_expression', 'next_run_at')
        }),
        ('Report Parameters', {
            'fields': ('default_filters', 'recipients')
        }),
        ('Status', {
            'fields': ('is_active', 'last_run_at', 'last_run_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
