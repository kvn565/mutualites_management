# ventilations/urls.py
from django.urls import path
from . import views

app_name = 'ventilations'

urlpatterns = [
    path('', views.index, name='index'),
]
