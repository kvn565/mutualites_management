# factures/urls.py
from django.urls import path
from . import views

app_name = 'factures'

urlpatterns = [
    path('', views.liste, name='liste'),
    path('journal/', views.journal, name='journal'),
    path('ajouter/', views.ajouter, name='ajouter'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/modifier/', views.modifier, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer, name='supprimer'),
    # Workflow de validation
    path('<int:pk>/soumettre/', views.soumettre, name='soumettre'),
    path('<int:pk>/valider/', views.valider, name='valider'),
    path('<int:pk>/rejeter/', views.rejeter, name='rejeter'),
    path('<int:pk>/marquer-paye/', views.marquer_paye, name='marquer_paye'),
    path('rechercher-affilie/', views.rechercher_affilie_json, name='rechercher_affilie'),
]

