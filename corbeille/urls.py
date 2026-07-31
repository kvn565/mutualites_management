from django.urls import path
from . import views

app_name = 'corbeille'

urlpatterns = [
    path('', views.CorbeilleListView.as_view(), name='index'),
    path('<int:pk>/', views.CorbeilleDetailView.as_view(), name='detail'),
    path('<int:pk>/restaurer/', views.corbeille_restaurer, name='restaurer'),
    path('restaurer-multiple/', views.corbeille_restaurer_multiple, name='restaurer_multiple'),
    path('<int:pk>/purger/', views.corbeille_purger, name='purger'),
    path('purger-multiple/', views.corbeille_purger_multiple, name='purger_multiple'),
    path('vider-expires/', views.corbeille_vider_expires, name='vider_expires'),
]