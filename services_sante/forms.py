# services_sante/forms.py
from django import forms
from .models import ServiceSante

class ServiceSanteForm(forms.ModelForm):
    class Meta:
        model = ServiceSante
        fields = [
            'code', 'nom', 'categorie', 'description', 
            'taux_prise_en_charge', 'plafond', 'conditions', 'actif'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'taux_prise_en_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'plafond': forms.NumberInput(attrs={'class': 'form-control'}),
            'conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
