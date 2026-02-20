from django.urls import path
from . import views

app_name = 'booking_engine'

urlpatterns = [
    path('', views.booking_dashboard, name='dashboard'),
    path('settings/', views.booking_settings, name='settings'),
    path('widget/<int:property_id>/', views.booking_widget, name='widget'),
    path('availability/', views.availability_check, name='availability_check'),
    path('availability/results/', views.availability_results, name='availability_results'),
    path('availability/select-rate/', views.booking_select_rate, name='booking_select_rate'),
    path('guest/', views.guest_form, name='guest_form'),
    path('confirm/', views.booking_confirm, name='booking_confirm'),
    path('create/', views.booking_create, name='booking_create'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
]
