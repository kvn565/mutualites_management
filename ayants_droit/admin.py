# ayants_droit/admin.py
from django.contrib import admin
from .models import AyantDroit


@admin.register(AyantDroit)
class AyantDroitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'affilie', 'lien_parente', 'statut', 'age']
    list_filter = ['lien_parente', 'statut', 'sexe']
    search_fields = ['nom', 'prenom', 'affilie__nom', 'affilie__numero_affiliation']
    ordering = ['affilie', 'lien_parente', 'nom']
    raw_id_fields = ['affilie']
