"""
Reports Models for Channel Manager
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from tenants.models import Tenant
from core.models import Property


class ReportTemplate(models.Model):
    """Predefined report templates"""
    
    REPORT_TYPES = [
        ('revenue', 'Revenue Report'),
        ('occupancy', 'Occupancy Report'),
        ('bookings', 'Bookings Report'),
        ('channel_performance', 'Channel Performance Report'),
        ('inventory', 'Inventory Report'),
        ('custom', 'Custom Report'),
    ]
    
    FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Template configuration
    format = models.CharField(max_length=10, choices=FORMATS, default='pdf')
    fields = models.JSONField(
        default=list,
        help_text="List of fields to include in the report"
    )
    filters = models.JSONField(
        default=dict,
        help_text="Default filters for the report"
    )
    
    # Scheduling
    can_schedule = models.BooleanField(default=True)
    default_schedule = models.CharField(
        max_length=50,
        blank=True,
        help_text="Cron expression for default schedule"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True, help_text="Available to all tenants")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'report_templates'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class GeneratedReport(models.Model):
    """Generated report instances"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='reports',
        null=True,
        blank=True
    )
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='generated_reports'
    )
    
    # Report parameters
    report_type = models.CharField(max_length=50)
    format = models.CharField(max_length=10)
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    
    # Generation details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")
    error_message = models.TextField(blank=True)
    
    # Metadata
    generated_by = models.ForeignKey(
        'tenants.TenantUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports'
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Report file expiration date")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'generated_reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['report_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.template.name} - {self.get_status_display()} ({self.created_at.strftime('%Y-%m-%d')})"


class ScheduledReport(models.Model):
    """Scheduled report generation"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='scheduled_reports'
    )
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='scheduled_reports'
    )
    
    # Schedule configuration
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    cron_expression = models.CharField(
        max_length=100,
        blank=True,
        help_text="Cron expression for custom frequency"
    )
    next_run_at = models.DateTimeField(null=True, blank=True)
    
    # Report parameters
    default_filters = models.JSONField(default=dict, blank=True)
    recipients = models.JSONField(
        default=list,
        help_text="List of email addresses to send report to"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_run_status = models.CharField(max_length=20, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        'tenants.TenantUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'scheduled_reports'
        ordering = ['next_run_at']
        unique_together = ['tenant', 'template', 'frequency']
    
    def __str__(self):
        return f"{self.template.name} - {self.get_frequency_display()} ({self.tenant.name})"
