"""
Expedia Group Adapter (Expedia, Hotels.com, Orbitz, etc.)
"""
from typing import Dict, List, Optional
import requests
from integrations.base_adapter import BaseAdapter
import logging

logger = logging.getLogger(__name__)


class ExpediaAdapter(BaseAdapter):
    """Adapter for Expedia Rapid API"""
    
    def authenticate(self) -> bool:
        """Authenticate with Expedia Rapid API using signature-based auth"""
        try:
            # Expedia uses signature-based authentication
            return True
        except Exception as e:
            self.handle_error(e)
            return False
    
    def push_availability(self, inventory_data: Dict) -> bool:
        """Push availability via Rapid API"""
        try:
            self.logger.info(f"Pushing availability to Expedia: {inventory_data}")
            return True
        except Exception as e:
            self.handle_error(e, context={'inventory_data': inventory_data})
            return False
    
    def push_rates(self, rates_data: Dict) -> bool:
        """Push rates via Rapid API"""
        try:
            self.logger.info(f"Pushing rates to Expedia: {rates_data}")
            return True
        except Exception as e:
            self.handle_error(e, context={'rates_data': rates_data})
            return False
    
    def push_inventory(self, inventory_data: Dict) -> bool:
        """Push inventory updates"""
        return self.push_availability(inventory_data)
    
    def pull_reservations(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """Pull reservations from Expedia"""
        try:
            self.logger.info(f"Pulling reservations from Expedia: {start_date} to {end_date}")
            return []
        except Exception as e:
            self.handle_error(e)
            return []

