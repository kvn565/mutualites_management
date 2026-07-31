from django import forms
from .models import TypeChambre, Chambre, Hospitalisation, MouvementChambre, Etablissement, Service, Soin


class EtablissementForm(forms.ModelForm):
    class Meta:
        model = Etablissement
        fields = ['mutualite', 'code', 'nom', 'sigle', 'type_etablissement', 'adresse', 'ville', 'telephone', 'email', 'directeur', 'autorisation_fonctionnement', 'conventionne', 'taux_prise_en_charge_defaut', 'actif']
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'type_etablissement': forms.Select(attrs={'class': 'form-select'}),
            'conventionne': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'taux_prise_en_charge_defaut': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100', 'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                if 'class' not in field.widget.attrs:
                    if isinstance(field.widget, forms.CheckboxInput):
                        field.widget.attrs.setdefault('class', 'form-check-input')
                    elif isinstance(field.widget, forms.Select):
                        field.widget.attrs.setdefault('class', 'form-select')
                    else:
                        field.widget.attrs.setdefault('class', 'form-control')


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['mutualite', 'etablissement', 'code', 'nom', 'description', 'specialite', 'responsable', 'telephone', 'email', 'etage', 'aile', 'actif', 'ordre']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'etablissement': forms.Select(attrs={'class': 'form-select'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        mutualite = kwargs.pop('mutualite', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                if 'class' not in field.widget.attrs:
                    if isinstance(field.widget, forms.CheckboxInput):
                        field.widget.attrs.setdefault('class', 'form-check-input')
                    elif isinstance(field.widget, forms.Select):
                        field.widget.attrs.setdefault('class', 'form-select')
                    else:
                        field.widget.attrs.setdefault('class', 'form-control')
        if mutualite:
            self.fields['etablissement'].queryset = Etablissement.objects.filter(mutualite=mutualite, actif=True)
        else:
            self.fields['etablissement'].queryset = Etablissement.objects.none()


class TypeChambreForm(forms.ModelForm):
    class Meta:
        model = TypeChambre
        fields = ['mutualite', 'code', 'nom', 'description', 'tarif_base', 'capacite', 'equipements', 'actif', 'ordre']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'equipements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'tarif_base': forms.NumberInput(attrs={'step': '100', 'min': '0', 'class': 'form-control'}),
            'capacite': forms.NumberInput(attrs={'min': '1', 'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                if 'class' not in field.widget.attrs:
                    if isinstance(field.widget, forms.CheckboxInput):
                        field.widget.attrs.setdefault('class', 'form-check-input')
                    elif isinstance(field.widget, forms.Select):
                        field.widget.attrs.setdefault('class', 'form-select')
                    else:
                        field.widget.attrs.setdefault('class', 'form-control')


class ChambreForm(forms.ModelForm):
    class Meta:
        model = Chambre
        fields = ['mutualite', 'etablissement', 'service', 'type_chambre', 'numero', 'etage', 'aile', 'lit_principal', 'lits_supplementaires', 'equipements', 'statut', 'observations']
        widgets = {
            'observations': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'equipements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'lits_supplementaires': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'etablissement': forms.Select(attrs={'class': 'form-select'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'type_chambre': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        mutualite = kwargs.pop('mutualite', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                if 'class' not in field.widget.attrs:
                    if isinstance(field.widget, forms.CheckboxInput):
                        field.widget.attrs.setdefault('class', 'form-check-input')
                    elif isinstance(field.widget, forms.Select):
                        field.widget.attrs.setdefault('class', 'form-select')
                    else:
                        field.widget.attrs.setdefault('class', 'form-control')
        if mutualite:
            self.fields['etablissement'].queryset = Etablissement.objects.filter(mutualite=mutualite, actif=True)
            self.fields['service'].queryset = Service.objects.filter(mutualite=mutualite, actif=True)
            self.fields['type_chambre'].queryset = TypeChambre.objects.filter(mutualite=mutualite, actif=True)
        else:
            self.fields['etablissement'].queryset = Etablissement.objects.none()
            self.fields['service'].queryset = Service.objects.none()
            self.fields['type_chambre'].queryset = TypeChambre.objects.none()

    def clean_numero(self):
        numero = self.cleaned_data['numero']
        etablissement = self.cleaned_data.get('etablissement')
        qs = Chambre.objects.filter(etablissement=etablissement, numero__iexact=numero)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Une chambre avec ce numéro existe déjà pour cet établissement.")
        return numero


class HospitalisationForm(forms.ModelForm):
    class Meta:
        model = Hospitalisation
        fields = [
            'mutualite', 'etablissement', 'service', 'affilie', 'patient_nom', 'patient_prenom', 'patient_sexe',
            'patient_date_naissance', 'patient_telephone', 'patient_adresse',
            'chambre', 'date_entree', 'date_sortie_prevue', 'motif_hospitalisation',
            'diagnostic_entree', 'soins', 'medecin_referent', 'statut', 'taux_prise_en_charge', 'observations'
        ]
        widgets = {
            'patient_nom': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_sexe': forms.Select(attrs={'class': 'form-select'}),
            'patient_date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'patient_telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_adresse': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'affilie': forms.Select(attrs={'class': 'form-select'}),
            'etablissement': forms.Select(attrs={'class': 'form-select'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'chambre': forms.Select(attrs={'class': 'form-select'}),
            'date_entree': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'date_sortie_prevue': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'motif_hospitalisation': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'diagnostic_entree': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'soins': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'medecin_referent': forms.TextInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'observations': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'taux_prise_en_charge': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        mutualite = kwargs.pop('mutualite', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                # Force proper Bootstrap classes on all fields
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                elif isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = 'form-select'
                elif isinstance(field.widget, forms.Textarea):
                    field.widget.attrs.setdefault('class', 'form-control')
                elif isinstance(field.widget, forms.DateInput) or isinstance(field.widget, forms.DateTimeInput):
                    field.widget.attrs.setdefault('class', 'form-control')
                elif isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.NumberInput) or isinstance(field.widget, forms.EmailInput) or isinstance(field.widget, forms.URLInput) or isinstance(field.widget, forms.PasswordInput):
                    field.widget.attrs.setdefault('class', 'form-control')
                else:
                    field.widget.attrs.setdefault('class', 'form-control')
        if mutualite:
            self.fields['etablissement'].queryset = Etablissement.objects.filter(mutualite=mutualite, actif=True)
            self.fields['service'].queryset = Service.objects.filter(mutualite=mutualite, actif=True)
            self.fields['chambre'].queryset = Chambre.objects.filter(mutualite=mutualite, statut='LIBRE')
        else:
            self.fields['etablissement'].queryset = Etablissement.objects.none()
            self.fields['service'].queryset = Service.objects.none()
            self.fields['chambre'].queryset = Chambre.objects.none()
            self.fields['service'].queryset = Service.objects.none()
            self.fields['chambre'].queryset = Chambre.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        chambre = cleaned_data.get('chambre')
        date_entree = cleaned_data.get('date_entree')
        date_sortie_prevue = cleaned_data.get('date_sortie_prevue')

        if chambre and chambre.statut != 'LIBRE' and not self.instance.pk:
            raise forms.ValidationError("Cette chambre n'est pas disponible (statut: %s)." % chambre.get_statut_display())

        if date_entree and date_sortie_prevue and date_sortie_prevue <= date_entree:
            raise forms.ValidationError("La date de sortie prévue doit être postérieure à la date d'entrée.")

        return cleaned_data


class HospitalisationSortieForm(forms.ModelForm):
    """Formulaire simplifié pour la sortie d'hospitalisation."""
    class Meta:
        model = Hospitalisation
        fields = ['date_sortie_reelle', 'mode_sortie', 'diagnostic_sortie', 'observations']
        widgets = {
            'date_sortie_reelle': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'mode_sortie': forms.Select(attrs={'class': 'form-select'}),
            'diagnostic_sortie': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = 'form-select'
                elif isinstance(field.widget, forms.Textarea):
                    field.widget.attrs.setdefault('class', 'form-control')
                elif isinstance(field.widget, forms.DateTimeInput):
                    field.widget.attrs.setdefault('class', 'form-control')
                else:
                    field.widget.attrs.setdefault('class', 'form-control')


class SoinForm(forms.ModelForm):
    class Meta:
        model = Soin
        fields = ['mutualite', 'hospitalisation', 'date_heure', 'type_soin', 'description', 'realise_par', 'cout', 'quantite', 'observations']
        widgets = {
            'date_heure': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'type_soin': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'realise_par': forms.Select(attrs={'class': 'form-select'}),
            'cout': forms.NumberInput(attrs={'step': '100', 'min': '0', 'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        mutualite = kwargs.pop('mutualite', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = 'form-select'
                elif isinstance(field.widget, forms.Textarea):
                    field.widget.attrs.setdefault('class', 'form-control')
                elif isinstance(field.widget, forms.DateTimeInput):
                    field.widget.attrs.setdefault('class', 'form-control')
                elif isinstance(field.widget, forms.NumberInput):
                    field.widget.attrs.setdefault('class', 'form-control')
                else:
                    field.widget.attrs.setdefault('class', 'form-control')
        if mutualite:
            self.fields['hospitalisation'].queryset = Hospitalisation.objects.filter(mutualite=mutualite, statut__in=['EN_COURS', 'PROLONGEE'])
        else:
            self.fields['hospitalisation'].queryset = Hospitalisation.objects.none()


class MouvementChambreForm(forms.ModelForm):
    class Meta:
        model = MouvementChambre
        fields = ['chambre', 'hospitalisation', 'type_mouvement', 'ancien_statut', 'nouveau_statut', 'commentaire']
        widgets = {
            'type_mouvement': forms.Select(attrs={'class': 'form-select'}),
            'ancien_statut': forms.Select(attrs={'class': 'form-select'}),
            'nouveau_statut': forms.Select(attrs={'class': 'form-select'}),
            'commentaire': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = 'form-select'
                elif isinstance(field.widget, forms.Textarea):
                    field.widget.attrs.setdefault('class', 'form-control')
                else:
                    field.widget.attrs.setdefault('class', 'form-control')