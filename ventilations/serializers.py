from rest_framework import serializers
from .models import Branche, RegleVentilation, Ventilation, VentilationHistory, \
    VentilationGlobale, LigneVentilationGlobale
from comptabilite.models import CentreAnalytique


class BrancheSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branche
        fields = '__all__'


class RegleVentilationSerializer(serializers.ModelSerializer):
    centre_code = serializers.CharField(source='centre.code', read_only=True)
    branche_code = serializers.CharField(source='branche.code', read_only=True)

    class Meta:
        model = RegleVentilation
        fields = ['id', 'libelle', 'type_origine', 'centre', 'centre_code',
                   'branche', 'branche_code', 'pourcentage', 'priorite', 'actif']


class VentilationSerializer(serializers.ModelSerializer):
    ecriture_piece = serializers.CharField(source='ecriture.piece_reference', read_only=True)
    ecriture_libelle = serializers.CharField(source='ecriture.libelle', read_only=True)
    ecriture_montant = serializers.DecimalField(source='ecriture.montant', max_digits=15, decimal_places=2, read_only=True)
    centre_code = serializers.CharField(source='centre.code', read_only=True)
    centre_libelle = serializers.CharField(source='centre.libelle', read_only=True)
    branche_code = serializers.CharField(source='branche.code', read_only=True)
    branche_libelle = serializers.CharField(source='branche.libelle', read_only=True)

    class Meta:
        model = Ventilation
        fields = ['id', 'ecriture', 'ecriture_piece', 'ecriture_libelle',
                   'ecriture_montant', 'centre', 'centre_code', 'centre_libelle',
                   'branche', 'branche_code', 'branche_libelle',
                   'pourcentage', 'montant', 'type_ventilation', 'statut',
                   'commentaire', 'date_ventilation']


class VentilationGlobaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VentilationGlobale
        fields = '__all__'
