# aide/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db import models
from django.db.models import Count, Q
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone

from .models import (
    ArticleAide, CategorieAide,
    MessageSuperAdmin, DocumentSuperAdmin, TypeDocumentSuperAdmin
)
from core.models import Utilisateur


class RequireMutualiteMixin:
    def dispatch(self, request, *args, **kwargs):
        self.mutualite = request.user.mutualite
        if not self.mutualite:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, "Aucune mutualité associée à votre compte.")
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.est_super_admin


# ────────────────── Mutualité : Aide locale ──────────────────

class AideIndexView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = CategorieAide
    template_name = 'aide/index.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return CategorieAide.objects.filter(
            mutualite=self.mutualite,
            actif=True
        ).annotate(
            nb_art_publies=Count('articles', filter=Q(articles__publie=True))
        ).order_by('ordre', 'nom')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['articles_recents'] = ArticleAide.objects.filter(
            mutualite=self.mutualite,
            publie=True
        ).select_related('categorie').order_by('-date_modification')[:5]
        ctx['total_articles'] = ArticleAide.objects.filter(
            mutualite=self.mutualite,
            publie=True
        ).count()
        # Documents SuperAdmin publiés pour cette mutualité
        ctx['docs_superadmin'] = DocumentSuperAdmin.objects.filter(
            publie=True
        ).order_by('type_document', 'ordre', '-date_publication')[:10]
        return ctx


class CategorieAideDetailView(LoginRequiredMixin, RequireMutualiteMixin, DetailView):
    model = CategorieAide
    template_name = 'aide/categorie.html'
    context_object_name = 'categorie'

    def get_queryset(self):
        return CategorieAide.objects.filter(mutualite=self.mutualite, actif=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['articles'] = self.object.articles.filter(publie=True).order_by('ordre', 'titre')
        return ctx


class ArticleAideDetailView(LoginRequiredMixin, RequireMutualiteMixin, DetailView):
    model = ArticleAide
    template_name = 'aide/article.html'
    context_object_name = 'article'

    def get_queryset(self):
        return ArticleAide.objects.filter(mutualite=self.mutualite, publie=True).select_related('categorie')


@login_required
def recherche_aide(request):
    query = request.GET.get('q', '').strip()
    articles = []
    if query:
        articles = ArticleAide.objects.filter(
            mutualite=request.user.mutualite,
            publie=True
        ).filter(
            models.Q(titre__icontains=query) |
            models.Q(contenu__icontains=query) |
            models.Q(mots_cles__icontains=query)
        ).select_related('categorie').order_by('-date_modification')[:20]
    return render(request, 'aide/recherche.html', {
        'query': query,
        'articles': articles,
    })


# ────────────────── Mutualité → SuperAdmin : Messages ──────────────────

class MessageSuperAdminListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = MessageSuperAdmin
    template_name = 'aide/message_list.html'
    context_object_name = 'message_list'
    paginate_by = 20

    def get_queryset(self):
        return MessageSuperAdmin.objects.filter(
            mutualite=self.mutualite
        ).select_related('expediteur', 'repondu_par').order_by('-date_creation')


class MessageSuperAdminCreateView(LoginRequiredMixin, RequireMutualiteMixin, CreateView):
    model = MessageSuperAdmin
    template_name = 'aide/message_form.html'
    fields = ['sujet', 'message']
    success_url = reverse_lazy('aide:message_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['sujet'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Ex: Problème facturation - partenaire Clinique X'
        })
        form.fields['message'].widget.attrs.update({
            'class': 'form-control',
            'rows': 8,
            'style': 'resize:vertical;min-height:180px;',
            'placeholder': 'Décrivez votre problème ou question le plus précisément possible...'
        })
        return form

    def form_valid(self, form):
        form.instance.mutualite = self.mutualite
        form.instance.expediteur = self.request.user
        messages.success(self.request, "Votre message a été envoyé au SuperAdmin.")
        return super().form_valid(form)


class MessageSuperAdminDetailView(LoginRequiredMixin, RequireMutualiteMixin, DetailView):
    model = MessageSuperAdmin
    template_name = 'aide/message_detail.html'
    context_object_name = 'message'

    def get_queryset(self):
        return MessageSuperAdmin.objects.filter(mutualite=self.mutualite).select_related('expediteur', 'repondu_par')


# ────────────────── SuperAdmin : Gestion messages ──────────────────

class SuperAdminMessageListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = MessageSuperAdmin
    template_name = 'aide/superadmin/message_list.html'
    context_object_name = 'message_list'
    paginate_by = 30

    def get_queryset(self):
        qs = MessageSuperAdmin.objects.select_related('mutualite', 'expediteur', 'repondu_par').order_by('-date_creation')
        f = self.request.GET
        if f.get('statut'):
            qs = qs.filter(statut=f['statut'])
        if f.get('mutualite'):
            qs = qs.filter(mutualite_id=f['mutualite'])
        if f.get('q'):
            q = f['q']
            qs = qs.filter(models.Q(sujet__icontains=q) | models.Q(message__icontains=q) | models.Q(mutualite__nom__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['mutualites'] = MessageSuperAdmin.objects.values_list('mutualite__nom', 'mutualite_id').distinct()
        ctx['statuts'] = MessageSuperAdmin.STATUT_CHOICES
        return ctx


class SuperAdminMessageDetailView(LoginRequiredMixin, SuperAdminRequiredMixin, DetailView):
    model = MessageSuperAdmin
    template_name = 'aide/superadmin/message_detail.html'
    context_object_name = 'message'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.statut == 'NOUVEAU':
            obj.statut = 'EN_COURS'
            obj.save(update_fields=['statut'])
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['can_reply'] = self.object.statut != 'FERME'
        return ctx


@login_required
def superadmin_message_repondre(request, pk):
    message = get_object_or_404(MessageSuperAdmin, pk=pk)
    if not request.user.est_super_admin:
        messages.error(request, "Accès refusé.")
        return redirect('aide:index')

    if request.method == 'POST':
        reponse = request.POST.get('reponse', '').strip()
        if reponse:
            message.reponse = reponse
            message.statut = 'REPONDU'
            message.repondu_par = request.user
            message.date_reponse = timezone.now()
            message.save(update_fields=['reponse', 'statut', 'repondu_par', 'date_reponse'])
            messages.success(request, "Réponse envoyée.")
        return redirect('aide:superadmin_message_detail', pk=pk)
    return redirect('aide:superadmin_message_detail', pk=pk)


@login_required
def superadmin_message_changer_statut(request, pk):
    message = get_object_or_404(MessageSuperAdmin, pk=pk)
    if not request.user.est_super_admin:
        messages.error(request, "Accès refusé.")
        return redirect('aide:index')

    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        if nouveau_statut in dict(MessageSuperAdmin.STATUT_CHOICES):
            message.statut = nouveau_statut
            message.save(update_fields=['statut'])
            messages.success(request, "Statut mis à jour.")
    return redirect('aide:superadmin_message_detail', pk=pk)


# ────────────────── SuperAdmin : Documents (Doc/Guide/FAQ) ──────────────────

class SuperAdminDocumentListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = DocumentSuperAdmin
    template_name = 'aide/superadmin/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        qs = DocumentSuperAdmin.objects.select_related('cree_par').order_by('type_document', 'ordre', '-date_publication')
        f = self.request.GET
        if f.get('type'):
            qs = qs.filter(type_document=f['type'])
        if f.get('publie') == '1':
            qs = qs.filter(publie=True)
        elif f.get('publie') == '0':
            qs = qs.filter(publie=False)
        if f.get('q'):
            q = f['q']
            qs = qs.filter(models.Q(titre__icontains=q) | models.Q(contenu__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['types'] = TypeDocumentSuperAdmin.choices
        return ctx


class SuperAdminDocumentCreateView(LoginRequiredMixin, SuperAdminRequiredMixin, CreateView):
    model = DocumentSuperAdmin
    template_name = 'aide/superadmin/document_form.html'
    fields = ['type_document', 'titre', 'slug', 'resume', 'contenu', 'fichier', 'video_url', 'version', 'publie', 'ordre']
    success_url = reverse_lazy('aide:superadmin_document_list')

    def form_valid(self, form):
        form.instance.cree_par = self.request.user
        messages.success(self.request, "Document créé.")
        return super().form_valid(form)


class SuperAdminDocumentUpdateView(LoginRequiredMixin, SuperAdminRequiredMixin, UpdateView):
    model = DocumentSuperAdmin
    template_name = 'aide/superadmin/document_form.html'
    fields = ['type_document', 'titre', 'slug', 'resume', 'contenu', 'fichier', 'video_url', 'version', 'publie', 'ordre']
    success_url = reverse_lazy('aide:superadmin_document_list')

    def form_valid(self, form):
        messages.success(self.request, "Document mis à jour.")
        return super().form_valid(form)


class SuperAdminDocumentDeleteView(LoginRequiredMixin, SuperAdminRequiredMixin, DetailView):
    model = DocumentSuperAdmin
    template_name = 'aide/superadmin/document_confirm_delete.html'
    context_object_name = 'document'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Document supprimé.")
        return redirect('aide:superadmin_document_list')


# ────────────────── Public (toutes mutualités) : Documents SuperAdmin ──────────────────

class SuperAdminDocumentPublicListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = DocumentSuperAdmin
    template_name = 'aide/doc_superadmin_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        qs = DocumentSuperAdmin.objects.filter(publie=True).order_by('type_document', 'ordre', '-date_publication')
        f = self.request.GET
        if f.get('type'):
            qs = qs.filter(type_document=f['type'])
        if f.get('q'):
            q = f['q']
            qs = qs.filter(Q(titre__icontains=q) | Q(contenu__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['types'] = TypeDocumentSuperAdmin.choices
        return ctx


class DocumentSuperAdminPublicListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = DocumentSuperAdmin
    template_name = 'aide/doc_superadmin_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        qs = DocumentSuperAdmin.objects.filter(publie=True).order_by('type_document', 'ordre', '-date_publication')
        f = self.request.GET
        if f.get('type'):
            qs = qs.filter(type_document=f['type'])
        if f.get('q'):
            q = f['q']
            qs = qs.filter(models.Q(titre__icontains=q) | models.Q(contenu__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['types'] = TypeDocumentSuperAdmin.choices
        return ctx


class SuperAdminDocumentPublicDetailView(LoginRequiredMixin, SuperAdminRequiredMixin, DetailView):
    model = DocumentSuperAdmin
    template_name = 'aide/doc_superadmin_detail.html'
    context_object_name = 'document'

    def get_queryset(self):
        return DocumentSuperAdmin.objects.filter(publie=True).select_related('cree_par')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['types'] = TypeDocumentSuperAdmin.choices
        return ctx


class DocumentSuperAdminPublicDetailView(LoginRequiredMixin, RequireMutualiteMixin, DetailView):
    model = DocumentSuperAdmin
    template_name = 'aide/doc_superadmin_detail.html'
    context_object_name = 'document'

    def get_queryset(self):
        return DocumentSuperAdmin.objects.filter(publie=True).select_related('cree_par')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['types'] = TypeDocumentSuperAdmin.choices
        return ctx