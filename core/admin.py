# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, JournalAudit, HistoriqueConnexion, Mutualite, ConfigurationApp


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ['username', 'nom_complet', 'role', 'email', 'actif', 'date_joined']
    list_filter = ['role', 'actif', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['last_name', 'first_name']

    fieldsets = UserAdmin.fieldsets + (
        ('Informations Mutualité', {
            'fields': ('role', 'telephone', 'photo', 'actif'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Mutualité', {
            'fields': ('role', 'telephone', 'actif'),
        }),
    )


@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    list_display = ['date_action', 'utilisateur', 'action', 'module', 'description']
    list_filter = ['action', 'module', 'date_action']
    search_fields = ['utilisateur__username', 'module', 'description']
    readonly_fields = ['utilisateur', 'action', 'module', 'description', 'objet_type', 'objet_id', 'adresse_ip', 'date_action']
    date_hierarchy = 'date_action'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(HistoriqueConnexion)
class HistoriqueConnexionAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'adresse_ip', 'succes', 'date_connexion', 'date_deconnexion']
    list_filter = ['succes', 'date_connexion']
    search_fields = ['utilisateur__username', 'adresse_ip']
    readonly_fields = ['utilisateur', 'adresse_ip', 'user_agent', 'date_connexion', 'date_deconnexion', 'succes']
    date_hierarchy = 'date_connexion'

    def has_add_permission(self, request):
        return False


@admin.register(Mutualite)
class MutualiteAdmin(admin.ModelAdmin):
    list_display = [
        'code_mutualite', 'nom', 'nif', 'statut', 'type_mutualite',
        'nom_responsable', 'telephone', 'email',
        'essai_gratuit', 'date_fin_essai', 'date_expiration',
    ]
    list_filter = ['statut', 'type_mutualite', 'essai_gratuit', 'province', 'commune']
    search_fields = ['code_mutualite', 'nom', 'nif', 'telephone', 'email', 'nom_responsable']
    readonly_fields = ['code_mutualite', 'date_creation', 'date_modification']
    fieldsets = [
        ('Identification', {
            'fields': ['code_mutualite', 'nif', 'nom', 'sigle', 'type_mutualite', 'statut']
        }),
        ('Responsable', {
            'fields': ['nom_responsable', 'fonction_responsable', 'telephone', 'email']
        }),
        ('Image et signature', {
            'fields': ['logo', 'signature']
        }),
        ('Localisation', {
            'fields': ['province', 'commune', 'adresse']
        }),
        ('Essai gratuit', {
            'fields': ['essai_gratuit', 'date_debut_essai', 'date_fin_essai']
        }),
        ('Licence', {
            'fields': ['cle_activation', 'date_activation', 'date_expiration', 'type_abonnement', 'max_utilisateurs', 'module_chambres_actif']
        }),
        ('Compte administrateur', {
            'fields': ['username_admin', 'email_admin']
        }),
        ('Audit', {
            'fields': ['created_by', 'date_creation', 'date_modification']
        }),
        ('Thème / Apparence', {
            'fields': ['primary_color', 'accent_color', 'background_color', 'text_color', 'background_image', 'background_opacity', 'background_brightness']
        }),
    ]


@admin.register(ConfigurationApp)
class ConfigurationAppAdmin(admin.ModelAdmin):
    list_display = ['nom_app', 'primary_color', 'accent_color', 'background_color', 'text_color']
    fieldsets = [
        ('Informations générales', {
            'fields': ['nom_app', 'logo_app', 'favicon']
        }),
        ('Couleurs', {
            'fields': ['primary_color', 'accent_color', 'background_color', 'text_color']
        }),
        ('Image de fond', {
            'fields': ['background_image', 'background_opacity', 'background_brightness']
        }),
    ]

    def has_add_permission(self, request):
        # Only allow one configuration
        return not ConfigurationApp.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
