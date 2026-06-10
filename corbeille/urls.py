# corbeille/urls.py
from django.urls import path
from . import views

app_name = 'corbeille'

urlpatterns = [
    path('', views.index, name='index'),
]
