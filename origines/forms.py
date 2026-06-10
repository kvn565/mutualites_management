# origines/forms.py
from django import forms
from .models import Origine

class OrigineForm(forms.ModelForm):
    class Meta:
        model = Origine
        fields = ['nom', 'type_origine', 'description', 'contact', 'telephone', 'email', 'adresse', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type_origine': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
