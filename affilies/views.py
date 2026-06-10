import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.views.generic import DetailView
from django.views.generic.edit import FormMixin

from core.views import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView, enregistrer_audit

from .models import Affilie
from .forms import AffilieForm
from django.contrib import messages
import openpyxl
from io import BytesIO

logger = logging.getLogger('core.security')


class AffilieListView(CrudListView):
    model = Affilie
    context_object_name = 'affilies'
    module_name = 'affilies'
    search_fields = ['nom', 'postnom', 'prenom', 'numero_affiliation', 'telephone']
    filter_fields = {'statut': 'statut'}
    default_order = '-date_creation'
    list_template = 'affilies/liste.html'
    titre = 'Liste des affiliés'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['statut_choices'] = Affilie.STATUT_CHOICES
        return ctx


class AffilieCreateView(CrudCreateView):
    model = Affilie
    form_class = AffilieForm
    module_name = 'affilies'
    form_template = 'affilies/form.html'
    titre = 'Ajouter un affilié'
    success_message_create = "✅ Affilié {obj.nom_complet} ajouté avec succès."

    def before_save(self, obj):
        if not obj.numero_affiliation:
            obj.numero_affiliation = Affilie.generer_numero()
        obj.cree_par = self.request.user

    def get_initial(self):
        return {'numero_affiliation': Affilie.generer_numero()}


class AffilieDetailView(LoginRequiredMixin, DetailView):
    model = Affilie
    template_name = 'affilies/detail.html'
    context_object_name = 'affilie'

    def get_object(self, queryset=None):
        return get_object_or_404(Affilie, pk=self.kwargs['pk'], supprime=False)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        affilie = self.object
        ctx['ayants_droit'] = []
        ctx['cotisations'] = []
        try:
            ctx['ayants_droit'] = affilie.ayants_droit.filter(supprime=False)
        except Exception as e:
            logger.warning("Erreur chargement ayants_droit: %s", e)
        try:
            ctx['cotisations'] = affilie.cotisations.all().order_by('-date_paiement')[:10]
        except Exception as e:
            logger.warning("Erreur chargement cotisations: %s", e)
        return ctx


class AffilieUpdateView(CrudUpdateView):
    model = Affilie
    form_class = AffilieForm
    module_name = 'affilies'
    form_template = 'affilies/form.html'
    titre = "Modifier l'affilié"
    success_message_update = "✅ Affilié {obj.nom_complet} modifié avec succès."
    success_url = None


class AffilieDeleteView(CrudDeleteView):
    model = Affilie
    module_name = 'affilies'
    confirm_delete_template = 'affilies/confirm_supprimer.html'
    success_message_delete = "🗑️ {obj} a été déplacé vers la corbeille."

    def get_success_url(self):
        from django.urls import reverse
        return reverse('affilies:liste')


@login_required
def export_excel(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    qs = Affilie.objects.filter(supprime=False, mutualite=request.user.mutualite)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Affiliés"
    headers = ['N° Affiliation', 'Nom', 'Prénom', 'Sexe', 'Date Naissance', 'Téléphone', 'Catégorie', 'Statut']
    ws.append(headers)
    for obj in qs:
        ws.append([
            obj.numero_affiliation, obj.nom, obj.prenom, obj.get_sexe_display(),
            obj.date_naissance.strftime('%d/%m/%Y'), obj.telephone,
            obj.get_type_adhesion_display(), obj.get_statut_display()
        ])
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="affilies.xlsx"'
    return response


def export_pdf(request):
    return HttpResponse("Export PDF à implémenter")


def fiche_pdf(request, pk):
    return HttpResponse("Fiche PDF à implémenter")
