# affilies/forms.py
from django import forms
from .models import Affilie

class AffilieForm(forms.ModelForm):
    class Meta:
        model = Affilie
        fields = [
            'numero_affiliation', 'nom', 'postnom', 'prenom', 'sexe',
            'date_naissance', 'etat_civil', 'numero_carte_identite',
            'province', 'commune', 'zone', 'colline', 'adresse',
            'telephone', 'email', 'profession',
            'photo', 'groupe_sanguin',
            'contact_urgence_nom', 'contact_urgence_telephone',
            'centre_sante_reference', 'hopital_reference',
            'date_adhesion', 'type_adhesion', 'section_antenne',
            'origine', 'statut', 'notes',
        ]
        widgets = {
            'numero_affiliation': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'postnom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'etat_civil': forms.Select(attrs={'class': 'form-select'}),
            'numero_carte_identite': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'zone': forms.TextInput(attrs={'class': 'form-control'}),
            'colline': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'groupe_sanguin': forms.Select(attrs={'class': 'form-select'}),
            'contact_urgence_nom': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_urgence_telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'centre_sante_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'hopital_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'date_adhesion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'type_adhesion': forms.Select(attrs={'class': 'form-select'}),
            'section_antenne': forms.TextInput(attrs={'class': 'form-control'}),
            'origine': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
