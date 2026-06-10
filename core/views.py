import logging
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic.detail import SingleObjectMixin

from core.mixins import ModificationRequiredMixin, MutualiteRequiredMixin
from core.models import JournalAudit, Mutualite, Utilisateur, HistoriqueConnexion, set_current_mutualite

logger = logging.getLogger('core.security')


def landing_view(request):
    from django.shortcuts import redirect
    return redirect('core:login')


def login_view(request):
    from core.forms import ConnexionForm
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.actif:
                    login(request, user)
                    remember = form.cleaned_data.get('remember', False)
                    if not remember:
                        request.session.set_expiry(0)
                    ip = request.META.get('REMOTE_ADDR', '')
                    JournalAudit.objects.create(
                        utilisateur=user, action='CONNEXION', module='core',
                        description=f"Connexion de {user.nom_complet}",
                        adresse_ip=ip,
                        mutualite=user.mutualite,
                    )
                    HistoriqueConnexion.objects.create(
                        utilisateur=user,
                        mutualite=user.mutualite,
                        adresse_ip=ip,
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                        succes=True,
                    )
                    messages.success(request, f"Bienvenue {user.nom_complet} !")
                    if user.est_super_admin:
                        return redirect('superadmin:dashboard')
                    return redirect('dashboard:index')
                else:
                    messages.error(request, "⛔ Ce compte est désactivé.")
            else:
                messages.error(request, "⛔ Identifiants incorrects.")
    else:
        form = ConnexionForm()
    return render(request, 'core/login.html', {'form': form})


def inscription_view(request):
    from .forms import InscriptionForm
    from django.contrib.auth.hashers import make_password
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            mutualite = Mutualite.objects.create(
                nom=data['nom_mutualite'],
                sigle=data.get('sigle', ''),
                telephone=data.get('telephone', ''),
                email=data.get('email', ''),
            )
            admin = Utilisateur.objects.create(
                username=data['username'],
                password=make_password(data['password']),
                first_name=data['prenom_admin'],
                last_name=data['nom_admin'],
                email=data['email_admin'],
                mutualite=mutualite,
                role='ADMIN_MUTUALITE',
                actif=True,
            )
            set_current_mutualite(mutualite)
            JournalAudit.objects.create(
                utilisateur=admin, action='CREATION', module='core',
                description=f"Inscription de la mutualité {mutualite.nom} par {admin.nom_complet}",
                mutualite=mutualite,
            )
            messages.success(
                request,
                f"✅ Mutualité « {mutualite.nom} » créée avec succès ! "
                f"Connectez-vous avec votre nom d'utilisateur.",
            )
            return redirect('core:login')
        else:
            messages.error(request, "⛔ Veuillez corriger les erreurs ci-dessous.")
    else:
        form = InscriptionForm()
    return render(request, 'core/inscription.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        JournalAudit.objects.create(
            utilisateur=request.user, action='DECONNEXION', module='core',
            description=f"Déconnexion de {request.user.nom_complet}",
            adresse_ip=request.META.get('REMOTE_ADDR', ''),
            mutualite=request.user.mutualite,
        )
        logout(request)
    return redirect('core:login')


@login_required
def profil_view(request):
    from .forms import ProfilForm, MotDePasseForm
    user = request.user
    if request.method == 'POST':
        form = ProfilForm(request.POST, request.FILES, instance=user)
        mdp_form = MotDePasseForm(user, request.POST)
        if 'update_profil' in request.POST and form.is_valid():
            form.save()
            messages.success(request, "✅ Profil mis à jour.")
            return redirect('core:profil')
        elif 'change_password' in request.POST and mdp_form.is_valid():
            mdp_form.save()
            messages.success(request, "✅ Mot de passe modifié.")
            return redirect('core:login')
    else:
        form = ProfilForm(instance=user)
        mdp_form = MotDePasseForm(user)
    return render(request, 'core/profil.html', {
        'form': form,
        'mdp_form': mdp_form,
    })


def enregistrer_audit(request, action, module, description, objet_type='', objet_id=None):
    try:
        mutualite = getattr(request.user, 'mutualite', None) if request.user.is_authenticated else None
        JournalAudit.objects.create(
            utilisateur=request.user if request.user.is_authenticated else None,
            action=action,
            module=module,
            description=description,
            objet_type=objet_type,
            objet_id=objet_id,
            adresse_ip=request.META.get('REMOTE_ADDR', ''),
            mutualite=mutualite,
        )
    except Exception as e:
        logger.exception("Erreur lors de l'enregistrement de l'audit: %s", e)


class CrudMixin(MutualiteRequiredMixin):
    """
    Mixin CRUD générique pour standardiser les vues.
    Inclut le blocage Super Admin et l'isolation par mutualité.
    """
    module_name = ''
    search_fields = []
    filter_fields = {}
    default_order = '-date_creation'
    paginate_by = 10
    permission_create = True
    permission_update = True
    permission_delete = True
    soft_delete_field = 'supprime'
    soft_delete = True
    success_message_create = ''
    success_message_update = ''
    success_message_delete = ''
    audit_action_create = 'CREATION'
    audit_action_update = 'MODIFICATION'
    audit_action_delete = 'SUPPRESSION'
    list_template = ''
    form_template = ''
    confirm_delete_template = ''

    def get_queryset(self):
        qs = super().get_queryset()
        if self.soft_delete and hasattr(self.model, self.soft_delete_field):
            qs = qs.filter(**{self.soft_delete_field: False})
        if hasattr(self.model, 'mutualite'):
            qs = qs.filter(mutualite=self.request.user.mutualite)
        return qs.order_by(self.default_order)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titre'] = self.get_titre()
        return ctx

    def get_titre(self):
        return self.titre if hasattr(self, 'titre') else ''

    def can_modify(self, obj):
        return True


class CrudListView(CrudMixin, ListView):
    """
    Vue liste générique avec recherche, filtres et pagination.
    """
    template_name = ''

    def get_template_names(self):
        if self.list_template:
            return [self.list_template]
        if self.model:
            app = self.model._meta.app_label
            model_name = self.model._meta.model_name
            return [f'{app}/{model_name}_liste.html']
        return []

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '')
        if q and self.search_fields:
            filters = Q()
            for field in self.search_fields:
                filters |= Q(**{f'{field}__icontains': q})
            qs = qs.filter(filters)
        for param, field_name in self.filter_fields.items():
            value = self.request.GET.get(param, '')
            if value:
                qs = qs.filter(**{field_name: value})
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        for param in self.filter_fields:
            ctx[param] = self.request.GET.get(param, '')
        ctx['total'] = self.get_queryset().count()
        return ctx


class CrudCreateView(ModificationRequiredMixin, CrudMixin, CreateView):
    """
    Vue création générique avec audit et message.
    """
    template_name = ''

    def get_template_names(self):
        if self.form_template:
            return [self.form_template]
        if self.model:
            app = self.model._meta.app_label
            model_name = self.model._meta.model_name
            return [f'{app}/{model_name}_form.html']
        return []

    def get_success_url(self):
        if hasattr(self, 'success_url') and self.success_url:
            return str(self.success_url)
        if self.object:
            return str(reverse_lazy(f'{self.model._meta.app_label}:detail', kwargs={'pk': self.object.pk}))
        return str(reverse_lazy(f'{self.model._meta.app_label}:liste'))

    def form_valid(self, form):
        obj = form.save(commit=False)
        if hasattr(obj, 'mutualite') and obj.mutualite is None:
            obj.mutualite = getattr(self.request, 'current_mutualite', None)
        self.before_save(obj)
        obj.save()
        enregistrer_audit(
            self.request, self.audit_action_create, self.module_name,
            f"Création : {str(obj)}", self.model.__name__, obj.pk
        )
        messages.success(self.request, self.success_message_create.format(obj=obj))
        return super().form_valid(form)

    def before_save(self, obj):
        pass


class CrudUpdateView(ModificationRequiredMixin, CrudMixin, UpdateView):
    """
    Vue modification générique avec audit et message.
    """
    template_name = ''

    def get_template_names(self):
        if self.form_template:
            return [self.form_template]
        if self.model:
            app = self.model._meta.app_label
            model_name = self.model._meta.model_name
            return [f'{app}/{model_name}_form.html']
        return []

    def get_success_url(self):
        if hasattr(self, 'success_url') and self.success_url:
            return str(self.success_url)
        if self.object:
            return str(reverse_lazy(f'{self.model._meta.app_label}:detail', kwargs={'pk': self.object.pk}))
        return str(reverse_lazy(f'{self.model._meta.app_label}:liste'))

    def form_valid(self, form):
        obj = form.save()
        enregistrer_audit(
            self.request, self.audit_action_update, self.module_name,
            f"Modification : {str(obj)}", self.model.__name__, obj.pk
        )
        messages.success(self.request, self.success_message_update.format(obj=obj))
        return super().form_valid(form)

    def can_modify(self, obj):
        return True

    def get_object(self, queryset=None):
        return super().get_object(queryset=queryset)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_modify(self.object):
            messages.error(self.request, "⛔ Vous ne pouvez pas modifier cet élément.")
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_modify(self.object):
            messages.error(self.request, "⛔ Vous ne pouvez pas modifier cet élément.")
            return redirect(self.get_success_url())
        return super().post(request, *args, **kwargs)


class CrudDeleteView(ModificationRequiredMixin, CrudMixin, DeleteView):
    """
    Vue suppression générique avec soft-delete, audit et message.
    """
    template_name = ''

    def get_template_names(self):
        if self.confirm_delete_template:
            return [self.confirm_delete_template]
        if self.model:
            app = self.model._meta.app_label
            model_name = self.model._meta.model_name
            return [f'{app}/{model_name}_confirm_delete.html']
        return []

    def get_success_url(self):
        return str(reverse_lazy(f'{self.model._meta.app_label}:liste'))

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_modify(self.object):
            messages.error(self.request, "⛔ Vous ne pouvez pas supprimer cet élément.")
            return redirect(self.get_success_url())
        obj = self.object
        obj_str = str(obj)
        if self.soft_delete and hasattr(obj, self.soft_delete_field):
            setattr(obj, self.soft_delete_field, True)
            if hasattr(obj, 'date_suppression'):
                from django.utils import timezone
                obj.date_suppression = timezone.now()
            obj.save()
        else:
            obj.delete()
        enregistrer_audit(
            request, self.audit_action_delete, self.module_name,
            f"Suppression : {obj_str}", self.model.__name__, obj.pk
        )
        messages.success(request, self.success_message_delete.format(obj=obj_str))
        return redirect(self.get_success_url())
