from django.urls import path
from . import views

app_name = 'affilies'

urlpatterns = [
    path('', views.AffilieListView.as_view(), name='liste'),
    path('ajouter/', views.AffilieCreateView.as_view(), name='ajouter'),
    path('<int:pk>/', views.AffilieDetailView.as_view(), name='detail'),
    path('<int:pk>/modifier/', views.AffilieUpdateView.as_view(), name='modifier'),
    path('<int:pk>/supprimer/', views.AffilieDeleteView.as_view(), name='supprimer'),
    path('importer/', views.importer, name='importer'),
    path('importer/modele/', views.telecharger_modele, name='modele_import'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('<int:pk>/fiche/', views.fiche_pdf, name='fiche_pdf'),
    path('ajax/detail/<int:pk>/', views.affilie_details_ajax, name='affilie_ajax_detail'),
    path('ajax/origin-plafonds/<int:pk>/', views.origin_plafonds_ajax, name='origin_plafonds_ajax'),

    # Exclusions
    path('<int:affilie_pk>/exclusions/ajouter/', views.exclusion_ajouter, name='exclusion_ajouter'),
    path('exclusions/<int:pk>/supprimer/', views.exclusion_supprimer, name='exclusion_supprimer'),
    path('ajax/<int:affilie_pk>/exclusions/', views.exclusion_liste_ajax, name='exclusion_liste_ajax'),
    path('recherche-ajax/', views.recherche_ajax, name='recherche_ajax'),
]
