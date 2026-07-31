from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import (
    Compte, CentreAnalytique, Ecriture, Budget, LigneBudget,
    PrevisionTresorerie, RapprochementBancaire, LigneRapprochement,
    AuditComptable,
)


class LigneBudgetInline(admin.TabularInline):
    model = LigneBudget
    extra = 1
    autocomplete_fields = ['compte']


class LigneRapprochementInline(admin.TabularInline):
    model = LigneRapprochement
    extra = 0
    autocomplete_fields = ['ecriture']
    readonly_fields = ['date_pointage']


@admin.register(Compte)
class CompteAdmin(admin.ModelAdmin):
    list_display = ['numero', 'intitule', 'type_compte', 'categorie_syscohada', 'solde_colore', 'actif']
    list_filter = ['type_compte', 'categorie_syscohada', 'actif']
    search_fields = ['numero', 'intitule']
    list_editable = ['actif']
    autocomplete_fields = ['compte_parent']

    def solde_colore(self, obj):
        s = obj.solde
        couleur = 'green' if s >= 0 else 'red'
        return format_html('<strong style="color:{};">{:,.0f} BIF</strong>', couleur, s)
    solde_colore.short_description = 'Solde'

    actions = ['exporter_plan_comptable']

    def exporter_plan_comptable(self, request, queryset):
        from django.http import HttpResponse
        lines = ["Code;Intitulé;Type;Solde"]
        for c in queryset:
            lines.append(f"{c.numero};{c.intitule};{c.type_compte};{c.solde}")
        return HttpResponse("\n".join(lines), content_type="text/csv; charset=utf-8",
                            headers={"Content-Disposition": 'attachment; filename="plan_comptable.csv"'})
    exporter_plan_comptable.short_description = "Exporter le plan comptable (CSV)"


@admin.register(CentreAnalytique)
class CentreAnalytiqueAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'type_centre', 'actif']
    list_filter = ['type_centre', 'actif']
    search_fields = ['code', 'libelle']
    list_editable = ['actif']


@admin.register(Ecriture)
class EcritureAdmin(admin.ModelAdmin):
    list_display = ['date', 'piece_reference', 'compte', 'type_mouvement', 'montant_affiche', 'statut_colore', 'origine']
    list_filter = ['statut', 'type_mouvement', 'origine', 'date']
    search_fields = ['piece_reference', 'libelle', 'compte__numero', 'compte__intitule']
    autocomplete_fields = ['compte', 'centre', 'contrepartie', 'valide_par', 'rejete_par', 'enregistre_par']
    date_hierarchy = 'date'

    def montant_affiche(self, obj):
        return f"{obj.montant:,.0f} BIF"
    montant_affiche.short_description = 'Montant'

    def statut_colore(self, obj):
        couleurs = {
            'BROUILLON': 'gray',
            'SOUMIS': 'orange',
            'VALIDE': 'green',
            'REJETE': 'red',
        }
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            couleurs.get(obj.statut, 'black'),
            obj.get_statut_display(),
        )
    statut_colore.short_description = 'Statut'

    actions = ['valider_ecritures', 'exporter_ecritures']

    def valider_ecritures(self, request, queryset):
        for ecriture in queryset.filter(statut='SOUMIS'):
            ecriture.valider(request.user)
        self.message_user(request, f"{queryset.filter(statut='SOUMIS').count()} écritures validées.")
    valider_ecritures.short_description = "Valider les écritures sélectionnées"

    def exporter_ecritures(self, request, queryset):
        from django.http import HttpResponse
        lines = ["Date;Pièce;Compte;Libellé;Débit;Crédit"]
        for e in queryset:
            debit = str(e.montant) if e.type_mouvement == 'DEBIT' else ''
            credit = str(e.montant) if e.type_mouvement == 'CREDIT' else ''
            lines.append(f"{e.date};{e.piece_reference};{e.compte.numero};{e.libelle};{debit};{credit}")
        return HttpResponse("\n".join(lines), content_type="text/csv; charset=utf-8",
                            headers={"Content-Disposition": 'attachment; filename="ecritures.csv"'})
    exporter_ecritures.short_description = "Exporter les écritures (CSV)"


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['annee', 'type_budget', 'centre', 'statut', 'total_prevu', 'total_realise_colore']
    list_filter = ['statut', 'type_budget', 'annee']
    inlines = [LigneBudgetInline]
    autocomplete_fields = ['centre', 'approuve_par', 'enregistre_par']

    def total_realise_colore(self, obj):
        tx = obj.taux_execution
        couleur = 'green' if tx >= 75 else 'orange' if tx >= 50 else 'red'
        return format_html('<span style="color:{};">{:,.0f} BIF ({:.1f}%)</span>', couleur, obj.total_realise, tx)
    total_realise_colore.short_description = 'Réalisé'


@admin.register(PrevisionTresorerie)
class PrevisionTresorerieAdmin(admin.ModelAdmin):
    list_display = ['date_prevision', 'libelle', 'type', 'montant', 'compte', 'statut']
    list_filter = ['type', 'statut']
    search_fields = ['libelle']
    autocomplete_fields = ['compte', 'centre', 'ecriture']


@admin.register(RapprochementBancaire)
class RapprochementBancaireAdmin(admin.ModelAdmin):
    list_display = ['compte', 'date_debut', 'date_fin', 'solde_comptable', 'solde_bancaire', 'ecart', 'statut_colore']
    list_filter = ['statut']
    autocomplete_fields = ['compte', 'rapproche_par', 'enregistre_par']
    inlines = [LigneRapprochementInline]

    def statut_colore(self, obj):
        couleurs = {'EN_COURS': 'orange', 'EQUILIBRE': 'green', 'ECART': 'red'}
        return format_html(
            '<span style="color:{};">{}</span>',
            couleurs.get(obj.statut, 'black'),
            obj.get_statut_display(),
        )
    statut_colore.short_description = 'Statut'


@admin.register(AuditComptable)
class AuditComptableAdmin(admin.ModelAdmin):
    list_display = ['date_action', 'utilisateur', 'action', 'modele', 'objet_id']
    list_filter = ['action', 'modele', 'date_action']
    search_fields = ['description']
    readonly_fields = list_display + ['description', 'adresse_ip']
    date_hierarchy = 'date_action'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
