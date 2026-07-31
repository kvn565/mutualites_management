from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from factures.models import Facture, LigneFacture
from partenaires.models import Partenaire, UtilisateurPartenaire, DocumentMedical
from pharmacie.models import Medicament


class InscriptionForm(forms.Form):
    type_partenaire = forms.ChoiceField(
        label="Type d'établissement",
        choices=Partenaire.TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'autofocus': True,
        }),
    )
    nif = forms.CharField(
        label="NIF (Numéro d'Identification Fiscale)",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 4000123456',
            'autocomplete': 'off',
        }),
        help_text="Le nom de l'établissement sera rempli automatiquement si le NIF est connu",
    )
    nom_etablissement = forms.CharField(
        label="Nom de l'établissement",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Hôpital Prince Louis Rwagasore',
        }),
    )
    logo = forms.ImageField(
        label='Logo de l\'établissement',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }),
    )
    email = forms.EmailField(
        label="Email de l'établissement",
        help_text="Email de contact principal",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'contact@hopital.bi',
        }),
    )
    telephone = forms.CharField(
        label='Téléphone',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: +257 71 00 00 00',
        }),
    )
    province = forms.CharField(
        label='Province',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Bujumbura',
        }),
    )
    commune = forms.CharField(
        label='Commune',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Mukaza',
        }),
    )
    zone = forms.CharField(
        label='Zone',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Rohero',
        }),
    )
    quartier = forms.CharField(
        label='Quartier',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Ex: Centre-Ville",
        }),
    )
    avenue = forms.CharField(
        label='Avenue',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Avenue de la Révolution',
        }),
    )
    numero = forms.CharField(
        label='Numéro',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Ex: 12",
        }),
    )
    nom_responsable = forms.CharField(
        label='Nom du responsable',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Dr. Jean Dupont',
        }),
    )
    username = forms.CharField(
        label="Nom d'utilisateur",
        help_text="Choisissez un identifiant unique pour vous connecter",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: gestionnaire.hopital',
        }),
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum 6 caractères',
        }),
    )
    confirm_password = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Répétez le mot de passe',
        }),
    )

    def clean_nif(self):
        nif = self.cleaned_data.get('nif', '').strip()
        if nif and Partenaire.all_objects.filter(nif=nif, is_deleted=False).exists():
            raise forms.ValidationError(
                'Ce NIF est déjà utilisé : un établissement est déjà inscrit avec ce numéro. Connectez-vous avec son compte gestionnaire.'
            )
        return nif

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')

        if password and confirm and password != confirm:
            raise ValidationError({'confirm_password': 'Les mots de passe ne correspondent pas.'})

        if password and len(password) < 6:
            raise ValidationError({'password': 'Le mot de passe doit contenir au moins 6 caractères.'})

        username = cleaned.get('username')
        if username:
            if UtilisateurPartenaire.objects.filter(username=username).exists():
                raise ValidationError({
                    'username': "Ce nom d'utilisateur est déjà pris. Choisissez-en un autre.",
                })

        return cleaned

    def save(self, commit=True):
        partenaire = Partenaire(
            type_partenaire=self.cleaned_data['type_partenaire'],
            nif=self.cleaned_data['nif'],
            nom_etablissement=self.cleaned_data['nom_etablissement'],
            logo=self.cleaned_data.get('logo'),
            email=self.cleaned_data.get('email', ''),
            telephone=self.cleaned_data.get('telephone', ''),
            province=self.cleaned_data.get('province', ''),
            commune=self.cleaned_data.get('commune', ''),
            zone=self.cleaned_data.get('zone', ''),
            quartier=self.cleaned_data.get('quartier', ''),
            avenue=self.cleaned_data.get('avenue', ''),
            numero=self.cleaned_data.get('numero', ''),
            nom_responsable=self.cleaned_data.get('nom_responsable', ''),
            statut='EN_ATTENTE',
        )
        partenaire.save()

        user = UtilisateurPartenaire(
            partenaire=partenaire,
            mutualite=None,
            username=self.cleaned_data['username'],
            email=self.cleaned_data.get('email', ''),
            password=self.cleaned_data['password'],
            role='GESTIONNAIRE',
            actif=True,
        )
        user.save()
        return user


class ConnexionForm(forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre nom d\'utilisateur',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre mot de passe',
        }),
    )


class RechercheMembreForm(forms.Form):
    q = forms.CharField(
        label="ID du membre",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Entrez l\'ID (ex: 42 ou MUT-A7K3P9-42)',
            'autofocus': True,
        }),
    )


class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = [
            'numero_dossier_soins', 'date', 'diagnostic', 'notes',
        ]
        widgets = {
            'numero_dossier_soins': forms.TextInput(attrs={
                'class': 'form-control form-control-lg', 'placeholder': 'N° dossier interne',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg', 'type': 'date',
            }),
            'diagnostic': forms.Textarea(attrs={
                'class': 'form-control form-control-lg', 'rows': 4,
                'placeholder': 'Diagnostic ou raison de la consultation',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-lg', 'rows': 3,
                'placeholder': 'Notes additionnelles...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].initial = timezone.now().date()


class FactureSimpleClientForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = [
            'client_nom', 'client_telephone',
            'numero_dossier_soins', 'date', 'diagnostic', 'notes',
        ]
        widgets = {
            'client_nom': forms.TextInput(attrs={
                'class': 'form-control form-control-lg', 'placeholder': 'Nom complet du client',
                'autofocus': True,
            }),
            'client_telephone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg', 'placeholder': 'Ex: +257 71 00 00 00',
            }),
            'numero_dossier_soins': forms.TextInput(attrs={
                'class': 'form-control form-control-lg', 'placeholder': 'N° dossier interne',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg', 'type': 'date',
            }),
            'diagnostic': forms.Textarea(attrs={
                'class': 'form-control form-control-lg', 'rows': 4,
                'placeholder': 'Diagnostic ou raison de la consultation',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-lg', 'rows': 3,
                'placeholder': 'Notes additionnelles...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].initial = timezone.now().date()


class LigneFactureForm(forms.ModelForm):
    class Meta:
        model = LigneFacture
        fields = ['service', 'designation', 'quantite', 'prix_unitaire', 'taux_applique']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'designation': forms.TextInput(attrs={
                'class': 'form-control form-control-lg', 'placeholder': 'Ex: Consultation générale',
            }),
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg', 'min': 1, 'value': 1,
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg', 'min': 0, 'step': 100,
            }),
            'taux_applique': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg', 'min': 0, 'max': 100, 'step': 5,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['taux_applique'].initial = 80


LigneFactureFormSet = forms.inlineformset_factory(
    Facture, LigneFacture,
    form=LigneFactureForm,
    extra=3,
    min_num=1,
    validate_min=True,
    can_delete=True,
)


class DocumentMedicalForm(forms.ModelForm):
    class Meta:
        model = DocumentMedical
        fields = ['type_document', 'fichier', 'description']
        widgets = {
            'type_document': forms.Select(attrs={'class': 'form-select'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Description du document...',
            }),
        }


class PartenaireProfilForm(forms.ModelForm):
    class Meta:
        model = Partenaire
        fields = [
            'logo', 'nif', 'assujetti_tva',
            'telephone', 'telephone_secondaire', 'email', 'site_web',
            'province', 'commune', 'zone', 'quartier', 'avenue', 'numero',
            'adresse_complete',
            'nom_responsable', 'fonction_responsable',
            'telephone_responsable', 'email_responsable',
            'observations',
        ]
        widgets = {
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'nif': forms.TextInput(attrs={'class': 'form-control'}),
            'assujetti_tva': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_secondaire': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'site_web': forms.URLInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'zone': forms.TextInput(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'avenue': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse_complete': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'nom_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'email_responsable': forms.EmailInput(attrs={'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ChangerMotDePasseForm(forms.Form):
    ancien_mot_de_passe = forms.CharField(
        label='Ancien mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Votre mot de passe actuel'}),
    )
    nouveau_mot_de_passe = forms.CharField(
        label='Nouveau mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nouveau mot de passe'}),
        min_length=6,
    )
    confirmer_mot_de_passe = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Répétez le nouveau mot de passe'}),
    )

    def clean(self):
        cleaned = super().clean()
        nouveau = cleaned.get('nouveau_mot_de_passe')
        confirmer = cleaned.get('confirmer_mot_de_passe')
        if nouveau and confirmer and nouveau != confirmer:
            self.add_error('confirmer_mot_de_passe', 'Les mots de passe ne correspondent pas.')
        return cleaned


class InfoCompteForm(forms.ModelForm):
    class Meta:
        model = UtilisateurPartenaire
        fields = ['email', 'telephone', 'photo']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'adresse@email.com'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+257 XX XX XX XX'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class CreerUtilisateurForm(forms.ModelForm):
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Minimum 6 caractères'}),
        min_length=6,
    )

    class Meta:
        model = UtilisateurPartenaire
        fields = ['username', 'email', 'telephone', 'role', 'password', 'photo']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur"}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'adresse@email.com'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+257 XX XX XX XX'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def save(self, commit=True, partenaire=None, mutualite=None):
        user = super().save(commit=False)
        if partenaire:
            user.partenaire = partenaire
        if mutualite:
            user.mutualite = mutualite
        if commit:
            user.save()
        return user


class MedicamentForm(forms.ModelForm):
    class Meta:
        model = Medicament
        fields = [
            'code', 'nom', 'dci', 'categorie', 'forme', 'dosage',
            'pris_en_charge', 'taux_remboursement', 'prix_reference',
            'observations', 'actif'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'dci': forms.TextInput(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'forme': forms.Select(attrs={'class': 'form-select'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'pris_en_charge': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'taux_remboursement': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'prix_reference': forms.NumberInput(attrs={'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
