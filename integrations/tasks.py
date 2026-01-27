"""
Celery Tasks for Integration Synchronization
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from integrations.models import IntegrationPlatform, PropertyIntegration, SyncLog
from integrations.adapters import BookingComAdapter, ExpediaAdapter, AgodaAdapter

logger = logging.getLogger(__name__)


# Adapter mapping
ADAPTER_MAP = {
    'booking.com': BookingComAdapter,
    'expedia': ExpediaAdapter,
    'agoda': AgodaAdapter,
    # Add more adapters as they are implemented
}


def get_adapter(platform_name: str, property_integration=None):
    """Get the appropriate adapter for a platform"""
    adapter_class = ADAPTER_MAP.get(platform_name.lower())
    if not adapter_class:
        logger.warning(f"No adapter found for platform: {platform_name}")
        return None
    
    platform = IntegrationPlatform.objects.filter(name=platform_name).first()
    if not platform:
        logger.warning(f"Platform not found: {platform_name}")
        return None
    
    return adapter_class(platform, property_integration)


@shared_task(bind=True, max_retries=3)
def sync_availability(self, property_integration_id: str):
    """Sync availability for a property integration"""
    try:
        property_integration = PropertyIntegration.objects.get(id=property_integration_id)
        
        if not property_integration.is_active or not property_integration.sync_availability:
            logger.info(f"Skipping availability sync for inactive integration: {property_integration_id}")
            return
        
        adapter = get_adapter(property_integration.platform.name, property_integration)
        if not adapter:
            return
        
        # Create sync log
        sync_log = SyncLog.objects.create(
            property_integration=property_integration,
            platform=property_integration.platform,
            sync_type='AVAILABILITY',
            status='IN_PROGRESS',
            started_at=timezone.now()
        )
        
        try:
            # Get inventory data from canonical model
            from core.models import Inventory
            from datetime import date, timedelta
            
            end_date = date.today() + timedelta(days=365)
            inventories = Inventory.objects.filter(
                property=property_integration.property,
                date__gte=date.today(),
                date__lte=end_date
            )
            
            # Transform to platform format
            inventory_data = {}
            for inv in inventories:
                # Map room type
                room_type_id = str(inv.room_type.id)
                provider_room_id = property_integration.provider_room_type_mappings.get(room_type_id)
                
                if provider_room_id:
                    if provider_room_id not in inventory_data:
                        inventory_data[provider_room_id] = {}
                    inventory_data[provider_room_id][str(inv.date)] = {
                        'available': inv.available_rooms,
                        'total': inv.total_rooms
                    }
            
            # Push to platform
            success = adapter.push_inventory(inventory_data)
            
            if success:
                sync_log.status = 'SUCCESS'
                sync_log.records_succeeded = len(inventory_data)
                PropertyIntegration.objects.filter(id=property_integration.id).update(
                    last_availability_sync=timezone.now(),
                    error_count=0
                )
            else:
                sync_log.status = 'FAILED'
                sync_log.error_message = "Failed to push availability"
            
        except Exception as e:
            logger.error(f"Error syncing availability: {e}", exc_info=True)
            sync_log.status = 'FAILED'
            sync_log.error_message = str(e)
            sync_log.error_details = {'exception': str(e), 'type': type(e).__name__}
            raise
        
        finally:
            sync_log.completed_at = timezone.now()
            if sync_log.started_at:
                sync_log.duration_seconds = (sync_log.completed_at - sync_log.started_at).total_seconds()
            sync_log.save()
    
    except PropertyIntegration.DoesNotExist:
        logger.error(f"PropertyIntegration not found: {property_integration_id}")
    except Exception as e:
        logger.error(f"Unexpected error in sync_availability: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def sync_rates(self, property_integration_id: str):
    """Sync rates for a property integration"""
    try:
        property_integration = PropertyIntegration.objects.get(id=property_integration_id)
        
        if not property_integration.is_active or not property_integration.sync_rates:
            logger.info(f"Skipping rates sync for inactive integration: {property_integration_id}")
            return
        
        adapter = get_adapter(property_integration.platform.name, property_integration)
        if not adapter:
            return
        
        sync_log = SyncLog.objects.create(
            property_integration=property_integration,
            platform=property_integration.platform,
            sync_type='RATES',
            status='IN_PROGRESS',
            started_at=timezone.now()
        )
        
        try:
            # Get rate plans from canonical model
            from core.models import RatePlan
            from datetime import date, timedelta
            
            end_date = date.today() + timedelta(days=365)
            rate_plans = RatePlan.objects.filter(
                property=property_integration.property,
                is_active=True
            )
            
            rates_data = {}
            for rate_plan in rate_plans:
                # Map rate plan
                rate_plan_id = str(rate_plan.id)
                provider_rate_id = property_integration.provider_rate_plan_mappings.get(rate_plan_id)
                
                if provider_rate_id:
                    rates_data[provider_rate_id] = {
                        'base_rate': float(rate_plan.base_rate.amount),
                        'currency': str(rate_plan.base_rate.currency),
                        'meal_plan': rate_plan.meal_plan.code if rate_plan.meal_plan else None,
                    }
            
            success = adapter.push_rates(rates_data)
            
            if success:
                sync_log.status = 'SUCCESS'
                sync_log.records_succeeded = len(rates_data)
                PropertyIntegration.objects.filter(id=property_integration.id).update(
                    last_rates_sync=timezone.now(),
                    error_count=0
                )
            else:
                sync_log.status = 'FAILED'
                sync_log.error_message = "Failed to push rates"
        
        except Exception as e:
            logger.error(f"Error syncing rates: {e}", exc_info=True)
            sync_log.status = 'FAILED'
            sync_log.error_message = str(e)
            sync_log.error_details = {'exception': str(e), 'type': type(e).__name__}
            raise
        
        finally:
            sync_log.completed_at = timezone.now()
            if sync_log.started_at:
                sync_log.duration_seconds = (sync_log.completed_at - sync_log.started_at).total_seconds()
            sync_log.save()
    
    except PropertyIntegration.DoesNotExist:
        logger.error(f"PropertyIntegration not found: {property_integration_id}")
    except Exception as e:
        logger.error(f"Unexpected error in sync_rates: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def sync_reservations(self, property_integration_id: str):
    """Pull reservations from platform"""
    try:
        property_integration = PropertyIntegration.objects.get(id=property_integration_id)
        
        if not property_integration.is_active or not property_integration.sync_reservations:
            logger.info(f"Skipping reservations sync for inactive integration: {property_integration_id}")
            return
        
        adapter = get_adapter(property_integration.platform.name, property_integration)
        if not adapter:
            return
        
        sync_log = SyncLog.objects.create(
            property_integration=property_integration,
            platform=property_integration.platform,
            sync_type='RESERVATIONS',
            status='IN_PROGRESS',
            started_at=timezone.now()
        )
        
        try:
            from datetime import date, timedelta
            
            start_date = date.today() - timedelta(days=7)
            end_date = date.today() + timedelta(days=365)
            
            reservations = adapter.pull_reservations(
                start_date=str(start_date),
                end_date=str(end_date)
            )
            
            # Process and save reservations
            from bookings.models import Reservation
            created_count = 0
            updated_count = 0
            
            for res_data in reservations:
                reservation, created = Reservation.objects.update_or_create(
                    provider_name=property_integration.platform.name,
                    provider_reservation_id=res_data.get('reservation_id'),
                    defaults={
                        'property': property_integration.property,
                        'guest_name': res_data.get('guest_name', ''),
                        'guest_email': res_data.get('guest_email', ''),
                        'check_in': res_data.get('check_in'),
                        'check_out': res_data.get('check_out'),
                        'status': res_data.get('status', 'PENDING'),
                        'total_amount': res_data.get('total_amount', 0),
                        # Map other fields as needed
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            sync_log.status = 'SUCCESS'
            sync_log.records_processed = len(reservations)
            sync_log.records_succeeded = created_count + updated_count
            PropertyIntegration.objects.filter(id=property_integration.id).update(
                last_reservations_sync=timezone.now(),
                error_count=0
            )
        
        except Exception as e:
            logger.error(f"Error syncing reservations: {e}", exc_info=True)
            sync_log.status = 'FAILED'
            sync_log.error_message = str(e)
            sync_log.error_details = {'exception': str(e), 'type': type(e).__name__}
            raise
        
        finally:
            sync_log.completed_at = timezone.now()
            if sync_log.started_at:
                sync_log.duration_seconds = (sync_log.completed_at - sync_log.started_at).total_seconds()
            sync_log.save()
    
    except PropertyIntegration.DoesNotExist:
        logger.error(f"PropertyIntegration not found: {property_integration_id}")
    except Exception as e:
        logger.error(f"Unexpected error in sync_reservations: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def reconcile_all_platforms():
    """Reconcile data across all platforms"""
    # Implementation for reconciliation
    pass


@shared_task
def process_webhook(platform_name: str, payload: dict):
    """Process webhook payload from platform"""
    try:
        adapter = get_adapter(platform_name)
        if not adapter:
            logger.error(f"Adapter not found for platform: {platform_name}")
            return
        
        result = adapter.handle_webhook(payload)
        logger.info(f"Webhook processed for {platform_name}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise


@shared_task
def cleanup_old_sync_logs():
    """Clean up old sync logs (older than 90 days)"""
    from datetime import timedelta
    from integrations.models import SyncLog
    
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count = SyncLog.objects.filter(created_at__lt=cutoff_date).delete()[0]
    logger.info(f"Cleaned up {deleted_count} old sync logs")


@shared_task
def schedule_syncs():
    """Periodic task to schedule syncs for all active integrations"""
    from datetime import timedelta
    
    active_integrations = PropertyIntegration.objects.filter(is_active=True)
    
    for integration in active_integrations:
        # Schedule availability sync
        if integration.sync_availability:
            last_sync = integration.last_availability_sync
            if not last_sync or (timezone.now() - last_sync) > timedelta(minutes=integration.availability_sync_interval):
                sync_availability.delay(str(integration.id))
        
        # Schedule rates sync
        if integration.sync_rates:
            last_sync = integration.last_rates_sync
            if not last_sync or (timezone.now() - last_sync) > timedelta(minutes=integration.rates_sync_interval):
                sync_rates.delay(str(integration.id))
        
        # Schedule reservations sync
        if integration.sync_reservations:
            last_sync = integration.last_reservations_sync
            if not last_sync or (timezone.now() - last_sync) > timedelta(minutes=integration.reservations_sync_interval):
                sync_reservations.delay(str(integration.id))

