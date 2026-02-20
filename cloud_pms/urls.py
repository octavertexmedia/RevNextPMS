from django.urls import path
from . import views

app_name = 'cloud_pms'

urlpatterns = [
    path('', views.pms_dashboard, name='dashboard'),
    path('property/<int:property_id>/', views.pms_dashboard_property, name='dashboard_property'),
    path('housekeeping/', views.housekeeping_list, name='housekeeping'),
    path('housekeeping/add/', views.housekeeping_task_create, name='housekeeping_task_create'),
    path('housekeeping/<int:task_id>/edit/', views.housekeeping_task_edit, name='housekeeping_task_edit'),
    path('housekeeping/<int:task_id>/status/', views.housekeeping_task_status_update, name='housekeeping_task_status_update'),
    path('folios/', views.folios_list, name='folios'),
    path('folios/add/', views.folio_create, name='folio_create'),
    path('folios/<int:folio_id>/', views.folio_detail, name='folio_detail'),
    path('folios/<int:folio_id>/line-item/add/', views.folio_line_item_add, name='folio_line_item_add'),
    path('folios/<int:folio_id>/line-item/<int:line_item_id>/delete/', views.folio_line_item_delete, name='folio_line_item_delete'),
    path('linked-rooms/', views.linked_rooms_list, name='linked_rooms'),
    path('linked-rooms/add/', views.linked_room_create, name='linked_room_create'),
    path('linked-rooms/<int:unit_id>/edit/', views.linked_room_edit, name='linked_room_edit'),
    path('folios/<int:folio_id>/close/', views.folio_close, name='folio_close'),
]
