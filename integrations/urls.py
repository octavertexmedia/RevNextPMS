from django.urls import path, include
from . import views

app_name = 'integrations'

urlpatterns = [
    path('webhooks/<str:platform_name>/', views.webhook_handler, name='webhook_handler'),
    path('', include('integrations.urls_api')),  # API endpoints
]

