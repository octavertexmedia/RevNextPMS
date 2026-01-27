"""
Views for Integration Webhooks
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

from .models import IntegrationPlatform

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_handler(request, platform_name):
    """
    Generic webhook handler for platform notifications
    
    Args:
        request: Django request object
        platform_name: Name of the platform (e.g., 'booking.com', 'expedia')
    
    Returns:
        JSON response
    """
    try:
        platform = IntegrationPlatform.objects.get(name=platform_name, is_active=True)
        
        if not platform.supports_webhooks:
            return JsonResponse({'error': 'Webhooks not supported for this platform'}, status=400)
        
        # Parse payload
        try:
            if request.content_type == 'application/json':
                payload = json.loads(request.body)
            else:
                payload = request.POST.dict()
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        
        # Get adapter and handle webhook
        from integrations.tasks import get_adapter
        adapter = get_adapter(platform_name)
        
        if not adapter:
            return JsonResponse({'error': 'Adapter not found'}, status=500)
        
        # Process webhook asynchronously
        from integrations.tasks import process_webhook
        process_webhook.delay(platform_name, payload)
        
        # Return immediate acknowledgment
        return JsonResponse({'status': 'received', 'message': 'Webhook queued for processing'})
    
    except IntegrationPlatform.DoesNotExist:
        return JsonResponse({'error': 'Platform not found or inactive'}, status=404)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)

