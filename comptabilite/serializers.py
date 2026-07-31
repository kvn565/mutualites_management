from rest_framework import serializers
from .models import Compte, CentreAnalytique, Ecriture, Budget, LigneBudget, \
    PrevisionTresorerie, RapprochementBancaire


class CompteSerializer(serializers.ModelSerializer):
    solde = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Compte
        fields = ['id', 'numero', 'intitule', 'type_compte', 'categorie_syscohada',
                   'solde_initial', 'solde', 'compte_parent', 'actif']


class CentreAnalytiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentreAnalytique
        fields = '__all__'


class EcritureSerializer(serializers.ModelSerializer):
    compte_numero = serializers.CharField(source='compte.numero', read_only=True)
    compte_intitule = serializers.CharField(source='compte.intitule', read_only=True)

    class Meta:
        model = Ecriture
        fields = ['id', 'date', 'piece_reference', 'compte', 'compte_numero',
                   'compte_intitule', 'type_mouvement', 'montant', 'libelle',
                   'centre', 'origine', 'statut', 'date_validation',
                   'date_creation', 'date_modification']


class LigneBudgetSerializer(serializers.ModelSerializer):
    compte_numero = serializers.CharField(source='compte.numero', read_only=True)

    class Meta:
        model = LigneBudget
        fields = ['id', 'compte', 'compte_numero', 'montant_prevu',
                   'montant_realise', 'ecart', 'taux']


class BudgetSerializer(serializers.ModelSerializer):
    lignes = LigneBudgetSerializer(many=True, read_only=True)
    total_prevu = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_realise = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    taux_execution = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Budget
        fields = ['id', 'annee', 'type_budget', 'centre', 'statut',
                   'total_prevu', 'total_realise', 'taux_execution', 'lignes']


class PrevisionTresorerieSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrevisionTresorerie
        fields = '__all__'


class RapprochementBancaireSerializer(serializers.ModelSerializer):
    ecart = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = RapprochementBancaire
        fields = ['id', 'compte', 'date_debut', 'date_fin', 'solde_comptable',
                   'solde_bancaire', 'solde_ajuste', 'ecart', 'statut']
