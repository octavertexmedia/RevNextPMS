from django.urls import path
from . import views

app_name = 'cloud_pos'

urlpatterns = [
    path('', views.pos_dashboard, name='dashboard'),
    path('orders/', views.pos_orders, name='orders'),
    path('orders/add/', views.order_create, name='order_create'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/item/add/', views.order_add_item, name='order_add_item'),
    path('orders/<int:order_id>/item/<int:item_id>/delete/', views.order_item_delete, name='order_item_delete'),
    path('orders/<int:order_id>/status/', views.order_status_update, name='order_status_update'),
    path('menu/', views.pos_menu, name='menu'),
    path('menu/category/add/', views.menu_category_create, name='menu_category_create'),
    path('menu/category/<int:category_id>/edit/', views.menu_category_edit, name='menu_category_edit'),
    path('menu/item/add/', views.menu_item_create, name='menu_item_create'),
    path('menu/item/<int:item_id>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('tables/', views.pos_tables, name='tables'),
    path('tables/add/', views.table_create, name='table_create'),
    path('tables/<int:table_id>/edit/', views.table_edit, name='table_edit'),
]
