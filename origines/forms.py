# origines/forms.py
from django import forms
from .models import Origine

class OrigineForm(forms.ModelForm):
    class Meta:
        model = Origine
        fields = [
            'nom', 'type_origine', 'description', 'contact', 'telephone', 'email', 'adresse', 'actif',
            'cotisation_mensuelle', 'soins_ambulatoires',
            'limite_laboratoire', 'limite_kinesitherapie', 'limite_reanimation', 'limite_imagerie_medicale',
            'hopital_plafond_chambre', 'hpc_nuit', 'limite_hospitalisation_generale',
            'maternite_forfait', 'pourcentage_maternite',
            'pharmacie_forfait', 'limites_medicaments', 'limites_lunettes', 'limites_dents',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type_origine': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cotisation_mensuelle': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'soins_ambulatoires': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'limite_laboratoire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'limite_kinesitherapie': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'limite_reanimation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'limite_imagerie_medicale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hopital_plafond_chambre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hpc_nuit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'limite_hospitalisation_generale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'maternite_forfait': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pourcentage_maternite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pharmacie_forfait': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'limites_medicaments': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'limites_lunettes': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'limites_dents': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
