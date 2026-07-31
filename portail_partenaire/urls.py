from django.urls import path
from . import views

app_name = 'portail_partenaire'

urlpatterns = [
    path('connexion/', views.connexion, name='connexion'),
    path('inscription/', views.inscription, name='inscription'),
    path('inscription/attente/', views.inscription_attente, name='inscription_attente'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('changer-mutualite/', views.changer_mutualite, name='changer_mutualite'),
    path('', views.dashboard, name='dashboard'),
    path('profil/', views.profil, name='profil'),
    path('membres/', views.recherche_membre, name='recherche_membre'),
    path('membres/<int:pk>/', views.detail_membre, name='detail_membre'),
    path('affilie/search/', views.affilie_search_json, name='affilie_search_json'),

    path('membres/<int:membre_pk>/facture/ajouter/', views.ajouter_facture, name='ajouter_facture'),
    path('factures/ajouter/', views.ajouter_facture_simple, name='ajouter_facture_simple'),
    path('factures/', views.liste_factures, name='liste_factures'),
    path('factures/<int:pk>/', views.detail_facture, name='detail_facture'),

    path('membres/<int:membre_pk>/document/transferer/', views.transferer_document, name='transferer_document'),

    # Impression / Export
    path('factures/<int:pk>/recu/', views.imprimer_recu, name='imprimer_recu'),
    path('factures/<int:pk>/pdf/', views.export_pdf, name='export_pdf'),

    # Profil
    path('profil/modifier/', views.modifier_profil, name='modifier_profil'),
    path('profil/configuration/', views.configuration_compte, name='configuration_compte'),
    path('profil/configuration/creer-utilisateur/', views.creer_utilisateur, name='creer_utilisateur'),
    path('profil/mutualite/<int:mutualite_pk>/bloquer/', views.bloquer_relation, name='bloquer_relation'),
    path('profil/mutualite/<int:mutualite_pk>/debloquer/', views.debloquer_relation, name='debloquer_relation'),

    # Notification
    path('notifications/dismiss/', views.notification_dismiss, name='notification_dismiss'),

    # Pharmacie / Médicaments
    path('medicaments/', views.liste_medicaments, name='liste_medicaments'),
    path('medicaments/ajouter/', views.ajouter_medicament, name='ajouter_medicament'),
    path('medicaments/<int:pk>/modifier/', views.modifier_medicament, name='modifier_medicament'),
    path('medicaments/<int:pk>/supprimer/', views.supprimer_medicament, name='supprimer_medicament'),
]
