# origines/urls.py
from django.urls import path
from . import views

app_name = 'origines'

urlpatterns = [
    path('', views.liste, name='liste'),
    path('ajouter/', views.ajouter, name='ajouter'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/modifier/', views.modifier, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer, name='supprimer'),
]
