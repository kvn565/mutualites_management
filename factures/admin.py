# factures/admin.py
from django.contrib import admin
from .models import Facture, LigneFacture

class LigneFactureInline(admin.TabularInline):
    model = LigneFacture
    extra = 1

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ['numero', 'date', 'partenaire', 'affilie', 'montant_total', 'statut']
    list_filter = ['statut', 'date', 'partenaire']
    search_fields = ['numero', 'affilie__nom', 'partenaire__nom']
    inlines = [LigneFactureInline]
    readonly_fields = ['date_creation', 'cree_par', 'montant_total', 'montant_ticket_moderateur', 'montant_mutualite']
