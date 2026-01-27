"""
Base Adapter Class for Platform Integrations
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """Base class for all platform adapters"""
    
    def __init__(self, platform, property_integration=None):
        self.platform = platform
        self.property_integration = property_integration
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the platform API"""
        pass
    
    @abstractmethod
    def push_availability(self, inventory_data: Dict) -> bool:
        """Push availability updates to platform"""
        pass
    
    @abstractmethod
    def push_rates(self, rates_data: Dict) -> bool:
        """Push rate updates to platform"""
        pass
    
    @abstractmethod
    def push_inventory(self, inventory_data: Dict) -> bool:
        """Push inventory updates to platform"""
        pass
    
    @abstractmethod
    def pull_reservations(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """Pull reservations from platform"""
        pass
    
    def handle_webhook(self, payload: Dict) -> Dict:
        """Handle incoming webhook from platform"""
        raise NotImplementedError("Webhook handling not implemented for this platform")
    
    def validate_response(self, response: Any) -> bool:
        """Validate API response"""
        return True
    
    def handle_error(self, error: Exception, context: Dict = None) -> None:
        """Handle errors with logging and error tracking"""
        error_msg = str(error)
        self.logger.error(f"Error in {self.__class__.__name__}: {error_msg}", exc_info=True, extra=context)
        
        if self.property_integration:
            from .models import PropertyIntegration
            from django.db.models import F
            PropertyIntegration.objects.filter(id=self.property_integration.id).update(
                last_error=error_msg,
                error_count=F('error_count') + 1,
                last_error_at=timezone.now()
            )

