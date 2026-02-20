"""
Website Builder - No-code templates, SEO, SSL

Templates, SEO optimization, free hosting with SSL. Direct link to Booking Engine.
"""
from django.db import models
from core.models import Property, TimeStampedModel


class SiteTemplate(TimeStampedModel):
    """Pre-built website template"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(blank=True)
    template_html = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PropertyWebsite(TimeStampedModel):
    """Property's built website"""
    id = models.BigAutoField(primary_key=True)
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='built_website')
    template = models.ForeignKey(SiteTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Domain
    custom_domain = models.CharField(max_length=255, blank=True)
    subdomain = models.CharField(max_length=100, blank=True, help_text="e.g., myhotel.revnext.in")
    
    # SSL
    ssl_enabled = models.BooleanField(default=True)
    
    # Content
    custom_css = models.TextField(blank=True)
    custom_js = models.TextField(blank=True)
    
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Property Website'
        verbose_name_plural = 'Property Websites'

    def __str__(self):
        return f"Website - {self.property.name}"
