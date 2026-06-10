# utilisateurs/urls.py
from django.urls import path
from . import views

app_name = 'utilisateurs'

urlpatterns = [
    path('', views.liste, name='index'),
    path('liste/', views.liste, name='liste'),
    path('ajouter/', views.ajouter, name='ajouter'),
    path('<int:pk>/modifier/', views.modifier, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer, name='supprimer'),
    path('inscription-chef/', views.inscription_chef, name='inscription_chef'),
]
