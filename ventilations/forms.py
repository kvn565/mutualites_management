from django import forms
from django.utils import timezone
from .models import Branche, RegleVentilation, Ventilation, VentilationGlobale, LigneVentilationGlobale
from comptabilite.models import CentreAnalytique, Ecriture, Compte


class BrancheForm(forms.ModelForm):
    class Meta:
        model = Branche
        fields = ['code', 'libelle', 'description', 'actif']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'libelle': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RegleVentilationForm(forms.ModelForm):
    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False,
    )
    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False,
    )

    class Meta:
        model = RegleVentilation
        fields = ['libelle', 'type_origine', 'centre', 'branche',
                   'pourcentage', 'appliquer_solde_restant', 'priorite',
                   'actif', 'date_debut', 'date_fin', 'notes']
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control'}),
            'type_origine': forms.Select(attrs={'class': 'form-select'}),
            'centre': forms.Select(attrs={'class': 'form-select'}),
            'branche': forms.Select(attrs={'class': 'form-select'}),
            'pourcentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'appliquer_solde_restant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'priorite': forms.NumberInput(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_pourcentage(self):
        pct = self.cleaned_data['pourcentage']
        if pct <= 0 or pct > 100:
            raise forms.ValidationError("Le pourcentage doit être entre 0 et 100.")
        return pct


class VentilationForm(forms.ModelForm):
    class Meta:
        model = Ventilation
        fields = ['ecriture', 'centre', 'branche', 'pourcentage',
                   'montant', 'type_ventilation', 'statut', 'commentaire']
        widgets = {
            'ecriture': forms.Select(attrs={'class': 'form-select'}),
            'centre': forms.Select(attrs={'class': 'form-select'}),
            'branche': forms.Select(attrs={'class': 'form-select'}),
            'pourcentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'type_ventilation': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        data = super().clean()
        pourcentage = data.get('pourcentage') or 0
        montant = data.get('montant') or 0
        ecriture = data.get('ecriture')

        if pourcentage > 100:
            raise forms.ValidationError("Le pourcentage total ne peut pas dépasser 100%.")

        if ecriture and montant > ecriture.montant:
            raise forms.ValidationError(
                f"Le montant ventilé ({montant}) ne peut pas dépasser "
                f"le montant de l'écriture ({ecriture.montant})."
            )

        if not data.get('centre') and not data.get('branche'):
            raise forms.ValidationError(
                "Veuillez sélectionner au moins un centre analytique ou une branche."
            )

        return data


class VentilationManuelleForm(forms.Form):
    """Formulaire de ventilation manuelle : sélectionne une écriture et répartit sur plusieurs axes."""
    ecriture = forms.ModelChoiceField(
        queryset=Ecriture.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Écriture à ventiler',
    )

    class Meta:
        pass


class LigneVentilationForm(forms.Form):
    centre = forms.ModelChoiceField(
        queryset=CentreAnalytique.objects.none(), required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Centre',
    )
    branche = forms.ModelChoiceField(
        queryset=Branche.objects.none(), required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Branche',
    )
    pourcentage = forms.DecimalField(
        max_digits=7, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='%',
    )


class VentilationGlobaleForm(forms.ModelForm):
    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.now,
    )
    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.now,
    )

    class Meta:
        model = VentilationGlobale
        fields = ['libelle', 'date_debut', 'date_fin', 'montant_total', 'notes']
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control'}),
            'montant_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class FiltreVentilationForm(forms.Form):
    PERIODE_CHOICES = [
        ('1', 'Ce mois'),
        ('3', 'Ce trimestre'),
        ('12', 'Cette année'),
        ('CUSTOM', 'Personnalisée'),
    ]
    periode = forms.ChoiceField(choices=PERIODE_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    date_debut = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=False)
    date_fin = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=False)
    centre = forms.ModelChoiceField(queryset=CentreAnalytique.objects.none(), required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    branche = forms.ModelChoiceField(queryset=Branche.objects.none(), required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    statut = forms.ChoiceField(choices=[('', 'Tous')] + Ventilation.STATUT, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    type_ventilation = forms.ChoiceField(choices=[('', 'Tous')] + Ventilation.TYPE_VENTILATION, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
