from django.urls import path
from . import views

app_name = 'hotels'

urlpatterns = [
    path('', views.hotels_dashboard, name='dashboard'),
    path('search/', views.public_search_page, name='public_search'),
]
