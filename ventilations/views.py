from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import calendar

from core.models import Utilisateur
from comptabilite.models import Ecriture, CentreAnalytique
from .models import (
    Branche, RegleVentilation, Ventilation, VentilationHistory,
    VentilationGlobale, LigneVentilationGlobale,
)
from .forms import (
    BrancheForm, RegleVentilationForm, VentilationForm,
    VentilationManuelleForm, LigneVentilationForm,
    VentilationGlobaleForm, FiltreVentilationForm,
)
from .utils import (
    ventiler_ecriture, re_ventiler, resumer_ventilations,
    exporter_ventilations_csv, _historique,
)


class RequireMutualiteMixin:
    def dispatch(self, request, *args, **kwargs):
        self.mutualite = request.user.mutualite
        if not self.mutualite:
            messages.error(request, "Aucune mutualité associée.")
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(mutualite=self.mutualite)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.mutualite = self.mutualite
        if hasattr(obj, 'enregistre_par'):
            obj.enregistre_par = self.request.user
        obj.save()
        form.save_m2m() if hasattr(form, 'save_m2m') else None
        return super().form_valid(form)


# ─── Dashboard ────────────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, RequireMutualiteMixin, TemplateView):
    template_name = 'ventilations/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        m = self.mutualite
        today = timezone.now().date()
        debut_mois = today.replace(day=1)
        fin_mois = today.replace(day=calendar.monthrange(today.year, today.month)[1])

        ctx['total_ventile_mois'] = Ventilation.objects.filter(
            mutualite=m, statut='VALIDEE',
            date_ventilation__date__gte=debut_mois,
            date_ventilation__date__lte=fin_mois,
        ).aggregate(t=Sum('montant'))['t'] or 0

        ctx['nb_ventilations_mois'] = Ventilation.objects.filter(
            mutualite=m, statut='VALIDEE',
            date_ventilation__date__gte=debut_mois,
            date_ventilation__date__lte=fin_mois,
        ).count()

        ctx['nb_provisoires'] = Ventilation.objects.filter(
            mutualite=m, statut='PROVISOIRE').count()

        ctx['nb_regles_actives'] = RegleVentilation.objects.filter(
            mutualite=m, actif=True).count()

        # Répartition par centre (pour graphique)
        repartition_centre = Ventilation.objects.filter(
            mutualite=m, statut='VALIDEE',
            date_ventilation__date__gte=debut_mois,
            date_ventilation__date__lte=fin_mois,
        ).values('centre__code', 'centre__libelle').annotate(
            total=Sum('montant')
        ).order_by('-total')[:8]

        ctx['repartition_centre'] = [
            {'code': r['centre__code'] or 'Général',
             'libelle': r['centre__libelle'] or 'Général',
             'total': float(r['total'])}
            for r in repartition_centre
        ]

        # Répartition par branche
        repartition_branche = Ventilation.objects.filter(
            mutualite=m, statut='VALIDEE',
            date_ventilation__date__gte=debut_mois,
            date_ventilation__date__lte=fin_mois,
        ).values('branche__code', 'branche__libelle').annotate(
            total=Sum('montant')
        ).order_by('-total')[:8]

        ctx['repartition_branche'] = [
            {'code': r['branche__code'] or 'Général',
             'libelle': r['branche__libelle'] or 'Général',
             'total': float(r['total'])}
            for r in repartition_branche
        ]

        # Dernières ventilations
        ctx['dernieres_ventilations'] = Ventilation.objects.filter(
            mutualite=m
        ).select_related('ecriture', 'centre', 'branche').order_by('-date_ventilation')[:10]

        # Écritures non ventilées
        ecritures_validees = Ecriture.objects.filter(mutualite=m, statut='VALIDE')
        ecritures_avec_ventilation = Ventilation.objects.filter(
            mutualite=m, statut='VALIDEE'
        ).values_list('ecriture_id', flat=True).distinct()

        ctx['ecritures_non_ventilees'] = ecritures_validees.exclude(
            pk__in=ecritures_avec_ventilation
        ).count()

        return ctx


# ─── Branches ──────────────────────────────────────────────────────────

class BrancheListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = Branche
    template_name = 'ventilations/branche_list.html'
    context_object_name = 'branches'

    def get_queryset(self):
        return super().get_queryset().order_by('code')


class BrancheCreateView(LoginRequiredMixin, RequireMutualiteMixin, CreateView):
    model = Branche
    form_class = BrancheForm
    template_name = 'ventilations/branche_form.html'
    success_url = reverse_lazy('ventilations:branche_list')


class BrancheUpdateView(LoginRequiredMixin, RequireMutualiteMixin, UpdateView):
    model = Branche
    form_class = BrancheForm
    template_name = 'ventilations/branche_form.html'
    success_url = reverse_lazy('ventilations:branche_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titre'] = f"Modifier {self.object.libelle}"
        return ctx


# ─── Règles de ventilation ────────────────────────────────────────────

class RegleListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = RegleVentilation
    template_name = 'ventilations/regle_list.html'
    context_object_name = 'regles'
    paginate_by = 30

    def get_queryset(self):
        return super().get_queryset().select_related('centre', 'branche').order_by('type_origine', 'priorite')


class RegleCreateView(LoginRequiredMixin, RequireMutualiteMixin, CreateView):
    model = RegleVentilation
    form_class = RegleVentilationForm
    template_name = 'ventilations/regle_form.html'
    success_url = reverse_lazy('ventilations:regle_list')


class RegleUpdateView(LoginRequiredMixin, RequireMutualiteMixin, UpdateView):
    model = RegleVentilation
    form_class = RegleVentilationForm
    template_name = 'ventilations/regle_form.html'
    success_url = reverse_lazy('ventilations:regle_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titre'] = f"Modifier {self.object.libelle}"
        return ctx


class RegleDeleteView(LoginRequiredMixin, RequireMutualiteMixin, DeleteView):
    model = RegleVentilation
    template_name = 'ventilations/confirm_delete.html'
    success_url = reverse_lazy('ventilations:regle_list')


# ─── Ventilations ─────────────────────────────────────────────────────

class VentilationListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = Ventilation
    template_name = 'ventilations/ventilation_list.html'
    context_object_name = 'ventilations'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'ecriture__compte', 'centre', 'branche', 'enregistre_par',
        )
        f = self.request.GET
        if f.get('statut'):
            qs = qs.filter(statut=f['statut'])
        if f.get('type_ventilation'):
            qs = qs.filter(type_ventilation=f['type_ventilation'])
        if f.get('centre'):
            qs = qs.filter(centre_id=f['centre'])
        if f.get('branche'):
            qs = qs.filter(branche_id=f['branche'])
        if f.get('date_debut'):
            qs = qs.filter(ecriture__date__gte=f['date_debut'])
        if f.get('date_fin'):
            qs = qs.filter(ecriture__date__lte=f['date_fin'])
        if f.get('q'):
            qs = qs.filter(
                Q(ecriture__piece_reference__icontains=f['q']) |
                Q(ecriture__libelle__icontains=f['q']) |
                Q(commentaire__icontains=f['q'])
            )
        return qs.order_by('-date_ventilation')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filtre_form'] = FiltreVentilationForm(self.request.GET or None)
        if ctx['filtre_form'].fields.get('centre'):
            ctx['filtre_form'].fields['centre'].queryset = CentreAnalytique.objects.filter(
                mutualite=self.mutualite, actif=True)
        if ctx['filtre_form'].fields.get('branche'):
            ctx['filtre_form'].fields['branche'].queryset = Branche.objects.filter(
                mutualite=self.mutualite, actif=True)
        ctx['total_ventile'] = ctx['ventilations'].aggregate(t=Sum('montant'))['t'] or 0
        return ctx


class VentilationCreateView(LoginRequiredMixin, RequireMutualiteMixin, CreateView):
    model = Ventilation
    form_class = VentilationForm
    template_name = 'ventilations/ventilation_form.html'
    success_url = reverse_lazy('ventilations:ventilation_list')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        # Restreindre les choix aux écritures de la mutualité
        if 'data' not in kw:
            kw['initial'] = kw.get('initial', {})
            ecriture_pk = self.request.GET.get('ecriture')
            if ecriture_pk:
                kw['initial']['ecriture'] = ecriture_pk
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'].fields['ecriture'].queryset = Ecriture.objects.filter(
            mutualite=self.mutualite, statut='VALIDE').select_related('compte')
        ctx['form'].fields['centre'].queryset = CentreAnalytique.objects.filter(
            mutualite=self.mutualite, actif=True)
        ctx['form'].fields['branche'].queryset = Branche.objects.filter(
            mutualite=self.mutualite, actif=True)
        return ctx

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.mutualite = self.mutualite
        obj.enregistre_par = self.request.user
        obj.save()
        _historique(obj, 'CREATION', self.request.user)
        messages.success(self.request, "Ventilation créée avec succès.")
        return redirect(self.success_url)


class VentilationUpdateView(LoginRequiredMixin, RequireMutualiteMixin, UpdateView):
    model = Ventilation
    form_class = VentilationForm
    template_name = 'ventilations/ventilation_form.html'
    success_url = reverse_lazy('ventilations:ventilation_list')

    def get_queryset(self):
        return super().get_queryset().filter(statut='PROVISOIRE')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'].fields['ecriture'].queryset = Ecriture.objects.filter(
            mutualite=self.mutualite)
        ctx['form'].fields['centre'].queryset = CentreAnalytique.objects.filter(
            mutualite=self.mutualite, actif=True)
        ctx['form'].fields['branche'].queryset = Branche.objects.filter(
            mutualite=self.mutualite, actif=True)
        ctx['titre'] = "Modifier la ventilation"
        return ctx

    def form_valid(self, form):
        ancien = {
            'pourcentage': self.object.pourcentage,
            'montant': self.object.montant,
            'centre': self.object.centre,
            'branche': self.object.branche,
        }
        obj = form.save(commit=False)
        obj.date_modification = timezone.now()
        obj.save()
        _historique(obj, 'MODIFICATION', self.request.user, ancien)
        messages.success(self.request, "Ventilation modifiée.")
        return redirect(self.success_url)


class VentilationDetailView(LoginRequiredMixin, RequireMutualiteMixin, DetailView):
    model = Ventilation
    template_name = 'ventilations/ventilation_detail.html'
    context_object_name = 'ventilation'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['historique'] = VentilationHistory.objects.filter(
            ventilation=self.object
        ).select_related('utilisateur').order_by('-date_action')[:20]

        # Vérifier que total <= 100%
        total_pct = Ventilation.objects.filter(
            ecriture=self.object.ecriture,
            statut__in=['PROVISOIRE', 'VALIDEE'],
        ).exclude(pk=self.object.pk).aggregate(
            t=Sum('pourcentage')
        )['t'] or 0
        ctx['total_pourcentage_ecriture'] = total_pct + self.object.pourcentage
        return ctx


class VentilationValiderView(LoginRequiredMixin, RequireMutualiteMixin, UpdateView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        ventilation = get_object_or_404(Ventilation, pk=kwargs['pk'], mutualite=self.mutualite)
        if ventilation.statut == 'PROVISOIRE':
            ventilation.statut = 'VALIDEE'
            ventilation.save(update_fields=['statut'])
            _historique(ventilation, 'VALIDATION', request.user)
            messages.success(request, "Ventilation validée.")
        return redirect('ventilations:ventilation_detail', pk=ventilation.pk)


class VentilationAnnulerView(LoginRequiredMixin, RequireMutualiteMixin, UpdateView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        ventilation = get_object_or_404(Ventilation, pk=kwargs['pk'], mutualite=self.mutualite)
        ventilation.statut = 'ANNULEE'
        ventilation.save(update_fields=['statut'])
        _historique(ventilation, 'ANNULATION', request.user)
        messages.warning(request, "Ventilation annulée.")
        return redirect('ventilations:ventilation_detail', pk=ventilation.pk)


# ─── Auto-ventilation ─────────────────────────────────────────────────

class AutoVentilationView(LoginRequiredMixin, RequireMutualiteMixin, TemplateView):
    """Ventile automatiquement toutes les écritures non encore ventilées."""

    def post(self, request, *args, **kwargs):
        ecritures_a_ventiler = Ecriture.objects.filter(
            mutualite=self.mutualite, statut='VALIDE',
        ).exclude(
            pk__in=Ventilation.objects.filter(
                mutualite=self.mutualite, statut__in=['PROVISOIRE', 'VALIDEE'],
            ).values_list('ecriture_id', flat=True)
        )

        compteur = 0
        for ecriture in ecritures_a_ventiler:
            resultats = ventiler_ecriture(ecriture, request.user)
            if resultats:
                compteur += len(resultats)

        messages.success(
            request,
            f"Ventilation automatique terminée : {compteur} ventilation(s) créée(s) "
            f"pour {ecritures_a_ventiler.count()} écriture(s)."
        )
        return redirect('ventilations:ventilation_list')


# ─── Ventilation globale ──────────────────────────────────────────────

class VentilationGlobaleListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = VentilationGlobale
    template_name = 'ventilations/globale_list.html'
    context_object_name = 'globales'

    def get_queryset(self):
        return super().get_queryset().order_by('-date_fin')


class VentilationGlobaleCreateView(LoginRequiredMixin, RequireMutualiteMixin, CreateView):
    model = VentilationGlobale
    form_class = VentilationGlobaleForm
    template_name = 'ventilations/globale_form.html'
    success_url = reverse_lazy('ventilations:globale_list')


class VentilationGlobaleDetailView(LoginRequiredMixin, RequireMutualiteMixin, DetailView):
    model = VentilationGlobale
    template_name = 'ventilations/globale_detail.html'
    context_object_name = 'globale'


# ─── Historique ────────────────────────────────────────────────────────

class HistoriqueListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = VentilationHistory
    template_name = 'ventilations/historique.html'
    context_object_name = 'historiques'
    paginate_by = 50

    def get_queryset(self):
        return VentilationHistory.objects.filter(
            ventilation__mutualite=self.mutualite
        ).select_related(
            'ventilation', 'utilisateur',
            'ancien_centre', 'nouveau_centre',
            'ancienne_branche', 'nouvelle_branche',
        ).order_by('-date_action')


# ─── Rapport analytique ───────────────────────────────────────────────

class RapportAnalytiqueView(LoginRequiredMixin, RequireMutualiteMixin, TemplateView):
    template_name = 'ventilations/rapport.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        m = self.mutualite
        today = timezone.now().date()

        # Période par défaut : cette année
        debut = today.replace(month=1, day=1)
        fin = today

        f = self.request.GET
        if f.get('date_debut'):
            debut = f['date_debut']
        if f.get('date_fin'):
            fin = f['date_fin']

        centre_id = f.get('centre')
        branche_id = f.get('branche')

        centre = None
        branche_obj = None
        if centre_id:
            centre = get_object_or_404(CentreAnalytique, pk=centre_id, mutualite=m)
        if branche_id:
            branche_obj = get_object_or_404(Branche, pk=branche_id, mutualite=m)

        ctx['debut'] = debut
        ctx['fin'] = fin
        ctx['rapport'] = resumer_ventilations(m, debut, fin, centre, branche_obj)

        # Formulaire de filtre
        filtre = FiltreVentilationForm()
        filtre.fields['centre'].queryset = CentreAnalytique.objects.filter(mutualite=m, actif=True)
        filtre.fields['branche'].queryset = Branche.objects.filter(mutualite=m, actif=True)
        ctx['filtre_form'] = filtre

        return ctx


# ─── Export CSV ────────────────────────────────────────────────────────

class ExportVentilationCSVView(LoginRequiredMixin, RequireMutualiteMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        qs = Ventilation.objects.filter(mutualite=self.mutualite).select_related(
            'ecriture', 'centre', 'branche')
        f = request.GET
        if f.get('statut'):
            qs = qs.filter(statut=f['statut'])
        if f.get('date_debut'):
            qs = qs.filter(ecriture__date__gte=f['date_debut'])
        if f.get('date_fin'):
            qs = qs.filter(ecriture__date__lte=f['date_fin'])

        csv_content = exporter_ventilations_csv(qs)
        return HttpResponse(csv_content, content_type='text/csv; charset=utf-8',
                            headers={
                                'Content-Disposition': 'attachment; filename="ventilations.csv"'})

# ─── API légère ────────────────────────────────────────────────────────
from decimal import Decimal as D


def api_ventiler_ecriture(request, ecriture_pk):
    """Endpoint AJAX pour ventiler une écriture spécifique."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    ecriture = get_object_or_404(Ecriture, pk=ecriture_pk, mutualite=request.user.mutualite)
    resultats = ventiler_ecriture(ecriture, request.user)
    return JsonResponse({
        'success': True,
        'nb_ventilations': len(resultats),
        'message': f"{len(resultats)} ventilation(s) créée(s).",
    })


def api_resume_ventilation(request):
    """Endpoint AJAX pour le résumé des ventilations."""
    m = request.user.mutualite
    if not m:
        return JsonResponse({}, status=403)
    today = timezone.now().date()
    debut = today.replace(day=1)
    resume = resumer_ventilations(m, debut, today)
    return JsonResponse({
        'total_ventile': float(resume['total_ventile']),
        'par_centre': [
            {'code': r['centre__code'] or '', 'libelle': r['centre__libelle'] or '',
             'total': float(r['total']), 'pct': float(r['total_pct'])}
            for r in resume['par_centre']
        ],
        'par_branche': [
            {'code': r['branche__code'] or '', 'libelle': r['branche__libelle'] or '',
             'total': float(r['total'])}
            for r in resume['par_branche']
        ],
    })
