from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    # Tableau de bord
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Mutualités (CRUD)
    path('mutualites/', views.mutualites_liste, name='mutualites_liste'),
    path('mutualites/creer/', views.mutualite_creer, name='mutualite_creer'),
    path('mutualites/<int:pk>/', views.mutualite_detail, name='mutualite_detail'),
    path('mutualites/<int:pk>/modifier/', views.mutualite_modifier, name='mutualite_modifier'),

    # Actions sur les mutualités
    path('mutualites/<int:pk>/suspendre/', views.mutualite_suspendre, name='mutualite_suspendre'),
    path('mutualites/<int:pk>/reactiver/', views.mutualite_reactiver, name='mutualite_reactiver'),
    path('mutualites/<int:pk>/prolonger-essai/', views.mutualite_essai_prolonger, name='mutualite_essai_prolonger'),

    # Utilisateurs (CRUD)
    path('utilisateurs/', views.utilisateurs_liste, name='utilisateurs_liste'),
    path('utilisateurs/creer/', views.utilisateur_creer, name='utilisateur_creer'),
    path('utilisateurs/<int:pk>/modifier/', views.utilisateur_modifier, name='utilisateur_modifier'),
    path('utilisateurs/<int:pk>/supprimer/', views.utilisateur_supprimer, name='utilisateur_supprimer'),

    # Validations (inscriptions en attente)
    path('validations/mutualites/', views.validations_mutualites, name='validations_mutualites'),
    path('validations/mutualites/<int:pk>/activer/', views.valider_mutualite, name='valider_mutualite'),
    path('validations/partenaires/', views.validations_partenaires, name='validations_partenaires'),
    path('validations/partenaires/<int:pk>/activer/', views.valider_partenaire, name='valider_partenaire'),



    # Suivi par mutualité
    path('mutualites/<int:pk>/factures/', views.mutualite_factures, name='mutualite_factures'),
    path('mutualites/<int:pk>/membres/', views.mutualite_membres, name='mutualite_membres'),

    # Suivi index
    path('suivi-factures/', views.suivi_factures, name='suivi_factures'),
    path('suivi-membres/', views.suivi_membres, name='suivi_membres'),
    path('notifications/', views.notifications_liste, name='notifications_liste'),

    # Audit
    path('audit-connexions/', views.audit_connexions, name='audit_connexions'),

    # Export & Utilitaires
    path('mutualites/export-excel/', views.export_toutes_mutualites_excel, name='export_toutes_mutualites_excel'),
    path('mutualites/<int:pk>/export-excel/', views.export_mutualite_excel, name='export_mutualite_excel'),
    path('reinitialiser-selection/', views.reinitialiser_selection, name='reinitialiser_selection'),
    path('mutualites/<int:pk>/reinitialiser/', views.mutualite_reinitialiser, name='mutualite_reinitialiser'),
    path('ajax-verifier-nif/', views.ajax_verifier_nif, name='ajax_verifier_nif'),

    # Partenaires (CRUD & Actions)
    path('partenaires/', views.partenaires_liste, name='partenaires_liste'),
    path('partenaires/creer/', views.partenaire_creer, name='partenaire_creer'),
    path('partenaires/<int:pk>/', views.partenaire_detail, name='partenaire_detail'),
    path('partenaires/<int:pk>/modifier/', views.partenaire_modifier, name='partenaire_modifier'),
    path('partenaires/<int:pk>/suspendre/', views.partenaire_suspendre, name='partenaire_suspendre'),
    path('partenaires/<int:pk>/reactiver/', views.partenaire_reactiver, name='partenaire_reactiver'),
    path('partenaires/<int:pk>/bloquer/', views.partenaire_bloquer, name='partenaire_bloquer'),
    path('partenaires/<int:pk>/debloquer/', views.partenaire_debloquer, name='partenaire_debloquer'),
    path('partenaires/<int:pk>/supprimer/', views.partenaire_supprimer, name='partenaire_supprimer'),
    path('partenaires/<int:pk>/utilisateurs/', views.partenaire_utilisateurs, name='partenaire_utilisateurs'),
    path('partenaires/<int:partenaire_pk>/utilisateurs/<int:user_pk>/modifier/', views.partenaire_utilisateur_modifier, name='partenaire_utilisateur_modifier'),
    path('partenaires/<int:pk>/conventions/', views.partenaire_conventions, name='partenaire_conventions'),
    path('partenaires/<int:pk>/valider/', views.partenaire_valider, name='partenaire_valider'),
    path('partenaires/<int:pk>/mutualite/<int:mutualite_pk>/supprimer-validation/', views.partenaire_supprimer_validation, name='partenaire_supprimer_validation'),

    # Configuration
    path('configuration/', views.configuration_app, name='configuration_app'),
]
