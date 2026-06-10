from django.urls import path
from . import views

app_name = 'affilies'

urlpatterns = [
    path('', views.AffilieListView.as_view(), name='liste'),
    path('ajouter/', views.AffilieCreateView.as_view(), name='ajouter'),
    path('<int:pk>/', views.AffilieDetailView.as_view(), name='detail'),
    path('<int:pk>/modifier/', views.AffilieUpdateView.as_view(), name='modifier'),
    path('<int:pk>/supprimer/', views.AffilieDeleteView.as_view(), name='supprimer'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('<int:pk>/fiche/', views.fiche_pdf, name='fiche_pdf'),
]
