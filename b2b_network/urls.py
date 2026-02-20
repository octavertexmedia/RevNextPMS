from django.urls import path
from . import views

app_name = 'b2b_network'

urlpatterns = [
    path('', views.b2b_dashboard, name='dashboard'),
    path('agents/', views.b2b_agents, name='agents'),
    path('agents/add/', views.agent_create, name='agent_create'),
    path('agents/<int:agent_id>/', views.agent_detail, name='agent_detail'),
    path('agents/<int:agent_id>/edit/', views.agent_edit, name='agent_edit'),
    path('agents/<int:agent_id>/rate/add/', views.b2b_rate_create, name='b2b_rate_create'),
    path('agents/<int:agent_id>/rate/<int:rate_id>/edit/', views.b2b_rate_edit, name='b2b_rate_edit'),
]
