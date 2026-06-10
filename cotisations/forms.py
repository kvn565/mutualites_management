# cotisations/forms.py
from django import forms
from .models import Cotisation

class CotisationForm(forms.ModelForm):
    class Meta:
        model = Cotisation
        fields = [
            'affilie', 'reference', 'montant', 'periode_type', 'mois', 'annee',
            'date_emission', 'date_echeance', 'date_paiement', 'statut', 
            'mode_paiement', 'recu_fichier', 'notes'
        ]
        widgets = {
            'affilie': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control'}),
            'periode_type': forms.Select(attrs={'class': 'form-select'}),
            'mois': forms.NumberInput(attrs={'class': 'form-control'}),
            'annee': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_emission': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_echeance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_paiement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
            'recu_fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
