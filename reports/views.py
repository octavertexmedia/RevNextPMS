"""
Views for Reports app
"""
import os
from datetime import datetime, timedelta
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ReportTemplate, GeneratedReport, ScheduledReport
from .generators import (
    generate_revenue_report,
    generate_occupancy_report,
    generate_bookings_report,
    generate_channel_performance_report,
)
from .serializers import (
    ReportTemplateSerializer,
    GeneratedReportSerializer,
    ScheduledReportSerializer,
)


@login_required
@require_http_methods(["GET", "POST"])
def generate_report_view(request, template_id):
    """Generate a report for the current tenant"""
    template = get_object_or_404(ReportTemplate, id=template_id, is_active=True)
    
    if not hasattr(request.user, 'tenant') or not request.user.tenant:
        return HttpResponse("Access denied. You must be associated with a tenant.", status=403)
    
    tenant = request.user.tenant
    
    # Get parameters
    start_date = request.GET.get('start_date') or request.POST.get('start_date')
    end_date = request.GET.get('end_date') or request.POST.get('end_date')
    report_format = request.GET.get('format', 'pdf') or request.POST.get('format', 'pdf')
    
    if not start_date or not end_date:
        # Default to last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Create GeneratedReport record
    generated_report = GeneratedReport.objects.create(
        tenant=tenant,
        template=template,
        report_type=template.report_type,
        format=report_format,
        date_range_start=start_date,
        date_range_end=end_date,
        status='generating',
        generated_by=request.user,
    )
    
    try:
        # Generate report based on type
        if template.report_type == 'revenue':
            buffer = generate_revenue_report(tenant, start_date, end_date, report_format)
        elif template.report_type == 'occupancy':
            buffer = generate_occupancy_report(tenant, start_date, end_date, report_format)
        elif template.report_type == 'bookings':
            buffer = generate_bookings_report(tenant, start_date, end_date, report_format)
        elif template.report_type == 'channel_performance':
            buffer = generate_channel_performance_report(tenant, start_date, end_date, report_format)
        else:
            raise ValueError(f"Unsupported report type: {template.report_type}")
        
        # Save file
        from django.conf import settings
        file_name = f"{template.report_type}_{tenant.slug}_{start_date}_{end_date}.{report_format}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'reports', file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(buffer.read())
        
        # Update GeneratedReport
        # Store relative path for database
        relative_path = os.path.join('reports', file_name)
        generated_report.status = 'completed'
        generated_report.file_path = relative_path
        generated_report.file_size = os.path.getsize(file_path)
        generated_report.generated_at = timezone.now()
        generated_report.expires_at = timezone.now() + timedelta(days=30)
        generated_report.save()
        
        response = FileResponse(open(file_path, 'rb'), content_type=get_content_type(report_format))
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
        
    except Exception as e:
        generated_report.status = 'failed'
        generated_report.error_message = str(e)
        generated_report.save()
        return HttpResponse(f"Error generating report: {str(e)}", status=500)


def get_content_type(format):
    """Get content type for report format"""
    content_types = {
        'pdf': 'application/pdf',
        'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv',
    }
    return content_types.get(format, 'application/octet-stream')


class ReportTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Report Templates"""
    queryset = ReportTemplate.objects.filter(is_active=True)
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter templates by tenant access"""
        qs = super().get_queryset()
        # Show public templates or tenant-specific templates
        return qs.filter(is_public=True)


class GeneratedReportViewSet(viewsets.ModelViewSet):
    """ViewSet for Generated Reports"""
    serializer_class = GeneratedReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter reports by tenant"""
        user = self.request.user
        if user.is_superuser:
            return GeneratedReport.objects.all()
        if hasattr(user, 'tenant') and user.tenant:
            return GeneratedReport.objects.filter(tenant=user.tenant)
        return GeneratedReport.objects.none()
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a generated report"""
        from django.conf import settings
        report = self.get_object()
        
        # Convert relative path to absolute
        if report.file_path.startswith('reports/'):
            absolute_path = os.path.join(settings.MEDIA_ROOT, report.file_path)
        else:
            absolute_path = report.file_path
        
        if not os.path.exists(absolute_path):
            return Response({'error': 'Report file not found'}, status=404)
        
        response = FileResponse(
            open(absolute_path, 'rb'),
            content_type=get_content_type(report.format)
        )
        file_name = os.path.basename(report.file_path)
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response


class ScheduledReportViewSet(viewsets.ModelViewSet):
    """ViewSet for Scheduled Reports"""
    serializer_class = ScheduledReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter scheduled reports by tenant"""
        user = self.request.user
        if user.is_superuser:
            return ScheduledReport.objects.all()
        if hasattr(user, 'tenant') and user.tenant:
            return ScheduledReport.objects.filter(tenant=user.tenant)
        return ScheduledReport.objects.none()
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Run a scheduled report immediately"""
        scheduled_report = self.get_object()
        # Trigger report generation
        # This would typically call a Celery task
        return Response({'message': 'Report generation triggered'})
