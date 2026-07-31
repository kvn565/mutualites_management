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
    fieldsets = [
        ('Identification', {
            'fields': ['code_partenaire', 'mutualite', 'type_partenaire', 'nom_etablissement', 'nif', 'assujetti_tva', 'logo', 'numero_agrement']
        }),
        ('Adresse', {
            'fields': ['province', 'commune', 'zone', 'quartier', 'avenue', 'numero', 'colline', 'adresse_complete']
        }),
        ('Contact', {
            'fields': ['telephone', 'telephone_secondaire', 'email', 'site_web']
        }),
        ('Responsable', {
            'fields': ['nom_responsable', 'fonction_responsable', 'telephone_responsable', 'email_responsable']
        }),
        ('Convention', {
            'fields': ['date_debut_convention', 'date_fin_convention', 'taux_prise_en_charge', 'plafond_couverture', 'observations']
        }),
        ('Thème / Apparence', {
            'fields': ['primary_color', 'accent_color', 'background_color', 'text_color', 'background_image', 'background_opacity', 'background_brightness']
        }),
        ('Statut', {
            'fields': ['statut', 'supprime', 'date_suppression']
        }),
        ('Audit', {
            'fields': ['created_by', 'date_creation', 'date_modification']
        }),
    ]
    fieldsets = [
        ('Identification', {
            'fields': ['code_partenaire', 'mutualite', 'type_partenaire', 'nom_etablissement', 'nif', 'assujetti_tva', 'logo', 'numero_agrement']
        }),
        ('Adresse', {
            'fields': ['province', 'commune', 'zone', 'quartier', 'avenue', 'numero', 'colline', 'adresse_complete']
        }),
        ('Contact', {
            'fields': ['telephone', 'telephone_secondaire', 'email', 'site_web']
        }),
        ('Responsable', {
            'fields': ['nom_responsable', 'fonction_responsable', 'telephone_responsable', 'email_responsable']
        }),
        ('Convention', {
            'fields': ['date_debut_convention', 'date_fin_convention', 'taux_prise_en_charge', 'plafond_couverture', 'observations']
        }),
        ('Thème / Apparence', {
            'fields': ['primary_color', 'accent_color', 'background_color', 'text_color', 'background_image', 'background_opacity', 'background_brightness']
        }),
        ('Statut & Audit', {
            'fields': ['statut', 'created_by', 'date_creation', 'date_modification']
        }),
    ]
