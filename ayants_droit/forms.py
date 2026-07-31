# ayants_droit/forms.py
from django import forms
from .models import AyantDroit


class AyantDroitForm(forms.ModelForm):
    class Meta:
        model = AyantDroit
        fields = ['affilie', 'nom', 'postnom', 'prenom', 'sexe', 'date_naissance',
                  'lien_parente', 'age_limite', 'statut', 'telephone', 'numero_identite', 'notes']
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
            'numero_identite': forms.TextInput(attrs={'class': 'form-control'}),
            'age_limite':    forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 120}),
            'notes':         forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['affilie'].queryset = self.fields['affilie'].queryset.filter(
                mutualite=user.mutualite, supprime=False
            )
