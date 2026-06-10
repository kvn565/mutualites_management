# ayants_droit/urls.py
from django.urls import path
from . import views

app_name = 'ayants_droit'

urlpatterns = [
    path('', views.liste, name='liste'),
    path('ajouter/', views.ajouter, name='ajouter'),
    path('<int:pk>/modifier/', views.modifier, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer, name='supprimer'),
]
