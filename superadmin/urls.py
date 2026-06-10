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
    path('mutualites/<int:pk>/renouveler-licence/', views.mutualite_renouveler_licence, name='mutualite_renouveler_licence'),
    path('mutualites/<int:pk>/prolonger-essai/', views.mutualite_essai_prolonger, name='mutualite_essai_prolonger'),

    # Utilisateurs (CRUD)
    path('utilisateurs/', views.utilisateurs_liste, name='utilisateurs_liste'),
    path('utilisateurs/creer/', views.utilisateur_creer, name='utilisateur_creer'),
    path('utilisateurs/<int:pk>/modifier/', views.utilisateur_modifier, name='utilisateur_modifier'),
    path('utilisateurs/<int:pk>/supprimer/', views.utilisateur_supprimer, name='utilisateur_supprimer'),

    # Clés d'activation
    path('cles/', views.cles_liste, name='cles_liste'),
    path('cles/generer/', views.cle_generer, name='cles_generer'),
    path('cles/<int:pk>/activer/', views.cle_activer, name='cle_activer'),
    path('cles/<int:pk>/revoquer/', views.cle_revoquer, name='cle_revoquer'),

    # Suivi par mutualité
    path('mutualites/<int:pk>/factures/', views.mutualite_factures, name='mutualite_factures'),
    path('mutualites/<int:pk>/membres/', views.mutualite_membres, name='mutualite_membres'),

    # Suivi index
    path('suivi-factures/', views.suivi_factures, name='suivi_factures'),
    path('suivi-membres/', views.suivi_membres, name='suivi_membres'),

    # Audit
    path('audit-connexions/', views.audit_connexions, name='audit_connexions'),
]
