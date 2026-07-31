# core/forms.py
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate
from .models import Mutualite, Utilisateur


class ConnexionForm(forms.Form):
    username = forms.CharField(
        label='Nom d\'utilisateur',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur',
            'autofocus': True,
            'id': 'id_username',
        }),
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'id': 'id_password',
        }),
    )
    remember = forms.BooleanField(
        required=False,
        label='Se souvenir de moi',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )


class ProfilForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'email', 'telephone', 'photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone':  forms.TextInput(attrs={'class': 'form-control'}),
            'photo':      forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Prénom',
            'last_name':  'Nom',
            'email':      'Email',
            'telephone':  'Téléphone',
            'photo':      'Photo de profil',
        }


class InscriptionForm(forms.Form):
    nom_mutualite = forms.CharField(
        label='Nom de la mutualité',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex : Mutuelle de Santé ABC',
        }),
    )
    nif = forms.CharField(
        max_length=50, required=False,
        label='NIF (Numéro d\'Identification Fiscale)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex : 4000123456',
        }),
    )
    sigle = forms.CharField(
        max_length=20, required=False,
        label='Sigle (optionnel)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex : MSA',
        }),
    )
    province = forms.CharField(
        max_length=100, required=False,
        label='Province',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex : Bujumbura',
        }),
    )
    commune = forms.CharField(
        max_length=100, required=False,
        label='Commune',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex : Mukaza',
        }),
    )
    quartier = forms.CharField(
        max_length=100, required=False,
        label='Quartier',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex : Rohero',
        }),
    )
    adresse = forms.CharField(
        required=False,
        label='Adresse',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2,
            'placeholder': 'Ex : Avenue de la Plage, 12',
        }),
    )
    telephone = forms.CharField(
        max_length=50, required=False,
        label='Téléphone',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+257 XX XX XX XX',
        }),
    )
    email = forms.EmailField(
        required=False,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'contact@mutualite.bi',
        }),
    )
    prenom_admin = forms.CharField(
        label='Prénom de l\'administrateur',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Jean',
        }),
    )
    nom_admin = forms.CharField(
        label='Nom de l\'administrateur',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dupont',
        }),
    )
    email_admin = forms.EmailField(
        label='Email de l\'administrateur',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'jean.dupont@email.com',
        }),
    )
    username = forms.CharField(
        label='Nom d\'utilisateur',
        help_text='Identifiant de connexion de l\'administrateur',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin_msa',
        }),
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
        }),
    )
    confirm_password = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
        }),
    )

    def clean_nif(self):
        nif = self.cleaned_data.get('nif', '').strip()
        if nif and Mutualite.objects.filter(nif=nif).exists():
            raise forms.ValidationError(
                'Ce NIF est déjà utilisé : une mutualité existe déjà avec ce numéro. Connectez-vous avec son compte administrateur.'
            )
        return nif

    def clean_username(self):
        username = self.cleaned_data['username']
        if Utilisateur.objects.filter(username=username).exists():
            raise forms.ValidationError('Ce nom d\'utilisateur est déjà pris.')
        return username

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if pwd and confirm and pwd != confirm:
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')
        return cleaned


class MotDePasseForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MutualiteParametresForm(forms.ModelForm):
    class Meta:
        model = Mutualite
        fields = [
            'nom', 'sigle', 'type_mutualite',
            'nom_responsable', 'fonction_responsable',
            'telephone', 'email',
            'logo', 'signature',
            'primary_color', 'accent_color', 'background_color', 'background_image',
            'background_opacity', 'background_brightness', 'text_color',
            'province', 'commune', 'quartier', 'adresse',
            'module_chambres_actif',
            'def_cotisation_mensuelle',
            'def_soins_ambulatoires',
            'def_limite_hospitalisation_generale',
            'def_hopital_plafond_chambre',
            'def_hpc_nuit',
            'def_limite_laboratoire',
            'def_limite_imagerie_medicale',
            'def_limite_kinesitherapie',
            'def_limite_reanimation',
            'def_maternite_forfait',
            'def_pourcentage_maternite',
            'def_pharmacie_forfait',
            'def_limites_medicaments',
            'def_limites_lunettes',
            'def_limites_dents',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control'}),
            'type_mutualite': forms.Select(attrs={'class': 'form-select'}),
            'nom_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'signature': forms.FileInput(attrs={'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'height:42px;padding:4px;'}),
            'accent_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'height:42px;padding:4px;'}),
            'background_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'height:42px;padding:4px;'}),
            'background_image': forms.FileInput(attrs={'class': 'form-control'}),
            'background_opacity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05', 'min': '0', 'max': '1'}),
            'background_brightness': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05', 'min': '0', 'max': '2'}),
            'text_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'height:42px;padding:4px;'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'def_cotisation_mensuelle': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_soins_ambulatoires': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_limite_hospitalisation_generale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_hopital_plafond_chambre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_hpc_nuit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_limite_laboratoire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_limite_imagerie_medicale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_limite_kinesitherapie': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_limite_reanimation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_maternite_forfait': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_pourcentage_maternite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_pharmacie_forfait': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_limites_medicaments': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_limites_lunettes': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'def_limites_dents': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'module_chambres_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nom': "Nom de la mutualité",
            'sigle': "Sigle / Abréviation",
            'type_mutualite': "Type de mutualité",
            'nom_responsable': "Nom du responsable",
            'fonction_responsable': "Fonction du responsable",
            'telephone': "Téléphone",
            'email': "Email",
            'logo': "Logo de la mutualité",
            'signature': "Signature du responsable",
            'primary_color': "Couleur principale",
            'accent_color': "Couleur secondaire",
            'background_color': "Couleur de fond",
            'background_image': "Image de fond",
            'background_opacity': "Opacité",
            'background_brightness': "Luminosité",
            'text_color': "Couleur du texte",
            'module_chambres_actif': "Activer module Gestion des Chambres",
            'province': "Province",
            'commune': "Commune",
            'quartier': "Quartier",
            'adresse': "Adresse",
            'def_cotisation_mensuelle': "Cotisation mensuelle (BIF)",
            'def_soins_ambulatoires': "Soins Ambulatoires (BIF)",
            'def_limite_hospitalisation_generale': "Limite Hospitalisation Générale (BIF)",
            'def_hopital_plafond_chambre': "Hôpital plafond chambre/nuit (BIF)",
            'def_hpc_nuit': "HPC / Nuit (BIF)",
            'def_limite_laboratoire': "Limite Laboratoire (BIF)",
            'def_limite_imagerie_medicale': "Limite Imagerie Médicale (BIF)",
            'def_limite_kinesitherapie': "Limite Kinésithérapie (BIF)",
            'def_limite_reanimation': "Limite Réanimation (BIF)",
            'def_maternite_forfait': "Maternité forfait (BIF)",
            'def_pourcentage_maternite': "Pourcentage Maternité (%)",
            'def_pharmacie_forfait': "Pharmacie forfait (BIF)",
            'def_limites_medicaments': "Limites Médicaments (BIF)",
            'def_limites_lunettes': "Limites Lunettes (verre et monture) (BIF)",
            'def_limites_dents': "Limites Soins Dentaires (BIF)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # NIF non modifiable par la mutualité
