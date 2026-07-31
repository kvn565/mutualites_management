from django import forms
from core.models import Utilisateur
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class UtilisateurForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ('username', 'nom', 'postnom', 'prenom', 'telephone', 'role', 'actif', 'photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['actif'].widget.attrs['class'] = 'form-check-input'


class UtilisateurEditForm(UserChangeForm):
    password = None # We don't want to change password here
    
    class Meta:
        model = Utilisateur
        fields = ('username', 'nom', 'postnom', 'prenom', 'telephone', 'role', 'actif', 'photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'actif':
                field.widget.attrs['class'] = 'form-control'
        self.fields['actif'].widget.attrs['class'] = 'form-check-input'

class InscriptionChefForm(forms.Form):
    nif = forms.CharField(max_length=50, label="NIF de la Mutualité", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 4000123456'}))
    province = forms.CharField(max_length=100, required=False, label="Province", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Bujumbura'}))
    commune = forms.CharField(max_length=100, required=False, label="Commune", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Mukaza'}))
    quartier = forms.CharField(max_length=100, required=False, label="Quartier", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Rohero'}))
    adresse = forms.CharField(required=False, label="Adresse", widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ex : Avenue de la Plage, 12'}))
    telephone = forms.CharField(max_length=50, required=False, label="Téléphone", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+257 XX XX XX XX'}))
    nom_gerant = forms.CharField(max_length=100, label="Votre nom", widget=forms.TextInput(attrs={'class': 'form-control'}))
    prenom_gerant = forms.CharField(max_length=100, label="Votre prénom", widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=150, label="Nom d'utilisateur", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, label="Votre email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(label="Confirmez le mot de passe", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        nif = cleaned_data.get('nif')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Les mots de passe ne correspondent pas.")

        if nif:
            from core.models import Mutualite
            from django.utils import timezone
            mutualite = Mutualite.objects.filter(nif=nif).first()
            if not mutualite:
                self.add_error('nif', "Aucune mutualité trouvée avec ce NIF. Veuillez contacter l'administrateur.")
            else:
                if mutualite.inscription_complete:
                    self.add_error('nif', "Cette mutualité est déjà gérée par un administrateur.")
                elif not mutualite.licence_valide:
                    self.add_error('nif', "Cette mutualité n'a pas de licence active ou sa période d'essai a expiré.")
                else:
                    cleaned_data['_mutualite'] = mutualite
        return cleaned_data
