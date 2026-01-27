"""
URLs for Reports app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    generate_report_view,
    ReportTemplateViewSet,
    GeneratedReportViewSet,
    ScheduledReportViewSet,
)

app_name = 'reports'

router = DefaultRouter()
router.register(r'templates', ReportTemplateViewSet, basename='report-template')
router.register(r'generated', GeneratedReportViewSet, basename='generated-report')
router.register(r'scheduled', ScheduledReportViewSet, basename='scheduled-report')

urlpatterns = [
    path('generate/<int:template_id>/', generate_report_view, name='generate_report'),
    path('', include(router.urls)),
]
