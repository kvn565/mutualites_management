from django import forms
from .models import Groupe, Menu


class GroupeForm(forms.ModelForm):
    class Meta:
        model = Groupe
        fields = ['nom', 'description', 'module_chambres_actif', 'membres', 'menus']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Comptabilité'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description du groupe...'}),
            'module_chambres_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'membres': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 10}),
            'menus': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nom': 'Nom du groupe',
            'description': 'Description',
            'module_chambres_actif': 'Activer le module Chambres pour ce groupe',
            'membres': 'Membres',
            'menus': 'Menus autorisés',
        }
