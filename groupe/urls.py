from django.urls import path
from . import views

app_name = 'groupe'

urlpatterns = [
    path('', views.GroupeListView.as_view(), name='liste'),
    path('ajouter/', views.GroupeCreateView.as_view(), name='ajouter'),
    path('<int:pk>/modifier/', views.GroupeUpdateView.as_view(), name='modifier'),
    path('<int:pk>/supprimer/', views.GroupeDeleteView.as_view(), name='supprimer'),
]
