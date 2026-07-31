from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Branche, RegleVentilation, Ventilation, VentilationHistory, \
    VentilationGlobale, LigneVentilationGlobale


class LigneVentilationGlobaleInline(admin.TabularInline):
    model = LigneVentilationGlobale
    extra = 1
    autocomplete_fields = ['centre', 'branche']


@admin.register(Branche)
class BrancheAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'actif', 'nb_ventilations']
    list_filter = ['actif']
    search_fields = ['code', 'libelle']
    list_editable = ['actif']

    def nb_ventilations(self, obj):
        return obj.ventilations.count()
    nb_ventilations.short_description = 'Ventilations'


@admin.register(RegleVentilation)
class RegleVentilationAdmin(admin.ModelAdmin):
    list_display = ['libelle', 'type_origine', 'centre', 'branche', 'pourcentage_affiche', 'actif', 'priorite']
    list_filter = ['type_origine', 'actif']
    search_fields = ['libelle']
    list_editable = ['actif', 'priorite']
    autocomplete_fields = ['centre', 'branche', 'enregistre_par']

    def pourcentage_affiche(self, obj):
        return f"{obj.pourcentage}%"
    pourcentage_affiche.short_description = '%'


@admin.register(Ventilation)
class VentilationAdmin(admin.ModelAdmin):
    list_display = ['ecriture_info', 'centre', 'branche', 'pourcentage_affiche', 'montant_affiche', 'type_ventilation', 'statut_colore']
    list_filter = ['statut', 'type_ventilation']
    search_fields = ['ecriture__piece_reference', 'ecriture__libelle']
    autocomplete_fields = ['ecriture', 'centre', 'branche', 'regle', 'enregistre_par']
    date_hierarchy = 'date_ventilation'

    def ecriture_info(self, obj):
        return format_html('<code>{}</code> — {}', obj.ecriture.piece_reference, obj.ecriture.libelle[:50])
    ecriture_info.short_description = 'Écriture'

    def pourcentage_affiche(self, obj):
        return f"{obj.pourcentage}%"
    pourcentage_affiche.short_description = '%'

    def montant_affiche(self, obj):
        return f"{obj.montant:,.0f} BIF"
    montant_affiche.short_description = 'Montant'

    def statut_colore(self, obj):
        couleurs = {'PROVISOIRE': 'orange', 'VALIDEE': 'green', 'ANNULEE': 'red'}
        return format_html('<span style="color:{};">{}</span>',
                           couleurs.get(obj.statut, 'black'), obj.get_statut_display())
    statut_colore.short_description = 'Statut'

    actions = ['valider_ventilations']

    def valider_ventilations(self, request, queryset):
        count = queryset.filter(statut='PROVISOIRE').update(statut='VALIDEE')
        self.message_user(request, f"{count} ventilation(s) validée(s).")
    valider_ventilations.short_description = "Valider les ventilations sélectionnées"


@admin.register(VentilationHistory)
class VentilationHistoryAdmin(admin.ModelAdmin):
    list_display = ['date_action', 'ventilation', 'action', 'utilisateur']
    list_filter = ['action', 'date_action']
    search_fields = ['ventilation__ecriture__piece_reference']
    readonly_fields = [f.name for f in VentilationHistory._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(VentilationGlobale)
class VentilationGlobaleAdmin(admin.ModelAdmin):
    list_display = ['libelle', 'date_debut', 'date_fin', 'montant_total', 'total_ventile', 'solde', 'statut']
    list_filter = ['statut']
    inlines = [LigneVentilationGlobaleInline]

    def solde(self, obj):
        s = obj.solde_a_ventiler
        return format_html('<span style="color:{};">{:,.0f}</span>',
                           'red' if s != 0 else 'green', s)
    solde.short_description = 'Solde'
