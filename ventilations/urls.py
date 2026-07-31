from django.urls import path
from . import views

app_name = 'ventilations'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='index'),

    # Branches
    path('branches/', views.BrancheListView.as_view(), name='branche_list'),
    path('branches/creer/', views.BrancheCreateView.as_view(), name='branche_create'),
    path('branches/<int:pk>/modifier/', views.BrancheUpdateView.as_view(), name='branche_update'),

    # Règles de ventilation
    path('regles/', views.RegleListView.as_view(), name='regle_list'),
    path('regles/creer/', views.RegleCreateView.as_view(), name='regle_create'),
    path('regles/<int:pk>/modifier/', views.RegleUpdateView.as_view(), name='regle_update'),
    path('regles/<int:pk>/supprimer/', views.RegleDeleteView.as_view(), name='regle_delete'),

    # Ventilations
    path('ventilations/', views.VentilationListView.as_view(), name='ventilation_list'),
    path('ventilations/creer/', views.VentilationCreateView.as_view(), name='ventilation_create'),
    path('ventilations/<int:pk>/', views.VentilationDetailView.as_view(), name='ventilation_detail'),
    path('ventilations/<int:pk>/modifier/', views.VentilationUpdateView.as_view(), name='ventilation_update'),
    path('ventilations/<int:pk>/valider/', views.VentilationValiderView.as_view(), name='ventilation_valider'),
    path('ventilations/<int:pk>/annuler/', views.VentilationAnnulerView.as_view(), name='ventilation_annuler'),
    path('ventilations/auto/', views.AutoVentilationView.as_view(), name='ventilation_auto'),

    # Ventilation globale
    path('globales/', views.VentilationGlobaleListView.as_view(), name='globale_list'),
    path('globales/creer/', views.VentilationGlobaleCreateView.as_view(), name='globale_create'),
    path('globales/<int:pk>/', views.VentilationGlobaleDetailView.as_view(), name='globale_detail'),

    # Historique
    path('historique/', views.HistoriqueListView.as_view(), name='historique'),

    # Rapport
    path('rapport/', views.RapportAnalytiqueView.as_view(), name='rapport'),

    # Export
    path('export/csv/', views.ExportVentilationCSVView.as_view(), name='export_csv'),

    # API
    path('api/ventiler/<int:ecriture_pk>/', views.api_ventiler_ecriture, name='api_ventiler'),
    path('api/resume/', views.api_resume_ventilation, name='api_resume'),
]
