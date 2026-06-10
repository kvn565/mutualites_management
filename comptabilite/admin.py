# comptabilite/admin.py
from django.contrib import admin
from .models import Compte, Transaction, Ecriture

class EcritureInline(admin.TabularInline):
    model = Ecriture
    extra = 1

@admin.register(Compte)
class CompteAdmin(admin.ModelAdmin):
    list_display = ['numero', 'intitule', 'type_compte', 'solde_actuel', 'actif']
    list_filter = ['type_compte', 'actif']
    search_fields = ['numero', 'intitule']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'date', 'libelle', 'enregistre_par']
    list_filter = ['date']
    search_fields = ['reference', 'libelle']
    inlines = [EcritureInline]
