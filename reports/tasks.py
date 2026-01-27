"""
Celery tasks for report generation
"""
from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .models import ScheduledReport, GeneratedReport, ReportTemplate
from .generators import (
    generate_revenue_report,
    generate_occupancy_report,
    generate_bookings_report,
    generate_channel_performance_report,
)

logger = logging.getLogger(__name__)


@shared_task
def generate_scheduled_reports():
    """Generate all scheduled reports that are due"""
    now = timezone.now()
    due_reports = ScheduledReport.objects.filter(
        is_active=True,
        next_run_at__lte=now
    )
    
    for scheduled_report in due_reports:
        try:
            generate_report_from_schedule.delay(scheduled_report.id)
        except Exception as e:
            logger.error(f"Error scheduling report {scheduled_report.id}: {e}", exc_info=True)


@shared_task
def generate_report_from_schedule(scheduled_report_id):
    """Generate a report from a scheduled report configuration"""
    try:
        scheduled_report = ScheduledReport.objects.get(id=scheduled_report_id)
        tenant = scheduled_report.tenant
        template = scheduled_report.template
        
        # Calculate date range based on frequency
        end_date = datetime.now().date()
        if scheduled_report.frequency == 'daily':
            start_date = end_date - timedelta(days=1)
        elif scheduled_report.frequency == 'weekly':
            start_date = end_date - timedelta(days=7)
        elif scheduled_report.frequency == 'monthly':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Merge default filters
        filters = {**scheduled_report.default_filters}
        
        # Create GeneratedReport record
        generated_report = GeneratedReport.objects.create(
            tenant=tenant,
            template=template,
            report_type=template.report_type,
            format=template.format,
            date_range_start=start_date,
            date_range_end=end_date,
            filters=filters,
            status='generating',
        )
        
        try:
            # Generate report
            if template.report_type == 'revenue':
                buffer = generate_revenue_report(tenant, start_date, end_date, template.format)
            elif template.report_type == 'occupancy':
                buffer = generate_occupancy_report(tenant, start_date, end_date, template.format)
            elif template.report_type == 'bookings':
                buffer = generate_bookings_report(tenant, start_date, end_date, template.format)
            elif template.report_type == 'channel_performance':
                buffer = generate_channel_performance_report(tenant, start_date, end_date, template.format)
            else:
                raise ValueError(f"Unsupported report type: {template.report_type}")
            
            if buffer is None:
                raise ValueError("Report generation returned None")
            
            # Save file
            import os
            from django.conf import settings
            file_name = f"{template.report_type}_{tenant.slug}_{start_date}_{end_date}.{template.format}"
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
            
            # Update scheduled report
            scheduled_report.last_run_at = timezone.now()
            scheduled_report.last_run_status = 'completed'
            
            # Calculate next run
            if scheduled_report.frequency == 'daily':
                scheduled_report.next_run_at = timezone.now() + timedelta(days=1)
            elif scheduled_report.frequency == 'weekly':
                scheduled_report.next_run_at = timezone.now() + timedelta(days=7)
            elif scheduled_report.frequency == 'monthly':
                scheduled_report.next_run_at = timezone.now() + timedelta(days=30)
            
            scheduled_report.save()
            
            # Send email if recipients configured
            if scheduled_report.recipients:
                send_report_email.delay(generated_report.id, scheduled_report.recipients)
            
            logger.info(f"Successfully generated report {generated_report.id}")
            
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            generated_report.status = 'failed'
            generated_report.error_message = str(e)
            generated_report.save()
            
            scheduled_report.last_run_at = timezone.now()
            scheduled_report.last_run_status = 'failed'
            scheduled_report.save()
            
    except ScheduledReport.DoesNotExist:
        logger.error(f"Scheduled report {scheduled_report_id} not found")
    except Exception as e:
        logger.error(f"Unexpected error in generate_report_from_schedule: {e}", exc_info=True)


@shared_task
def send_report_email(report_id, recipients):
    """Send report via email to recipients"""
    try:
        # TODO: Implement email sending
        # For now, just log
        logger.info(f"Would send report {report_id} to {recipients}")
    except Exception as e:
        logger.error(f"Error sending report email: {e}", exc_info=True)


@shared_task
def cleanup_expired_reports():
    """Clean up expired report files"""
    try:
        from datetime import datetime
        expired_reports = GeneratedReport.objects.filter(
            expires_at__lt=timezone.now(),
            status='completed'
        )
        
        deleted_count = 0
        for report in expired_reports:
            try:
                import os
                from django.conf import settings
                # Convert relative path to absolute
                if report.file_path.startswith('reports/'):
                    absolute_path = os.path.join(settings.MEDIA_ROOT, report.file_path)
                else:
                    absolute_path = report.file_path
                
                if os.path.exists(absolute_path):
                    os.remove(absolute_path)
                report.delete()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting report {report.id}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} expired reports")
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_reports: {e}", exc_info=True)
