# aide/urls.py
from django.urls import path
from . import views

app_name = 'aide'

urlpatterns = [
    path('', views.index, name='index'),
]
