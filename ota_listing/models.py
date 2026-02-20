"""
OTA Listing Service - Professional setup & optimization

Setup and optimize property listings on major OTAs. Get your property online fast.
"""
from django.db import models
from core.models import Property, TimeStampedModel
from integrations.models import IntegrationPlatform, PropertyIntegration


class ListingProject(TimeStampedModel):
    """OTA listing setup project"""
    
    STATUS = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('LIVE', 'Live'),
        ('OPTIMIZED', 'Optimized'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='listing_projects')
    platform = models.ForeignKey(IntegrationPlatform, on_delete=models.CASCADE, related_name='listing_projects')
    
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    provider_property_id = models.CharField(max_length=255, blank=True)
    
    # Optimization
    listing_score = models.PositiveIntegerField(null=True, blank=True, help_text="0-100 quality score")
    optimization_notes = models.TextField(blank=True)
    
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['property', 'platform']


class OTAListingStatus(TimeStampedModel):
    """Status snapshot for OTA listing"""
    id = models.BigAutoField(primary_key=True)
    property_integration = models.ForeignKey(PropertyIntegration, on_delete=models.CASCADE, related_name='listing_statuses')
    status = models.CharField(max_length=50)
    details = models.JSONField(default=dict)
    recorded_at = models.DateTimeField(auto_now_add=True)
