from django.urls import path
from . import views

app_name = 'google_hotel_ads'

urlpatterns = [
    path('', views.hotel_ads_dashboard, name='dashboard'),
    path('config/add/', views.config_create, name='config_create'),
    path('config/<int:config_id>/edit/', views.config_edit, name='config_edit'),
    path('config/<int:config_id>/submit-feed/', views.feed_submit, name='feed_submit'),
]
