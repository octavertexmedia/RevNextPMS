from django.urls import path
from . import views
from . import views_terminal
from . import views_public
from . import views_ops

app_name = 'cloud_pos'

urlpatterns = [
    path('', views.pos_dashboard, name='dashboard'),
    path('billing/', views_terminal.billing_terminal, name='billing'),
    path('billing/api/', views_terminal.billing_api, name='billing_api'),
    path('waiter/', views_terminal.waiter_board, name='waiter'),
    path('inventory/', views_ops.inventory_list, name='inventory'),
    path('inventory/<int:item_id>/adjust/', views_ops.inventory_adjust, name='inventory_adjust'),
    path('delivery/', views_ops.delivery_inbox, name='delivery_inbox'),
    path('delivery/add/', views_ops.delivery_create, name='delivery_create'),
    path('delivery/<int:order_id>/accept/', views_ops.delivery_accept, name='delivery_accept'),
    path('qr/<str:token>/', views_public.qr_order, name='qr_order'),
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
