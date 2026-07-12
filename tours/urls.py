from django.urls import path
from . import views

app_name = 'tours'

urlpatterns = [
    path('', views.tours_dashboard, name='dashboard'),
    path('catalog/', views.public_catalog, name='public_catalog'),
    path('packages/<int:package_id>/', views.package_detail, name='package_detail'),
]
