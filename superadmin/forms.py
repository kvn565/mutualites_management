from django import forms
from django.contrib.auth import get_user_model
from core.models import Mutualite, ConfigurationApp
from partenaires.models import Partenaire, UtilisateurPartenaire, Convention

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
            'module_chambres_actif',
        ]
        widgets = {
            'nif': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 4000123456'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control'}),
            'type_mutuelite': forms.Select(attrs={'class': 'form-select'}),
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
            'module_chambres_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nif': 'NIF (Numéro d\'Identification Fiscale)',
            'nom': 'Nom de la mutualité / Établissement',
            'sigle': 'Sigle / Abréviation',
        }


class SuperAdminPartenaireForm(forms.ModelForm):
    class Meta:
        model = Partenaire
        fields = [
            'code_partenaire', 'type_partenaire', 'nom_etablissement',
            'nif', 'numero_agrement', 'assujetti_tva', 'logo',
            'mutualite', 'statut',
            'province', 'commune', 'zone', 'colline', 'adresse_complete',
            'telephone', 'telephone_secondaire', 'email', 'site_web',
            'nom_responsable', 'fonction_responsable',
            'telephone_responsable', 'email_responsable',
            'date_debut_convention', 'date_fin_convention',
            'taux_prise_en_charge', 'plafond_couverture', 'observations',
        ]
        widgets = {
            'code_partenaire': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'type_partenaire': forms.Select(attrs={'class': 'form-select'}),
            'nom_etablissement': forms.TextInput(attrs={'class': 'form-control'}),
            'nif': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_agrement': forms.TextInput(attrs={'class': 'form-control'}),
            'assujetti_tva': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'mutualite': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'zone': forms.TextInput(attrs={'class': 'form-control'}),
            'colline': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse_complete': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_secondaire': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'site_web': forms.URLInput(attrs={'class': 'form-control'}),
            'nom_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'email_responsable': forms.EmailInput(attrs={'class': 'form-control'}),
            'date_debut_convention': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_convention': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'taux_prise_en_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'plafond_couverture': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mutualite'].queryset = Mutualite.objects.all().order_by('nom')
        self.fields['mutualite'].empty_label = "— Aucune mutualité —"
        self.fields['code_partenaire'].required = False


class SuperAdminUtilisateurPartenaireForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Mot de passe',
        required=False,
        help_text='Requis lors de la création. Laissez vide pour conserver.',
    )

    class Meta:
        model = UtilisateurPartenaire
        fields = ['username', 'password', 'role', 'email', 'telephone', 'actif']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['password'].required = False
            self.fields['password'].help_text = 'Laissez vide pour conserver le mot de passe actuel.'
        else:
            self.fields['password'].required = True
            self.fields['password'].help_text = 'Mot de passe pour le nouveau compte (min. 6 caractères).'

    def save(self, commit=True):
        instance = super().save(commit=False)
        pwd = self.cleaned_data.get('password')
        if pwd:
            from django.contrib.auth.hashers import make_password
            instance.password = make_password(pwd)
        if commit:
            instance.save()
        return instance


class SuperAdminConventionForm(forms.ModelForm):
    class Meta:
        model = Convention
        fields = [
            'mutualite', 'numero_convention', 'date_debut', 'date_fin',
            'statut', 'taux_prise_en_charge', 'plafond_couverture', 'observations',
        ]
        widgets = {
            'mutualite': forms.Select(attrs={'class': 'form-select'}),
            'numero_convention': forms.TextInput(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'taux_prise_en_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'plafond_couverture': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mutualite'].queryset = Mutualite.objects.all().order_by('nom')


class ConfigurationAppForm(forms.ModelForm):
    class Meta:
        model = ConfigurationApp
        fields = ['nom_app', 'logo_app', 'favicon', 'primary_color', 'accent_color', 'background_color', 'background_image', 'background_opacity', 'background_brightness', 'text_color']
        widgets = {
            'nom_app': forms.TextInput(attrs={'class': 'form-control'}),
            'logo_app': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'favicon': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'background_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'background_opacity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05', 'min': '0', 'max': '1'}),
            'background_brightness': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05', 'min': '0', 'max': '2'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'height:42px;padding:4px;'}),
            'accent_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'height:42px;padding:4px;'}),
            'background_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'height:42px;padding:4px;'}),
            'text_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'height:42px;padding:4px;'}),
        }

