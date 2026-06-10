# pharmacie/forms.py
from django import forms
from .models import Medicament, CategorieMedicament

class MedicamentForm(forms.ModelForm):
    class Meta:
        model = Medicament
        fields = [
            'code', 'nom', 'dci', 'categorie', 'forme', 'dosage',
            'pris_en_charge', 'taux_remboursement', 'prix_reference',
            'observations', 'actif'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'dci': forms.TextInput(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'forme': forms.Select(attrs={'class': 'form-select'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'pris_en_charge': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'taux_remboursement': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'prix_reference': forms.NumberInput(attrs={'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
