"""
Report views for tenants
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import HttpResponse, FileResponse
from django.conf import settings
import os

from reports.models import ReportTemplate, GeneratedReport, ScheduledReport
from reports.generators import (
    generate_revenue_report,
    generate_occupancy_report,
    generate_bookings_report,
    generate_channel_performance_report,
)


@login_required
def tenant_reports_list(request):
    """List all generated reports for the tenant"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    # Get all generated reports for this tenant
    reports = GeneratedReport.objects.filter(tenant=tenant).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    # Filter by report type if provided
    report_type_filter = request.GET.get('report_type')
    if report_type_filter:
        reports = reports.filter(report_type=report_type_filter)
    
    context = {
        'tenant': tenant,
        'user': user,
        'reports': reports,
        'status_filter': status_filter,
        'report_type_filter': report_type_filter,
    }
    
    return render(request, 'reports/report_list.html', context)


@login_required
def tenant_report_create(request):
    """Create/generate a new report"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    # Get available report templates
    templates = ReportTemplate.objects.filter(is_active=True, is_public=True)
    
    if request.method == 'POST':
        template_id = request.POST.get('template')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        report_format = request.POST.get('format', 'pdf')
        
        if not template_id or not start_date or not end_date:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('tenants:report_create')
        
        template = get_object_or_404(ReportTemplate, id=template_id, is_active=True)
        
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('tenants:report_create')
        
        # Create GeneratedReport record
        generated_report = GeneratedReport.objects.create(
            tenant=tenant,
            template=template,
            report_type=template.report_type,
            format=report_format,
            date_range_start=start_date_obj,
            date_range_end=end_date_obj,
            status='generating',
            generated_by=user,
        )
        
        try:
            # Generate report based on type
            buffer = None
            if template.report_type == 'revenue':
                buffer = generate_revenue_report(tenant, start_date_obj, end_date_obj, report_format)
            elif template.report_type == 'occupancy':
                buffer = generate_occupancy_report(tenant, start_date_obj, end_date_obj, report_format)
            elif template.report_type == 'bookings':
                buffer = generate_bookings_report(tenant, start_date_obj, end_date_obj, report_format)
            elif template.report_type == 'channel_performance':
                buffer = generate_channel_performance_report(tenant, start_date_obj, end_date_obj, report_format)
            else:
                raise ValueError(f"Unsupported report type: {template.report_type}")
            
            if buffer is None:
                raise Exception("Report generation failed or returned no content.")
            
            # Save file
            file_name = f"{template.report_type}_{tenant.slug}_{start_date_obj}_{end_date_obj}.{report_format}"
            relative_file_path = os.path.join('reports', file_name)
            absolute_file_path = os.path.join(settings.MEDIA_ROOT, relative_file_path)
            os.makedirs(os.path.dirname(absolute_file_path), exist_ok=True)
            
            with open(absolute_file_path, 'wb') as f:
                f.write(buffer.read())
            
            # Update GeneratedReport
            generated_report.status = 'completed'
            generated_report.file_path = relative_file_path
            generated_report.file_size = os.path.getsize(absolute_file_path)
            generated_report.generated_at = timezone.now()
            generated_report.expires_at = timezone.now() + timedelta(days=30)
            generated_report.save()
            
            messages.success(request, f'Report "{template.name}" generated successfully!')
            return redirect('tenants:report_detail', report_id=generated_report.id)
            
        except Exception as e:
            generated_report.status = 'failed'
            generated_report.error_message = str(e)
            generated_report.save()
            messages.error(request, f'Error generating report: {str(e)}')
            return redirect('tenants:report_create')
    
    # Default date range (last 30 days)
    today = timezone.now().date()
    default_start = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    default_end = today.strftime('%Y-%m-%d')
    
    context = {
        'tenant': tenant,
        'user': user,
        'templates': templates,
        'default_start': default_start,
        'default_end': default_end,
    }
    
    return render(request, 'reports/report_create.html', context)


@login_required
def tenant_report_detail(request, report_id):
    """View details of a generated report"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    report = get_object_or_404(GeneratedReport, id=report_id, tenant=tenant)
    
    # Check if file exists
    file_exists = False
    file_size_mb = 0
    if report.file_path:
        absolute_path = os.path.join(settings.MEDIA_ROOT, report.file_path)
        if os.path.exists(absolute_path):
            file_exists = True
            file_size_mb = round(report.file_size / (1024 * 1024), 2) if report.file_size else 0
    
    context = {
        'tenant': tenant,
        'user': user,
        'report': report,
        'file_exists': file_exists,
        'file_size_mb': file_size_mb,
    }
    
    return render(request, 'reports/report_detail.html', context)


@login_required
def tenant_report_download(request, report_id):
    """Download a generated report"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    report = get_object_or_404(GeneratedReport, id=report_id, tenant=tenant)
    
    if not report.file_path or report.status != 'completed':
        messages.error(request, 'Report file not available for download.')
        return redirect('tenants:report_detail', report_id=report_id)
    
    # Convert relative path to absolute
    absolute_path = os.path.join(settings.MEDIA_ROOT, report.file_path)
    
    if not os.path.exists(absolute_path):
        messages.error(request, 'Report file not found.')
        return redirect('tenants:report_detail', report_id=report_id)
    
    # Get content type
    content_types = {
        'pdf': 'application/pdf',
        'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv',
    }
    content_type = content_types.get(report.format, 'application/octet-stream')
    
    file_name = os.path.basename(report.file_path)
    response = FileResponse(open(absolute_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response
