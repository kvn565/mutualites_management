from django.contrib import admin
from .models import Partenaire


@admin.register(Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    list_display = [
        'code_partenaire', 'nom_etablissement', 'type_partenaire',
        'province', 'telephone', 'statut', 'convention_active',
    ]
    list_filter = ['type_partenaire', 'statut', 'province', 'commune']
    search_fields = ['code_partenaire', 'nom_etablissement', 'nif', 'telephone']
    readonly_fields = ['code_partenaire', 'date_creation', 'date_modification']
