from django import forms
from django.utils import timezone
from .models import Compte, Ecriture, CentreAnalytique, Budget, LigneBudget, PrevisionTresorerie, RapprochementBancaire


class CompteForm(forms.ModelForm):
    class Meta:
        model = Compte
        fields = ['numero', 'intitule', 'type_compte', 'categorie_syscohada',
                   'solde_initial', 'compte_parent', 'description', 'actif']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'intitule': forms.TextInput(attrs={'class': 'form-control'}),
            'type_compte': forms.Select(attrs={'class': 'form-select'}),
            'categorie_syscohada': forms.Select(attrs={'class': 'form-select'}),
            'solde_initial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'compte_parent': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_numero(self):
        numero = self.cleaned_data['numero']
        if len(numero) < 2:
            raise forms.ValidationError("Le code compte doit contenir au moins 2 caractères.")
        return numero


class EcritureForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.now,
    )

    class Meta:
        model = Ecriture
        fields = ['date', 'piece_reference', 'compte', 'type_mouvement',
                   'montant', 'centre', 'libelle', 'statut', 'date_echeance',
                   'piece_jointe', 'notes']
        widgets = {
            'piece_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'compte': forms.Select(attrs={'class': 'form-select'}),
            'type_mouvement': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'centre': forms.Select(attrs={'class': 'form-select'}),
            'libelle': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'date_echeance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'piece_jointe': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_montant(self):
        montant = self.cleaned_data['montant']
        if montant <= 0:
            raise forms.ValidationError("Le montant doit être supérieur à zéro.")
        return montant


class CentreAnalytiqueForm(forms.ModelForm):
    class Meta:
        model = CentreAnalytique
        fields = ['code', 'libelle', 'type_centre', 'actif']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'libelle': forms.TextInput(attrs={'class': 'form-control'}),
            'type_centre': forms.Select(attrs={'class': 'form-select'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EcritureValidationForm(forms.Form):
    action = forms.ChoiceField(
        choices=[('VALIDER', 'Valider'), ('REJETER', 'Rejeter')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    motif_rejet = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Motif du rejet (obligatoire si rejet)'}),
        required=False,
    )

    def clean(self):
        data = super().clean()
        if data.get('action') == 'REJETER' and not data.get('motif_rejet'):
            raise forms.ValidationError("Le motif du rejet est obligatoire.")
        return data


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['annee', 'type_budget', 'centre', 'statut', 'description']
        widgets = {
            'annee': forms.NumberInput(attrs={'class': 'form-control'}),
            'type_budget': forms.Select(attrs={'class': 'form-select'}),
            'centre': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class LigneBudgetForm(forms.ModelForm):
    class Meta:
        model = LigneBudget
        fields = ['compte', 'montant_prevu', 'notes']
        widgets = {
            'compte': forms.Select(attrs={'class': 'form-select'}),
            'montant_prevu': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
        }


LigneBudgetFormSet = forms.inlineformset_factory(
    Budget, LigneBudget, form=LigneBudgetForm,
    extra=3, can_delete=True,
)


class PrevisionTresorerieForm(forms.ModelForm):
    date_prevision = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.now,
    )

    class Meta:
        model = PrevisionTresorerie
        fields = ['date_prevision', 'libelle', 'type', 'montant',
                   'compte', 'centre', 'notes']
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'compte': forms.Select(attrs={'class': 'form-select'}),
            'centre': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RapprochementBancaireForm(forms.ModelForm):
    class Meta:
        model = RapprochementBancaire
        fields = ['compte', 'date_debut', 'date_fin', 'solde_comptable',
                   'solde_bancaire', 'notes']
        widgets = {
            'compte': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'solde_comptable': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'solde_bancaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RapportForm(forms.Form):
    PERIODE = [
        ('3', 'Ce trimestre'),
        ('6', 'Ce semestre'),
        ('12', 'Cette année'),
        ('CUSTOM', 'Personnalisée'),
    ]
    periode = forms.ChoiceField(
        choices=PERIODE, required=False, label='Période',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=False,
    )
    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=False,
    )
    type_rapport = forms.ChoiceField(
        choices=[
            ('BILAN', 'Bilan comptable'),
            ('CPC', 'Compte de résultat (CPC)'),
            ('GRAND_LIVRE', 'Grand livre'),
            ('JOURNAL', 'Journal général'),
            ('BALANCE', 'Balance des comptes'),
            ('TRESORERIE', 'Trésorerie'),
            ('BUDGET', 'Suivi budgétaire'),
        ],
        label='Type de rapport',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    centre = forms.ModelChoiceField(
        queryset=CentreAnalytique.objects.none(), required=False,
        label='Centre analytique (optionnel)',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    format_export = forms.ChoiceField(
        choices=[('HTML', 'Afficher'), ('PDF', 'PDF'), ('EXCEL', 'Excel'), ('CSV', 'CSV')],
        required=False, label='Format',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
