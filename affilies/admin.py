# affilies/admin.py
from django.contrib import admin
from .models import Affilie

@admin.register(Affilie)
class AffilieAdmin(admin.ModelAdmin):
    list_display = ['numero_affiliation', 'nom', 'prenom', 'sexe', 'type_adhesion', 'statut', 'date_adhesion']
    list_filter = ['statut', 'type_adhesion', 'sexe', 'date_adhesion']
    search_fields = ['numero_affiliation', 'nom', 'prenom', 'telephone', 'email']
    readonly_fields = ['date_creation', 'date_modification']
