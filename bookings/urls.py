from django.urls import path, include
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', include('bookings.urls_api')),  # API endpoints
]

