# comptabilite/forms.py
from django import forms
from .models import Compte, Transaction, Ecriture
from django.forms import inlineformset_factory

class CompteForm(forms.ModelForm):
    class Meta:
        model = Compte
        fields = ['numero', 'intitule', 'type_compte', 'solde_initial', 'description', 'actif']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'intitule': forms.TextInput(attrs={'class': 'form-control'}),
            'type_compte': forms.Select(attrs={'class': 'form-select'}),
            'solde_initial': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['reference', 'date', 'libelle', 'piece_justificative']
        widgets = {
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'libelle': forms.TextInput(attrs={'class': 'form-control'}),
            'piece_justificative': forms.FileInput(attrs={'class': 'form-control'}),
        }

class EcritureForm(forms.ModelForm):
    class Meta:
        model = Ecriture
        fields = ['compte', 'type_mouvement', 'montant', 'libelle_ligne']
        widgets = {
            'compte': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'type_mouvement': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'libelle_ligne': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }

EcritureFormSet = inlineformset_factory(Transaction, Ecriture, form=EcritureForm, extra=2, can_delete=True)
