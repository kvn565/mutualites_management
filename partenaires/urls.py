from django.urls import path
from . import views

app_name = 'partenaires'

urlpatterns = [
    path('', views.liste, name='liste'),
    path('ajouter/', views.ajouter, name='ajouter'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/modifier/', views.modifier, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer, name='supprimer'),
    path('<int:pk>/supprimer-attente/', views.supprimer_attente, name='supprimer_attente'),
    path('<int:pk>/suspendre/', views.suspendre, name='suspendre'),
    path('<int:pk>/reactiver/', views.reactiver, name='reactiver'),
    path('<int:pk>/accepter/', views.accepter_demande, name='accepter_demande'),
    path('<int:pk>/bloquer-relation/', views.bloquer_relation, name='bloquer_relation'),
    path('<int:pk>/debloquer-relation/', views.debloquer_relation, name='debloquer_relation'),
    path('<int:pk>/restaurer/', views.restaurer, name='restaurer'),
    path('<int:pk>/purger/', views.purger, name='purger'),
]
