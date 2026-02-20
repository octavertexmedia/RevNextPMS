from django.urls import path
from . import views

app_name = 'payment_gateways'

urlpatterns = [
    path('', views.gateways_dashboard, name='dashboard'),
    path('config/add/', views.config_create, name='config_create'),
    path('config/<int:config_id>/edit/', views.config_edit, name='config_edit'),
    path('config/<int:config_id>/test/', views.test_transaction, name='test_transaction'),
]
