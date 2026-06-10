# ayants_droit/forms.py
from django import forms
from .models import AyantDroit


class AyantDroitForm(forms.ModelForm):
    class Meta:
        model = AyantDroit
        fields = ['affilie', 'nom', 'postnom', 'prenom', 'sexe', 'date_naissance',
                  'lien_parente', 'statut', 'telephone', 'notes']
        widgets = {
            'affilie':       forms.Select(attrs={'class': 'form-select'}),
            'nom':           forms.TextInput(attrs={'class': 'form-control'}),
            'postnom':       forms.TextInput(attrs={'class': 'form-control'}),
            'prenom':        forms.TextInput(attrs={'class': 'form-control'}),
            'sexe':          forms.Select(attrs={'class': 'form-select'}),
            'date_naissance':forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lien_parente':  forms.Select(attrs={'class': 'form-select'}),
            'statut':        forms.Select(attrs={'class': 'form-select'}),
            'telephone':     forms.TextInput(attrs={'class': 'form-control'}),
            'notes':         forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
