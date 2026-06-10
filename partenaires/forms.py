from django import forms
from .models import Partenaire


class PartenaireForm(forms.ModelForm):
    class Meta:
        model = Partenaire
        fields = [
            'code_partenaire', 'type_partenaire', 'nom_etablissement',
            'nif', 'numero_agrement',
            'province', 'commune', 'zone', 'colline', 'adresse_complete',
            'telephone', 'telephone_secondaire', 'email', 'site_web',
            'nom_responsable', 'fonction_responsable',
            'telephone_responsable', 'email_responsable',
            'date_debut_convention', 'date_fin_convention',
            'taux_prise_en_charge', 'plafond_couverture', 'observations',
            'statut',
        ]
        widgets = {
            'code_partenaire': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'type_partenaire': forms.Select(attrs={'class': 'form-select'}),
            'nom_etablissement': forms.TextInput(attrs={'class': 'form-control'}),
            'nif': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_agrement': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'zone': forms.TextInput(attrs={'class': 'form-control'}),
            'colline': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse_complete': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_secondaire': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'site_web': forms.URLInput(attrs={'class': 'form-control'}),
            'nom_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'email_responsable': forms.EmailInput(attrs={'class': 'form-control'}),
            'date_debut_convention': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_convention': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'taux_prise_en_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'plafond_couverture': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }
