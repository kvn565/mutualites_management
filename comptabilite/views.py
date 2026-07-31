from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
from datetime import date, timedelta
import calendar

from core.models import Mutualite
from .models import Compte, CentreAnalytique, Ecriture, Budget, LigneBudget, \
    PrevisionTresorerie, RapprochementBancaire, LigneRapprochement, AuditComptable
from .forms import (
    CompteForm, CentreAnalytiqueForm, EcritureForm, BudgetForm, LigneBudgetFormSet,
    PrevisionTresorerieForm, RapprochementBancaireForm,
    RapportForm, EcritureValidationForm,
)
from .utils import (
    _audit, comptabiliser_cotisation, comptabiliser_prestation,
    generer_balance, generer_bilan, generer_cpc, exporter_grand_livre,
)


class RequireMutualiteMixin:
    """Attache l'instance mutualite à la vue."""

    def dispatch(self, request, *args, **kwargs):
        self.mutualite = request.user.mutualite
        if not self.mutualite:
            messages.error(request, "Aucune mutualité associée à votre compte.")
            return redirect('index')
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
        _audit(self.mutualite, self.request.user, 'CREATION',
               obj._meta.object_name, obj.pk,
               f"Création {obj._meta.verbose_name}: {obj}")
        return super().form_valid(form)


# ─── Dashboard ───────────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, RequireMutualiteMixin, TemplateView):
    template_name = 'comptabilite/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mutualite = self.mutualite
        today = timezone.now().date()
        first_day = today.replace(day=1)
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])

        ctx['mutualite'] = mutualite

        # KPIs
        ecritures_validees = Ecriture.objects.filter(
            mutualite=mutualite, statut='VALIDE')
        total_debit = ecritures_validees.filter(
            type_mouvement='DEBIT', date__gte=first_day, date__lte=last_day
        ).aggregate(t=Sum('montant'))['t'] or 0
        total_credit = ecritures_validees.filter(
            type_mouvement='CREDIT', date__gte=first_day, date__lte=last_day
        ).aggregate(t=Sum('montant'))['t'] or 0

        ctx['total_debit_mois'] = total_debit
        ctx['total_credit_mois'] = total_credit
        ctx['solde_tresorerie'] = sum(
            c.solde for c in Compte.objects.filter(
                mutualite=mutualite, type_compte='ACTIF', actif=True)
        )

        # En attente
        ctx['ecritures_attente'] = Ecriture.objects.filter(
            mutualite=mutualite, statut='SOUMIS').count()
        ctx['budgets_actifs'] = Budget.objects.filter(
            mutualite=mutualite).exclude(statut='CLOTURE').count()

        # Graphique balances 12 derniers mois
        mois_data = []
        for m in range(12):
            m_date = today.replace(day=1) - timedelta(days=30 * (11 - m))
            deb = ecritures_validees.filter(
                date__year=m_date.year, date__month=m_date.month,
                type_mouvement='DEBIT').aggregate(t=Sum('montant'))['t'] or 0
            cre = ecritures_validees.filter(
                date__year=m_date.year, date__month=m_date.month,
                type_mouvement='CREDIT').aggregate(t=Sum('montant'))['t'] or 0
            mois_data.append({
                'mois': m_date.strftime('%b'),
                'debit': float(deb),
                'credit': float(cre),
            })
        ctx['mois_data'] = mois_data

        # Dernières écritures
        ctx['dernieres_ecritures'] = Ecriture.objects.filter(
            mutualite=mutualite
        ).select_related('compte', 'enregistre_par').order_by('-date_creation')[:10]

        # Budgets en cours
        ctx['budgets_suivi'] = Budget.objects.filter(
            mutualite=mutualite).exclude(statut='CLOTURE'
        ).select_related('centre')[:5]

        return ctx


# ─── Comptes ─────────────────────────────────────────────────────────

class CompteListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = Compte
    template_name = 'comptabilite/compte_list.html'
    context_object_name = 'comptes'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        type_f = self.request.GET.get('type')
        if q:
            qs = qs.filter(Q(numero__icontains=q) | Q(intitule__icontains=q))
        if type_f:
            qs = qs.filter(type_compte=type_f)
        return qs.select_related('compte_parent').order_by('numero')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['types'] = Compte.TYPE_COMPTE
        ctx['total_actif'] = sum(c.solde for c in ctx['comptes'] if c.type_compte == 'ACTIF' if c.solde != 0)
        return ctx


class CompteCreateView(LoginRequiredMixin, RequireMutualiteMixin, CreateView):
    model = Compte
    form_class = CompteForm
    template_name = 'comptabilite/compte_form.html'
    success_url = reverse_lazy('comptabilite:compte_list')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        if self.request.POST:
            kw['data'] = self.request.POST.copy()
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titre'] = "Nouveau compte"
        return ctx


class CompteUpdateView(LoginRequiredMixin, RequireMutualiteMixin, UpdateView):
    model = Compte
    form_class = CompteForm
    template_name = 'comptabilite/compte_form.html'
    success_url = reverse_lazy('comptabilite:compte_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titre'] = f"Modifier {self.object.numero}"
        return ctx


class CompteDeleteView(LoginRequiredMixin, RequireMutualiteMixin, DeleteView):
    model = Compte
    template_name = 'comptabilite/confirm_delete.html'
    success_url = reverse_lazy('comptabilite:compte_list')


# ─── Écritures ───────────────────────────────────────────────────────

class EcritureListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = Ecriture
    template_name = 'comptabilite/ecriture_list.html'
    context_object_name = 'ecritures'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related('compte', 'centre', 'valide_par')
        f = self.request.GET
        if f.get('statut'):
            qs = qs.filter(statut=f['statut'])
        if f.get('type_mvt'):
            qs = qs.filter(type_mouvement=f['type_mvt'])
        if f.get('date_debut'):
            qs = qs.filter(date__gte=f['date_debut'])
        if f.get('date_fin'):
            qs = qs.filter(date__lte=f['date_fin'])
        if f.get('q'):
            qs = qs.filter(
                Q(libelle__icontains=f['q']) |
                Q(piece_reference__icontains=f['q']) |
                Q(compte__numero__icontains=f['q'])
            )
        return qs.order_by('-date', '-id')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['statuts'] = Ecriture.STATUT
        return ctx


class EcritureCreateView(LoginRequiredMixin, RequireMutualiteMixin, CreateView):
    model = Ecriture
    form_class = EcritureForm
    template_name = 'comptabilite/ecriture_form.html'
    success_url = reverse_lazy('comptabilite:ecriture_list')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.mutualite = self.mutualite
        obj.enregistre_par = self.request.user
        if not obj.piece_reference:
            from .utils import _piece_ref
            obj.piece_reference = _piece_ref('EC', self.mutualite)
        if obj.statut == 'SOUMIS' and not obj.piece_reference:
            from .utils import _piece_ref
            obj.piece_reference = _piece_ref('EC', self.mutualite)
        obj.save()
        _audit(self.mutualite, self.request.user, 'CREATION', 'ECRITURE',
               obj.pk, f"Écriture {obj.piece_reference}")
        messages.success(self.request, "Écriture créée avec succès.")
        return redirect(self.success_url)


class EcritureUpdateView(LoginRequiredMixin, RequireMutualiteMixin, UpdateView):
    model = Ecriture
    form_class = EcritureForm
    template_name = 'comptabilite/ecriture_form.html'
    success_url = reverse_lazy('comptabilite:ecriture_list')

    def get_queryset(self):
        return super().get_queryset().filter(statut='BROUILLON')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.date_modification = timezone.now()
        obj.save()
        _audit(self.mutualite, self.request.user, 'MODIFICATION', 'ECRITURE',
               obj.pk, f"Modification écriture {obj.piece_reference}")
        messages.success(self.request, "Écriture modifiée.")
        return redirect(self.success_url)


class EcritureDetailView(LoginRequiredMixin, RequireMutualiteMixin, DetailView):
    model = Ecriture
    template_name = 'comptabilite/ecriture_detail.html'
    context_object_name = 'ecriture'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['validation_form'] = EcritureValidationForm()
        return ctx


class EcritureValidationView(LoginRequiredMixin, RequireMutualiteMixin, FormView):
    form_class = EcritureValidationForm
    http_method_names = ['post']

    def form_valid(self, form):
        ecriture = get_object_or_404(Ecriture, pk=self.kwargs['pk'], mutualite=self.mutualite)
        action = form.cleaned_data['action']
        if action == 'VALIDER' and ecriture.statut == 'SOUMIS':
            ecriture.valider(self.request.user)
            _audit(self.mutualite, self.request.user, 'VALIDATION', 'ECRITURE',
                   ecriture.pk, f"Validation écriture {ecriture.piece_reference}")
            messages.success(self.request, f"Écriture {ecriture.piece_reference} validée.")
        elif action == 'REJETER' and ecriture.statut == 'SOUMIS':
            ecriture.rejeter(self.request.user, form.cleaned_data['motif_rejet'])
            messages.warning(self.request, f"Écriture {ecriture.piece_reference} rejetée.")
        return redirect('comptabilite:ecriture_list')


class EcritureSoumettreView(LoginRequiredMixin, RequireMutualiteMixin, DeleteView):
    """Soumettre une écriture pour validation."""
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        ecriture = get_object_or_404(Ecriture, pk=kwargs['pk'], mutualite=self.mutualite)
        if ecriture.statut == 'BROUILLON':
            ecriture.statut = 'SOUMIS'
            ecriture.save(update_fields=['statut'])
            messages.success(request, "Écriture soumise pour validation.")
        return redirect('comptabilite:ecriture_detail', pk=ecriture.pk)


# ─── Centres Analytiques ────────────────────────────────────────────

class CentreAnalytiqueListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = CentreAnalytique
    template_name = 'comptabilite/centre_list.html'
    context_object_name = 'centres'

    def get_queryset(self):
        return super().get_queryset().order_by('code')


class CentreAnalytiqueCreateView(LoginRequiredMixin, RequireMutualiteMixin, CreateView):
    model = CentreAnalytique
    form_class = CentreAnalytiqueForm
    template_name = 'comptabilite/centre_form.html'
    success_url = reverse_lazy('comptabilite:centre_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titre'] = "Nouveau centre analytique"
        return ctx


# ─── Budgets ─────────────────────────────────────────────────────────

class BudgetListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = Budget
    template_name = 'comptabilite/budget_list.html'
    context_object_name = 'budgets'

    def get_queryset(self):
        return super().get_queryset().select_related('centre').order_by('-annee', 'centre')


class BudgetCreateView(LoginRequiredMixin, RequireMutualiteMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'comptabilite/budget_form.html'
    success_url = reverse_lazy('comptabilite:budget_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['lignes_formset'] = LigneBudgetFormSet(self.request.POST)
        else:
            ctx['lignes_formset'] = LigneBudgetFormSet()
        ctx['titre'] = "Nouveau budget"
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        lignes = ctx['lignes_formset']
        if not lignes.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        self.object = form.save(commit=False)
        self.object.mutualite = self.mutualite
        self.object.enregistre_par = self.request.user
        self.object.save()
        lignes.instance = self.object
        lignes.save()
        _audit(self.mutualite, self.request.user, 'CREATION', 'BUDGET',
               self.object.pk, f"Budget {self.object}")
        return redirect(self.success_url)


class BudgetDetailView(LoginRequiredMixin, RequireMutualiteMixin, DetailView):
    model = Budget
    template_name = 'comptabilite/budget_detail.html'
    context_object_name = 'budget'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['lignes'] = self.object.lignes.select_related('compte').all()
        return ctx


# ─── Trésorerie ──────────────────────────────────────────────────────

class PrevisionListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = PrevisionTresorerie
    template_name = 'comptabilite/prevision_list.html'
    context_object_name = 'previsions'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('compte', 'centre')
        f = self.request.GET
        if f.get('type'):
            qs = qs.filter(type=f['type'])
        if f.get('statut'):
            qs = qs.filter(statut=f['statut'])
        return qs.order_by('date_prevision')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_encaissements'] = super().get_queryset().filter(
            type='ENCAISSEMENT', statut='PREVU'
        ).aggregate(t=Sum('montant'))['t'] or 0
        ctx['total_decaissements'] = super().get_queryset().filter(
            type='DECAISSEMENT', statut='PREVU'
        ).aggregate(t=Sum('montant'))['t'] or 0
        return ctx


class PrevisionCreateView(LoginRequiredMixin, RequireMutualiteMixin, CreateView):
    model = PrevisionTresorerie
    form_class = PrevisionTresorerieForm
    template_name = 'comptabilite/prevision_form.html'
    success_url = reverse_lazy('comptabilite:prevision_list')


# ─── Rapprochement ──────────────────────────────────────────────────

class RapprochementListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = RapprochementBancaire
    template_name = 'comptabilite/rapprochement_list.html'
    context_object_name = 'rapprochements'

    def get_queryset(self):
        return super().get_queryset().select_related('compte').order_by('-date_fin')


class RapprochementCreateView(LoginRequiredMixin, RequireMutualiteMixin, CreateView):
    model = RapprochementBancaire
    form_class = RapprochementBancaireForm
    template_name = 'comptabilite/rapprochement_form.html'
    success_url = reverse_lazy('comptabilite:rapprochement_list')


# ─── Rapports ────────────────────────────────────────────────────────

class RapportView(LoginRequiredMixin, RequireMutualiteMixin, FormView):
    template_name = 'comptabilite/rapport.html'
    form_class = RapportForm
    success_url = reverse_lazy('comptabilite:rapport')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        if self.request.GET:
            kw['data'] = self.request.GET
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Préremplir les centres
        if 'form' in ctx:
            ctx['form'].fields['centre'].queryset = CentreAnalytique.objects.filter(
                mutualite=self.mutualite, actif=True)

        # Résultats si formulaire soumis
        if self.request.GET and self.request.GET.get('type_rapport'):
            ctx['afficher'] = True
            data = self.request.GET
            type_ = data['type_rapport']
            aujourd = timezone.now().date()

            # Période
            periode = data.get('periode', '12')
            if periode == 'CUSTOM':
                debut = self._parse_date(data.get('date_debut'))
                fin = self._parse_date(data.get('date_fin'))
            else:
                debut = aujourd - timedelta(days=30 * int(periode))
                fin = aujourd

            centre = None
            if data.get('centre'):
                centre = get_object_or_404(CentreAnalytique, pk=data['centre'])

            ctx['debut'] = debut
            ctx['fin'] = fin

            if type_ == 'BILAN':
                ctx['rapport_data'] = generer_bilan(self.mutualite, fin)
                ctx['titre_rapport'] = 'Bilan comptable'
                ctx['template_rapport'] = 'comptabilite/rapports/_bilan.html'
            elif type_ == 'CPC':
                ctx['rapport_data'] = generer_cpc(self.mutualite, debut, fin)
                ctx['titre_rapport'] = 'Compte de résultat'
                ctx['template_rapport'] = 'comptabilite/rapports/_cpc.html'
            elif type_ == 'BALANCE':
                ctx['rapport_data'] = generer_balance(self.mutualite, debut, fin, centre)
                ctx['titre_rapport'] = 'Balance des comptes'
                ctx['template_rapport'] = 'comptabilite/rapports/_balance.html'
            elif type_ == 'GRAND_LIVRE':
                ecritures = Ecriture.objects.filter(
                    mutualite=self.mutualite, statut='VALIDE',
                    date__gte=debut, date__lte=fin,
                ).select_related('compte')
                if centre:
                    ecritures = ecritures.filter(centre=centre)
                ctx['ecritures'] = ecritures.order_by('date', 'id')
                ctx['titre_rapport'] = 'Grand livre'
                ctx['template_rapport'] = 'comptabilite/rapports/_grand_livre.html'
            elif type_ == 'JOURNAL':
                ctx['ecritures'] = Ecriture.objects.filter(
                    mutualite=self.mutualite, statut='VALIDE',
                    date__gte=debut, date__lte=fin,
                ).select_related('compte').order_by('date', 'piece_reference')
                ctx['titre_rapport'] = 'Journal général'
                ctx['template_rapport'] = 'comptabilite/rapports/_journal.html'
            elif type_ == 'TRESORERIE':
                tresorerie = Ecriture.objects.filter(
                    mutualite=self.mutualite, statut='VALIDE',
                    date__gte=debut, date__lte=fin,
                    compte__type_compte='ACTIF',
                ).select_related('compte').order_by('date')
                ctx['ecritures'] = tresorerie
                ctx['titre_rapport'] = 'Trésorerie'
                ctx['template_rapport'] = 'comptabilite/rapports/_tresorerie.html'
            elif type_ == 'BUDGET':
                ctx['budgets'] = Budget.objects.filter(
                    mutualite=self.mutualite, annee__gte=debut.year, annee__lte=fin.year,
                ).prefetch_related('lignes__compte')
                ctx['titre_rapport'] = 'Suivi budgétaire'
                ctx['template_rapport'] = 'comptabilite/rapports/_budget.html'

        return ctx

    def _parse_date(self, val):
        if not val:
            return timezone.now().date()
        from datetime import datetime
        return datetime.strptime(val, '%Y-%m-%d').date()


# ─── Export ──────────────────────────────────────────────────────────

class ExportGrandLivreView(LoginRequiredMixin, RequireMutualiteMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        mutualite = self.mutualite
        debut = request.GET.get('debut')
        fin = request.GET.get('fin')
        if not debut or not fin:
            return HttpResponse("Paramètres debut et fin requis.", status=400)
        ecritures = Ecriture.objects.filter(
            mutualite=mutualite, statut='VALIDE',
            date__gte=debut, date__lte=fin,
        ).select_related('compte')
        csv = exporter_grand_livre(ecritures)
        return HttpResponse(csv, content_type='text/csv; charset=utf-8',
                            headers={
                                'Content-Disposition': 'attachment; filename="grand_livre.csv"'})


# ─── Guide d'utilisation ─────────────────────────────────────────────

class GuideView(LoginRequiredMixin, RequireMutualiteMixin, TemplateView):
    template_name = 'comptabilite/guide.html'


class GuidePdfView(LoginRequiredMixin, RequireMutualiteMixin, TemplateView):
    template_name = 'comptabilite/guide.html'

    def get(self, request, *args, **kwargs):
        from django.template.loader import render_to_string
        from weasyprint import HTML
        import tempfile, os

        html = render_to_string(self.template_name, self.get_context_data(), request=request)
        # Version simplifiée pour le PDF (sans barre latérale, sans header/footer)
        html = html.replace(
            '<div class="col-lg-3">', '<div class="col-lg-3" style="display:none;">'
        ).replace(
            'class="btn btn-danger btn-lg"', 'class="btn btn-danger btn-lg" style="display:none;"'
        ).replace(
            'href="javascript:window.print()"', 'href="javascript:window.print()" style="display:none;"'
        )

        import tempfile, os, io
        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_file.close()
        HTML(string=html).write_pdf(pdf_file.name)
        with open(pdf_file.name, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
        try:
            os.unlink(pdf_file.name)
        except PermissionError:
            pass
        response['Content-Disposition'] = 'attachment; filename="guide_comptabilite_ventilation.pdf"'
        return response


# ─── Paiements récents pour JSON ────────────────────────────────────
from decimal import Decimal as D


def recent_transactions_json(request):
    mutualite = request.user.mutualite
    if not mutualite:
        return JsonResponse([], safe=False)
    ecritures = Ecriture.objects.filter(mutualite=mutualite).select_related('compte')[:20]
    data = [{
        'id': e.id,
        'date': str(e.date),
        'libelle': e.libelle,
        'compte': str(e.compte),
        'type': e.type_mouvement,
        'montant': float(e.montant),
        'statut': e.statut,
        'piece': e.piece_reference,
    } for e in ecritures]
    return JsonResponse(data, safe=False)


# ─── Signal : comptabilisation auto depuis cotisation ────────────────
def comptabiliser_depuis_model(objet, utilisateur=None, ip=None):
    """
    Point d'entrée générique : détecte le type et comptabilise.
    """
    from cotisations.models import Cotisation
    if isinstance(objet, Cotisation):
        return comptabiliser_cotisation(objet, utilisateur, ip)
    return []
