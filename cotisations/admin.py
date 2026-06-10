# cotisations/admin.py
from django.contrib import admin
from .models import Cotisation

@admin.register(Cotisation)
class CotisationAdmin(admin.ModelAdmin):
    list_display = ['reference', 'affilie', 'periode_type', 'mois', 'annee', 'montant', 'statut', 'date_paiement']
    list_filter = ['statut', 'periode_type', 'annee', 'mois', 'mode_paiement']
    search_fields = ['reference', 'affilie__nom', 'affilie__prenom', 'affilie__numero_affiliation']
