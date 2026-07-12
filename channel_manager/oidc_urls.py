from django.urls import path

from channel_manager import oidc

app_name = 'oidc'

urlpatterns = [
    path('login/', oidc.oidc_login, name='login'),
    path('callback/', oidc.oidc_callback, name='callback'),
    path('logout/', oidc.oidc_logout, name='logout'),
    path('.well-known/', oidc.oidc_metadata, name='metadata'),
]
