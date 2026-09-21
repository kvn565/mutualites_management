# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('inscription/', views.inscription_view, name='inscription'),
    path('inscription/attente/', views.inscription_attente, name='inscription_attente'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('profil/', views.profil_view, name='profil'),

    # Notifications plafond
    path('notifications/', views.notification_liste, name='notification_liste'),
    path('notifications/<int:pk>/marquer-vue/', views.notification_marquer_vue, name='notification_marquer_vue'),
    path('notifications/<int:pk>/marquer-vue-rapide/', views.notification_marquer_vue_rapide, name='notification_marquer_vue_rapide'),
    path('notifications/tout-vu/', views.notification_tout_vu, name='notification_tout_vu'),
    path('notifications/<int:pk>/debloquer/', views.notification_debloquer, name='notification_debloquer'),
    path('notifications/<int:pk>/bloquer-definitif/', views.notification_bloquer_definitif, name='notification_bloquer_definitif'),

    # Exclusions globales
    path('exclusions-globales/ajouter/', views.mutualite_exclusion_ajouter, name='mutualite_exclusion_ajouter'),
    path('exclusions-globales/<int:pk>/supprimer/', views.mutualite_exclusion_supprimer, name='mutualite_exclusion_supprimer'),
]
