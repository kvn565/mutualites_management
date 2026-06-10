# services_sante/admin.py
from django.contrib import admin
from .models import ServiceSante

@admin.register(ServiceSante)
class ServiceSanteAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'categorie', 'taux_prise_en_charge', 'plafond', 'actif']
    list_filter = ['categorie', 'actif']
    search_fields = ['code', 'nom']
