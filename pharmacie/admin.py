# pharmacie/admin.py
from django.contrib import admin
from .models import CategorieMedicament, Medicament

@admin.register(CategorieMedicament)
class CategorieMedicamentAdmin(admin.ModelAdmin):
    list_display = ['nom']

@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'dci', 'forme', 'pris_en_charge', 'taux_remboursement', 'prix_reference', 'actif']
    list_filter = ['pris_en_charge', 'forme', 'actif', 'categorie']
    search_fields = ['code', 'nom', 'dci']
