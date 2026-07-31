from django.urls import path
from . import views
from . import views_corbeille

app_name = 'comptabilite'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Comptes
    path('comptes/', views.CompteListView.as_view(), name='compte_list'),
    path('comptes/creer/', views.CompteCreateView.as_view(), name='compte_create'),
    path('comptes/<int:pk>/modifier/', views.CompteUpdateView.as_view(), name='compte_update'),
    path('comptes/<int:pk>/supprimer/', views.CompteDeleteView.as_view(), name='compte_delete'),

    # Centres analytiques
    path('centres/', views.CentreAnalytiqueListView.as_view(), name='centre_list'),
    path('centres/creer/', views.CentreAnalytiqueCreateView.as_view(), name='centre_create'),

    # Écritures
    path('ecritures/', views.EcritureListView.as_view(), name='ecriture_list'),
    path('ecritures/creer/', views.EcritureCreateView.as_view(), name='ecriture_create'),
    path('ecritures/<int:pk>/', views.EcritureDetailView.as_view(), name='ecriture_detail'),
    path('ecritures/<int:pk>/modifier/', views.EcritureUpdateView.as_view(), name='ecriture_update'),
    path('ecritures/<int:pk>/soumettre/', views.EcritureSoumettreView.as_view(), name='ecriture_soumettre'),
    path('ecritures/<int:pk>/valider/', views.EcritureValidationView.as_view(), name='ecriture_valider'),

    # Budgets
    path('budgets/', views.BudgetListView.as_view(), name='budget_list'),
    path('budgets/creer/', views.BudgetCreateView.as_view(), name='budget_create'),
    path('budgets/<int:pk>/', views.BudgetDetailView.as_view(), name='budget_detail'),

    # Trésorerie
    path('tresorerie/', views.PrevisionListView.as_view(), name='prevision_list'),
    path('tresorerie/creer/', views.PrevisionCreateView.as_view(), name='prevision_create'),

    # Rapprochement
    path('rapprochements/', views.RapprochementListView.as_view(), name='rapprochement_list'),
    path('rapprochements/creer/', views.RapprochementCreateView.as_view(), name='rapprochement_create'),

    # Corbeille
    path('corbeille/', views_corbeille.CorbeilleListView.as_view(), name='corbeille_list'),
    path('corbeille/<int:pk>/', views_corbeille.CorbeilleDetailView.as_view(), name='corbeille_detail'),
    path('corbeille/<int:pk>/restaurer/', views_corbeille.corbeille_restaurer, name='corbeille_restaurer'),
    path('corbeille/restaurer-multiple/', views_corbeille.corbeille_restaurer_multiple, name='corbeille_restaurer_multiple'),
    path('corbeille/<int:pk>/purger/', views_corbeille.corbeille_purger, name='corbeille_purger'),
    path('corbeille/purger-multiple/', views_corbeille.corbeille_purger_multiple, name='corbeille_purger_multiple'),
    path('corbeille/vider-expires/', views_corbeille.corbeille_vider_expires, name='corbeille_vider_expires'),

    # Rapports
    path('rapports/', views.RapportView.as_view(), name='rapport'),

    # Guide d'utilisation
    path('guide/', views.GuideView.as_view(), name='guide'),
    path('guide/pdf/', views.GuidePdfView.as_view(), name='guide_pdf'),

    # Export
    path('export/grand-livre/', views.ExportGrandLivreView.as_view(), name='export_grand_livre'),

    # API légère
    path('api/transactions-recentes/', views.recent_transactions_json, name='api_transactions'),
]
