# core/forms.py
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate
from .models import Utilisateur


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
    sigle = forms.CharField(
        max_length=20, required=False,
        label='Sigle (optionnel)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex : MSA',
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
