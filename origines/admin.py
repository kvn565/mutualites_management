# origines/admin.py
from django.contrib import admin
from .models import Origine

@admin.register(Origine)
class OrigineAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_origine', 'contact', 'telephone', 'actif']
    list_filter = ['type_origine', 'actif']
    search_fields = ['nom', 'contact', 'email']
