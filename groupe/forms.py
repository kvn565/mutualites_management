from django import forms
from .models import Groupe


class GroupeForm(forms.ModelForm):
    class Meta:
        model = Groupe
        fields = ['nom', 'description', 'membres']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Comptabilité'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description du groupe...'}),
            'membres': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 10}),
        }
        labels = {
            'nom': 'Nom du groupe',
            'description': 'Description',
            'membres': 'Membres',
        }
