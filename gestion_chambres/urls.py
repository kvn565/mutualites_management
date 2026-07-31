from django.urls import path
from . import views

app_name = 'gestion_chambres'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Établissements
    path('etablissements/', views.etablissement_liste, name='etablissement_liste'),
    path('etablissements/nouveau/', views.etablissement_creer, name='etablissement_creer'),
    path('etablissements/<int:pk>/modifier/', views.etablissement_modifier, name='etablissement_modifier'),
    path('etablissements/<int:pk>/supprimer/', views.etablissement_supprimer, name='etablissement_supprimer'),

    # Services
    path('services/', views.service_liste, name='service_liste'),
    path('services/nouveau/', views.service_creer, name='service_creer'),
    path('services/<int:pk>/modifier/', views.service_modifier, name='service_modifier'),
    path('services/<int:pk>/supprimer/', views.service_supprimer, name='service_supprimer'),

    # Types de chambres
    path('types/', views.type_chambre_liste, name='type_chambre_liste'),
    path('types/nouveau/', views.type_chambre_creer, name='type_chambre_creer'),
    path('types/<int:pk>/modifier/', views.type_chambre_modifier, name='type_chambre_modifier'),
    path('types/<int:pk>/supprimer/', views.type_chambre_supprimer, name='type_chambre_supprimer'),

    # Chambres
    path('chambres/', views.chambre_liste, name='chambre_liste'),
    path('chambres/nouvelle/', views.chambre_creer, name='chambre_creer'),
    path('chambres/<int:pk>/', views.chambre_detail, name='chambre_detail'),
    path('chambres/<int:pk>/modifier/', views.chambre_modifier, name='chambre_modifier'),
    path('chambres/<int:pk>/statut/', views.chambre_changer_statut, name='chambre_changer_statut'),

    # Hospitalisations
    path('hospitalisations/', views.hospitalisation_liste, name='hospitalisation_liste'),
    path('hospitalisations/nouvelle/', views.hospitalisation_creer, name='hospitalisation_creer'),
    path('hospitalisations/<int:pk>/', views.hospitalisation_detail, name='hospitalisation_detail'),
    path('hospitalisations/<int:pk>/sortie/', views.hospitalisation_sortie, name='hospitalisation_sortie'),
    path('hospitalisations/<int:pk>/prolonger/', views.hospitalisation_prolonger, name='hospitalisation_prolonger'),
    path('hospitalisations/<int:pk>/transfert/', views.hospitalisation_transfert, name='hospitalisation_transfert'),

    # Soins
    path('hospitalisations/<int:hospitalisation_pk>/soins/', views.soin_liste, name='soin_liste'),
    path('hospitalisations/<int:hospitalisation_pk>/soins/nouveau/', views.soin_creer, name='soin_creer'),
    path('soins/<int:pk>/modifier/', views.soin_modifier, name='soin_modifier'),
    path('soins/<int:pk>/supprimer/', views.soin_supprimer, name='soin_supprimer'),

    # API / AJAX
    path('api/chambres-disponibles/', views.api_chambres_disponibles, name='api_chambres_disponibles'),
    path('api/chambres/<int:pk>/occuper/', views.api_occuper_chambre, name='api_occuper_chambre'),
    path('api/chambres/<int:pk>/liberer/', views.api_liberer_chambre, name='api_liberer_chambre'),
]