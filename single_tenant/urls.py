from django.urls import path
from . import views

app_name = 'single_tenant'

urlpatterns = [
    path('config/', views.SingleTenantConfigView.as_view(), name='config'),
    path('config/update/', views.SingleTenantConfigUpdateView.as_view(), name='config_update'),
    path('config/toggle/<int:pk>/', views.toggle_active, name='toggle_active'),
]
