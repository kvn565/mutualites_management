from django import forms
from django.contrib.auth import get_user_model
from core.models import Mutualite

User = get_user_model()


class SuperAdminUtilisateurForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Mot de passe',
        required=False,
        help_text='Requis uniquement lors de la création. Laissez vide pour conserver le mot de passe actuel.',
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur pour la connexion"}),
        label="Nom d'utilisateur",
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'nom', 'postnom', 'prenom',
            'role', 'mutualite', 'telephone', 'actif',
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'postnom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postnom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'mutualite': forms.Select(attrs={'class': 'form-select'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'mutualite': 'Mutualité',
            'actif': 'Compte actif',
            'nom': 'Nom',
            'postnom': 'Postnom',
            'prenom': 'Prénom',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mutualite'].queryset = Mutualite.objects.all().order_by('nom')
        self.fields['mutualite'].empty_label = "— Aucune mutualité —"
        if self.instance and self.instance.pk:
            self.fields['password'].help_text = 'Laissez vide pour conserver le mot de passe actuel.'
            self.fields['password'].required = False
        else:
            self.fields['password'].required = True
            self.fields['password'].help_text = 'Mot de passe pour le nouveau compte.'

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class MutualiteForm(forms.ModelForm):
    password_admin = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Mot de passe administrateur",
        required=False,
        help_text="Requis uniquement lors de la création.",
    )

    class Meta:
        model = Mutualite
        fields = [
            'nif', 'nom', 'sigle', 'type_mutualite',
            'nom_responsable', 'fonction_responsable', 'telephone', 'email',
            'province', 'commune', 'adresse',
            'username_admin', 'email_admin',
            'max_utilisateurs',
        ]
        widgets = {
            'nif': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 4000123456'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control'}),
            'type_mutualite': forms.Select(attrs={'class': 'form-select'}),
            'nom_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'username_admin': forms.TextInput(attrs={'class': 'form-control'}),
            'email_admin': forms.EmailInput(attrs={'class': 'form-control'}),
            'max_utilisateurs': forms.NumberInput(attrs={'class': 'form-control'}),
        }

