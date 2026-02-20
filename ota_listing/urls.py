from django.urls import path
from . import views

app_name = 'ota_listing'

urlpatterns = [
    path('', views.ota_listing_dashboard, name='dashboard'),
    path('projects/add/', views.project_create, name='project_create'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:project_id>/status/', views.project_status_update, name='project_status_update'),
    path('projects/<int:project_id>/checklist/', views.project_optimization_checklist, name='project_optimization_checklist'),
]
