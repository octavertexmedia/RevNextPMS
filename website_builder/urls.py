from django.urls import path
from . import views

app_name = 'website_builder'

urlpatterns = [
    path('', views.website_dashboard, name='dashboard'),
    path('edit/<int:property_id>/', views.website_editor, name='editor'),
    path('preview/<int:property_id>/', views.website_preview, name='preview'),
]
