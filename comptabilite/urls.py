# comptabilite/urls.py
from django.urls import path
from . import views

app_name = 'comptabilite'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('comptes/', views.liste_comptes, name='liste_comptes'),
    path('journal/', views.journal, name='journal'),
    path('transaction/ajouter/', views.ajouter_transaction, name='ajouter_transaction'),
]
