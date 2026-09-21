# cotisations/forms.py
from django import forms
from .models import Cotisation
from affilies.models import Affilie

class CotisationForm(forms.ModelForm):
    class Meta:
        model = Cotisation
        fields = [
            'affilie', 'reference', 'montant', 'periode_type', 'mois', 'annee',
            'date_emission', 'date_echeance', 'date_paiement', 'statut', 
            'mode_paiement', 'recu_fichier', 'notes'
        ]
        widgets = {
            'affilie': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control'}),
            'periode_type': forms.Select(attrs={'class': 'form-select'}),
            'mois': forms.NumberInput(attrs={'class': 'form-control'}),
            'annee': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_emission': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_echeance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_paiement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
            'recu_fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        mutualite = kwargs.pop('mutualite', None)
        super().__init__(*args, **kwargs)
        if mutualite:
            self.fields['affilie'].queryset = Affilie.objects.filter(
                mutualite=mutualite, supprime=False
            ).order_by('nom', 'prenom')


class RapportPeriodiqueFilterForm(forms.Form):
    MOIS_CHOICES = [
        (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
        (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
        (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre'),
    ]
    
    STATUT_CHOICES = [
        ('TOUS', 'Tous les affiliés'),
        ('ACTIF', 'Affiliés actifs uniquement'),
    ]

    mois_debut = forms.ChoiceField(
        choices=MOIS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mois de début'
    )
    annee_debut = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Année de début'
    )
    mois_fin = forms.ChoiceField(
        choices=MOIS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mois de fin'
    )
    annee_fin = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Année de fin'
    )
    origine = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='Toutes les origines / structures',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Origine / Entreprise'
    )
    statut = forms.ChoiceField(
        choices=STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Statut des affiliés'
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rechercher nom, N° affiliation...'}),
        label='Recherche'
    )

    def __init__(self, *args, **kwargs):
        mutualite = kwargs.pop('mutualite', None)
        super().__init__(*args, **kwargs)
        from origines.models import Origine
        if mutualite:
            self.fields['origine'].queryset = Origine.objects.filter(mutualite=mutualite, actif=True).order_by('nom')
        else:
            self.fields['origine'].queryset = Origine.objects.filter(actif=True).order_by('nom')
