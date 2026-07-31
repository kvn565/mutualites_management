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
    path('ajax/creer/', views.ajax_creer, name='ajax_creer'),

    # Exclusions
    path('<int:origine_pk>/exclusions/ajouter/', views.exclusion_ajouter, name='exclusion_ajouter'),
    path('exclusions/<int:pk>/supprimer/', views.exclusion_supprimer, name='exclusion_supprimer'),
]
