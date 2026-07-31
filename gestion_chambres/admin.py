from django.contrib import admin
from .models import TypeChambre, Chambre, Hospitalisation, MouvementChambre


@admin.register(TypeChambre)
class TypeChambreAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'tarif_base', 'capacite', 'actif', 'ordre']
    list_filter = ['actif', 'mutualite']
    search_fields = ['code', 'nom', 'description']
    list_editable = ['actif', 'ordre']
    fieldsets = [
        ('Informations', {'fields': ['mutualite', 'code', 'nom', 'description']}),
        ('Tarification & Capacité', {'fields': ['tarif_base', 'capacite', 'equipements']}),
        ('État', {'fields': ['actif', 'ordre']}),
    ]


@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ['numero', 'type_chambre', 'etage', 'aile', 'statut', 'capacite_totale', 'est_disponible']
    list_filter = ['statut', 'type_chambre', 'etage', 'aile', 'mutualite']
    search_fields = ['numero', 'type_chambre__nom', 'observations']
    list_editable = ['statut']
    readonly_fields = ['date_creation', 'date_modification']
    fieldsets = [
        ('Identification', {'fields': ['mutualite', 'numero', 'type_chambre']}),
        ('Localisation', {'fields': ['etage', 'aile']}),
        ('Configuration lits', {'fields': ['lit_principal', 'lits_supplementaires']}),
        ('Statut & Observations', {'fields': ['statut', 'observations']}),
        ('Audit', {'fields': ['date_creation', 'date_modification']}),
    ]

    def capacite_totale(self, obj):
        return obj.capacite_totale
    capacite_totale.short_description = 'Capacité'

    def est_disponible(self, obj):
        return obj.est_disponible
    est_disponible.boolean = True
    est_disponible.short_description = 'Disponible'


@admin.register(Hospitalisation)
class HospitalisationAdmin(admin.ModelAdmin):
    list_display = ['numero_dossier', 'patient_nom', 'patient_prenom', 'chambre', 'statut', 'date_entree', 'date_sortie_reelle', 'duree_sejour', 'cout_estime']
    list_filter = ['statut', 'chambre__type_chambre', 'service', 'mutualite']
    search_fields = ['numero_dossier', 'patient_nom', 'patient_prenom', 'motif_hospitalisation']
    readonly_fields = ['numero_dossier', 'date_creation', 'date_modification', 'duree_sejour', 'cout_estime']
    date_hierarchy = 'date_entree'
    fieldsets = [
        ('Dossier', {'fields': ['mutualite', 'numero_dossier', 'affilie']}),
        ('Patient', {'fields': ['patient_nom', 'patient_prenom', 'patient_sexe', 'patient_date_naissance', 'patient_telephone', 'patient_adresse']}),
        ('Hospitalisation', {'fields': ['chambre', 'date_entree', 'date_sortie_prevue', 'date_sortie_reelle', 'motif_hospitalisation', 'diagnostic_entree', 'diagnostic_sortie']}),
        ('Médical', {'fields': ['medecin_referent', 'service', 'statut', 'mode_sortie']}),
        ('Observations', {'fields': ['observations']}),
        ('Audit', {'fields': ['created_by', 'date_creation', 'date_modification', 'duree_sejour', 'cout_estime']}),
    ]

    def duree_sejour(self, obj):
        return f"{obj.duree_sejour} jour(s)"
    duree_sejour.short_description = 'Durée'

    def cout_estime(self, obj):
        return f"{obj.cout_estime:,.0f} BIF"
    cout_estime.short_description = 'Coût estimé'


@admin.register(MouvementChambre)
class MouvementChambreAdmin(admin.ModelAdmin):
    list_display = ['chambre', 'type_mouvement', 'ancien_statut', 'nouveau_statut', 'date_mouvement', 'utilisateur']
    list_filter = ['type_mouvement', 'chambre__type_chambre', 'mutualite']
    search_fields = ['chambre__numero', 'commentaire']
    readonly_fields = ['date_mouvement']
    date_hierarchy = 'date_mouvement'