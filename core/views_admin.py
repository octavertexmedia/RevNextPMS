"""
Admin views for system monitoring and backup management
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
import os
import subprocess
from datetime import datetime, timedelta
import json

from .views import health_check


@staff_member_required
def admin_system_health(request):
    """System health monitoring dashboard for admins"""
    # Get health check data
    from django.db import connection
    import psutil
    
    health_data = {
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_data['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful',
            }
    except Exception as e:
        health_data['checks']['database'] = {
            'status': 'unhealthy',
            'message': str(e),
        }
    
    # Cache check
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        cache_result = cache.get('health_check')
        if cache_result == 'ok':
            health_data['checks']['cache'] = {
                'status': 'healthy',
                'message': 'Cache is operational',
            }
        else:
            health_data['checks']['cache'] = {
                'status': 'degraded',
                'message': 'Cache may not be working properly',
            }
    except Exception as e:
        health_data['checks']['cache'] = {
            'status': 'unavailable',
            'message': str(e),
        }
    
    # Disk space
    try:
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        health_data['checks']['disk'] = {
            'status': 'healthy' if disk_percent < 90 else 'warning',
            'usage_percent': round(disk_percent, 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'total_gb': round(disk.total / (1024**3), 2),
            'used_gb': round(disk.used / (1024**3), 2),
        }
    except Exception as e:
        health_data['checks']['disk'] = {
            'status': 'unknown',
            'message': str(e),
        }
    
    # Memory
    try:
        memory = psutil.virtual_memory()
        health_data['checks']['memory'] = {
            'status': 'healthy' if memory.percent < 90 else 'warning',
            'usage_percent': round(memory.percent, 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'total_gb': round(memory.total / (1024**3), 2),
            'used_gb': round((memory.total - memory.available) / (1024**3), 2),
        }
    except Exception as e:
        health_data['checks']['memory'] = {
            'status': 'unknown',
            'message': str(e),
        }
    
    # Celery workers
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            health_data['checks']['celery'] = {
                'status': 'healthy',
                'active_workers': len(active_workers),
                'worker_names': list(active_workers.keys()),
            }
        else:
            health_data['checks']['celery'] = {
                'status': 'warning',
                'message': 'No active workers found',
            }
    except Exception as e:
        health_data['checks']['celery'] = {
            'status': 'unknown',
            'message': str(e),
        }
    
    context = {
        'health_data': health_data,
    }
    
    return render(request, 'admin/system_health.html', context)


@staff_member_required
def admin_backup_management(request):
    """Backup management interface for admins"""
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    
    # List existing backups
    backups = []
    if os.path.exists(backup_dir):
        for filename in os.listdir(backup_dir):
            if filename.endswith('.sql'):
                file_path = os.path.join(backup_dir, filename)
                file_stat = os.stat(file_path)
                backups.append({
                    'filename': filename,
                    'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(file_stat.st_mtime),
                    'path': file_path,
                })
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
    
    # Trigger backup
    if request.method == 'POST' and request.POST.get('action') == 'create_backup':
        try:
            from django.core.management import call_command
            call_command('backup_database')
            messages.success(request, 'Backup created successfully!')
            return redirect('admin:backup_management')
        except Exception as e:
            messages.error(request, f'Error creating backup: {str(e)}')
    
    # Delete backup
    if request.method == 'POST' and request.POST.get('action') == 'delete_backup':
        filename = request.POST.get('filename')
        if filename:
            file_path = os.path.join(backup_dir, filename)
            if os.path.exists(file_path) and filename.endswith('.sql'):
                try:
                    os.remove(file_path)
                    messages.success(request, f'Backup {filename} deleted successfully!')
                    return redirect('admin:backup_management')
                except Exception as e:
                    messages.error(request, f'Error deleting backup: {str(e)}')
    
    # Calculate total backup size
    total_size_mb = sum(b['size_mb'] for b in backups)
    
    context = {
        'backups': backups,
        'backup_dir': backup_dir,
        'total_size_mb': round(total_size_mb, 2),
        'backup_count': len(backups),
    }
    
    return render(request, 'admin/backup_management.html', context)
