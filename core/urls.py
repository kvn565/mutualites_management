# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('inscription/', views.inscription_view, name='inscription'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('profil/', views.profil_view, name='profil'),
]
