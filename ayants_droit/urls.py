# ayants_droit/urls.py
from django.urls import path
from . import views

app_name = 'ayants_droit'

urlpatterns = [
    path('', views.liste, name='liste'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('importer/', views.importer, name='importer'),
    path('importer/modele/', views.telecharger_modele, name='modele_import'),
    path('ajouter/', views.ajouter, name='ajouter'),
    path('<int:pk>/modifier/', views.modifier, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer, name='supprimer'),
]
