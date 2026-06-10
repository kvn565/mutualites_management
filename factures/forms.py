# factures/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Facture, LigneFacture

class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = [
            'numero', 'date', 'partenaire', 'affilie', 'ayant_droit', 
            'diagnostic', 'statut', 'fichier_joint', 'notes', 'motif_rejet'
        ]
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'partenaire': forms.Select(attrs={'class': 'form-select'}),
            'affilie': forms.Select(attrs={'class': 'form-select'}),
            'ayant_droit': forms.Select(attrs={'class': 'form-select'}),
            'diagnostic': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'motif_rejet': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fichier_joint': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        
class LigneFactureForm(forms.ModelForm):
    class Meta:
        model = LigneFacture
        fields = ['service', 'designation', 'quantite', 'prix_unitaire', 'taux_applique']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'designation': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'taux_applique': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }

LigneFactureFormSet = inlineformset_factory(
    Facture, LigneFacture, form=LigneFactureForm, 
    extra=1, can_delete=True
)
