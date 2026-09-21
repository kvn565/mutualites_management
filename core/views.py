import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic.detail import SingleObjectMixin

from core.mixins import ModificationRequiredMixin, MutualiteRequiredMixin
from core.models import Mutualite, Utilisateur, JournalAudit, HistoriqueConnexion, set_current_mutualite

logger = logging.getLogger('core.security')


def landing_view(request):
    from django.shortcuts import redirect
    if request.user.is_authenticated:
        # Super admin de la plateforme → espace superadmin
        if request.user.est_super_admin:
            return redirect('superadmin:dashboard')
        # Staff/superuser Django uniquement → interface admin Django
        if request.user.is_superuser or request.user.is_staff:
            return redirect('admin:index')
        # Utilisateur normal d'une mutualité → dashboard
        return redirect('dashboard:index')
    # Non connecté → page de connexion
    return redirect('core:login')


def login_view(request):
    from core.forms import ConnexionForm
    if request.user.is_authenticated:
        if not request.user.est_super_admin and request.user.mutualite:
            try:
                request.user.mutualite.actualiser_statut_expiration()
            except Exception:
                pass
            if not request.user.mutualite.licence_valide:
                return redirect('activer_licence')
        return redirect('dashboard:index')
    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.actif:
                    # Vérifier si la mutualité a été auto-supprimée (expirée)
                    if user.mutualite and user.mutualite.statut == 'EN_ATTENTE':
                        from datetime import timedelta
                        from django.utils import timezone
                        age = (timezone.now() - user.mutualite.date_creation).days
                        if age >= 7:
                            # Mutualité expirée - supprimer l'utilisateur aussi
                            user.delete()
                            messages.error(request, "Votre mutualité a expiré (plus de 7 jours sans validation). Veuillez vous réinscrire.")
                            return redirect('core:inscription')
                    
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
                    if not user.est_super_admin and getattr(user.mutualite, 'statut', None) == 'EN_ATTENTE':
                        request.session['mutualite_inscrite_id'] = user.mutualite.pk
                        return redirect('core:inscription_attente')
                    if not user.est_super_admin and user.mutualite:
                        try:
                            user.mutualite.actualiser_statut_expiration()
                        except Exception:
                            pass
                        if not user.mutualite.licence_valide:
                            messages.warning(request, "⚠️ Votre licence est expirée. Veuillez saisir une clé d'activation pour continuer.")
                            if user.est_super_admin:
                                return redirect('superadmin:dashboard')
                            return redirect('activer_licence')
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
                nif=data.get('nif') or None,
                sigle=data.get('sigle', ''),
                province=data.get('province', ''),
                commune=data.get('commune', ''),
                quartier=data.get('quartier', ''),
                adresse=data.get('adresse', ''),
                telephone=data.get('telephone', ''),
                email=data.get('email', ''),
                statut='EN_ATTENTE',
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
            JournalAudit.objects.create(
                utilisateur=admin, action='CREATION', module='core',
                description=f"Inscription de la mutualité {mutualite.nom} par {admin.nom_complet}",
                mutualite=mutualite,
            )
            request.session['mutualite_inscrite_id'] = mutualite.pk
            return redirect('core:inscription_attente')
    else:
        form = InscriptionForm()
    return render(request, 'core/inscription.html', {'form': form})


def inscription_attente(request):
    from datetime import timedelta
    from django.utils import timezone
    
    mutualite_id = request.session.get('mutualite_inscrite_id')
    mutualite = None
    if mutualite_id:
        try:
            mutualite = Mutualite.objects.get(pk=mutualite_id)
        except Mutualite.DoesNotExist:
            pass
    if not mutualite and request.user.is_authenticated:
        mutualite = getattr(request.user, 'mutualite', None)
    if not mutualite:
        return redirect('core:login')

    # Vérifier si la mutualité a expiré (plus de 7 jours en attente)
    if mutualite.statut == 'EN_ATTENTE':
        age = (timezone.now() - mutualite.date_creation).days
        if age >= 7:
            # Supprimer la mutualité et son admin
            username_admin = mutualite.username_admin
            mutualite_nom = mutualite.nom
            
            # Log audit
            from core.models import JournalAudit
            JournalAudit.objects.create(
                mutualite=None,
                utilisateur=None,
                action='SUPPRESSION_AUTO',
                module='core',
                description=f"Suppression auto : mutualité '{mutualite_nom}' en attente depuis {age} jours (expirée)",
                objet_type='Mutualite',
                objet_id=mutualite.pk,
                adresse_ip='system',
            )
            
            # Supprimer l'admin user s'il existe
            if username_admin:
                try:
                    admin_user = Utilisateur.objects.get(username=username_admin, mutualite=mutualite)
                    admin_user.delete()
                except Utilisateur.DoesNotExist:
                    pass
            
            # Supprimer la mutualité
            mutualite.delete()
            
            # Nettoyer la session
            request.session.pop('mutualite_inscrite_id', None)
            
            from django.contrib import messages
            messages.info(request, f"Votre demande d'inscription a expiré (plus de 7 jours sans validation). Vous pouvez vous réinscrire.")
            return redirect('core:inscription')

    return render(request, 'core/inscription_attente.html', {'mutualite': mutualite})


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


def activer_licence(request):
    from core.models import CleActivation
    if not request.user.is_authenticated:
        return render(request, 'core/licence_activer.html', {'mutualite': None})
    mutualite = request.user.mutualite
    if not mutualite or request.user.est_super_admin:
        messages.error(request, "⛔ Accès non autorisé.")
        return redirect('dashboard:index')

    if request.method == 'POST':
        cle = request.POST.get('cle_activation', '').strip().upper()
        if not cle:
            messages.error(request, "Veuillez entrer une clé d'activation.")
        else:
            obj = CleActivation.objects.filter(cle_visible=cle, utilisee=False, active=True).first()
            if obj and obj.mutualite == mutualite:
                obj.utilisee = True
                obj.date_utilisation = timezone.now()
                obj.statut = 'ACTIVE'
                obj.save()
                mutualite.essai_gratuit = (obj.type_plan == 'ESSAI')
                mutualite.cle_activation = obj.cle_visible
                mutualite.date_activation = obj.date_debut
                mutualite.date_expiration = obj.date_fin
                mutualite.type_abonnement = obj.type_plan
                mutualite.statut = 'ACTIF'
                mutualite.save()
                JournalAudit.objects.create(
                    mutualite=mutualite, utilisateur=request.user,
                    action='MODIFICATION', module='core',
                    description=f"Licence activée avec la clé {cle}",
                    objet_type='Mutualite', objet_id=mutualite.pk,
                    adresse_ip=request.META.get('REMOTE_ADDR', ''),
                )
                messages.success(request, f"✅ Licence activée avec succès jusqu'au {mutualite.date_expiration.strftime('%d/%m/%Y')}.")
                return redirect('dashboard:index')
            else:
                messages.error(request, "❌ Clé invalide ou déjà utilisée. Contactez l'administrateur.")

    return render(request, 'core/licence_activer.html', {'mutualite': mutualite})


@login_required
def parametres_mutualite(request):
    if not request.user.est_admin and not request.user.est_super_admin:
        messages.error(request, "⛔ Accès réservé aux administrateurs.")
        return redirect('dashboard:index')

    mutualite = request.user.mutualite
    if not mutualite:
        messages.error(request, "⛔ Aucune mutualité associée à votre compte.")
        return redirect('dashboard:index')

    from .forms import MutualiteParametresForm

    if request.method == 'POST':
        form = MutualiteParametresForm(request.POST, request.FILES, instance=mutualite)
        if form.is_valid():
            form.save()
            JournalAudit.objects.create(
                mutualite=mutualite,
                utilisateur=request.user,
                action='MODIFICATION',
                module='core',
                description=f"Paramètres mutualité modifiés par {request.user.username}",
                objet_type='Mutualite',
                objet_id=mutualite.pk,
                adresse_ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, "✅ Paramètres de la mutualité mis à jour.")
            return redirect('parametres_mutualite')
    else:
        form = MutualiteParametresForm(instance=mutualite)

    # Exclusions globales (paginated)
    from core.models import MutualiteExclusion
    exclusions_qs = MutualiteExclusion.objects.filter(mutualite=mutualite).select_related('medicament', 'service')
    page_excl = request.GET.get('page_excl', 1)
    paginator_excl = Paginator(exclusions_qs, 5)
    exclusions_globales = paginator_excl.get_page(page_excl)
    medicaments = mutualite.medicaments.all() if mutualite else []
    services = mutualite.servicesantes.all() if mutualite else []

    return render(request, 'core/mutualite_parametres.html', {
        'form': form,
        'mutualite': mutualite,
        'exclusions_globales': exclusions_globales,
        'paginator_excl': paginator_excl,
        'medicaments': medicaments,
        'services': services,
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
        if hasattr(obj, 'is_deleted'):
            obj.delete(user=request.user)
        elif self.soft_delete and hasattr(obj, self.soft_delete_field):
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


@login_required
@require_POST
def dismiss_notification_licence(request):
    """Masque la notification de licence pour 24h."""
    request.session['licence_notif_dismissed'] = timezone.now().isoformat()
    return JsonResponse({'ok': True})


# ─────────────────────────────────────────────
#  Notifications de plafond (mutualité)
# ─────────────────────────────────────────────

@login_required
def notification_liste(request):
    from core.models import Notification
    mutualite = request.user.mutualite
    if not mutualite:
        messages.error(request, "Aucune mutualité associée.")
        return redirect('dashboard')

    notif_vues = request.GET.get('vues', 'non')
    qs = Notification.objects.filter(mutualite=mutualite)
    if notif_vues == 'non':
        qs = qs.filter(vue=False)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'notifications': page,
        'paginator': paginator,
        'filtre_vues': notif_vues,
    }
    return render(request, 'core/notification_liste.html', context)


@login_required
@require_POST
def notification_marquer_vue(request, pk):
    from core.models import Notification
    notification = get_object_or_404(Notification, pk=pk, mutualite=request.user.mutualite)
    notification.vue = True
    notification.save(update_fields=['vue'])
    return redirect('core:notification_liste')


@login_required
def notification_marquer_vue_rapide(request, pk):
    from core.models import Notification
    try:
        notification = Notification.objects.get(pk=pk, mutualite=request.user.mutualite)
        if not notification.vue:
            notification.vue = True
            notification.save(update_fields=['vue'])
    except Notification.DoesNotExist:
        pass
    return HttpResponse('ok')


@login_required
@require_POST
def notification_tout_vu(request):
    from core.models import Notification
    Notification.objects.filter(mutualite=request.user.mutualite, vue=False).update(vue=True)
    messages.success(request, "Toutes les notifications marquées comme lues.")
    return redirect('core:notification_liste')


@login_required
@require_POST
def notification_debloquer(request, pk):
    """Débloque un affilié pour dépassement de plafond (reset mensuel)."""
    from core.models import Notification
    notification = get_object_or_404(Notification, pk=pk, mutualite=request.user.mutualite)
    affilie = notification.affilie
    affilie.bloque = False
    affilie.save(update_fields=['bloque'])

    Notification.objects.create(
        mutualite=request.user.mutualite,
        affilie=affilie,
        type_notification='DEBLOCAGE',
        message=(
            f"L'affilié {affilie.nom_complet} ({affilie.numero_affiliation}) "
            f"a été débloqué par {request.user.get_full_name() or request.user.username}."
        ),
        consommation=notification.consommation,
        plafond=notification.plafond,
        pourcentage=notification.pourcentage,
    )

    enregistrer_audit(request, 'MODIFICATION', 'affilies',
                      f"Déblocage plafond : {affilie.nom_complet} ({affilie.numero_affiliation})",
                      'Affilie', affilie.pk)
    messages.success(request, f"L'affilié {affilie.nom_complet} a été débloqué.")
    return redirect('core:notification_liste')


# ─────────────────────────────────────────────
#  Exclusions globales (mutualité)
# ─────────────────────────────────────────────

@login_required
@require_POST
def mutualite_exclusion_ajouter(request):
    if not request.user.est_admin or request.user.est_super_admin:
        messages.error(request, "Permission refusée.")
        return redirect('parametres_mutualite')

    from core.models import MutualiteExclusion
    type_excl = request.POST.get('type')
    item_pk = request.POST.get('item_pk')
    motif = request.POST.get('motif', '')

    if not type_excl or not item_pk:
        messages.error(request, "Veuillez sélectionner un type et un élément.")
        return redirect('parametres_mutualite')

    if type_excl == 'medicament':
        from pharmacie.models import Medicament
        item = get_object_or_404(Medicament, pk=item_pk, mutualite=request.user.mutualite)
        if MutualiteExclusion.objects.filter(mutualite=request.user.mutualite, medicament=item).exists():
            messages.warning(request, "Ce médicament est déjà exclu globalement.")
            return redirect('parametres_mutualite')
        MutualiteExclusion.objects.create(
            mutualite=request.user.mutualite, medicament=item,
            motif=motif, cree_par=request.user,
        )
        messages.success(request, f"Médicament « {item.nom} » exclu globalement.")
    elif type_excl == 'service':
        from services_sante.models import ServiceSante
        item = get_object_or_404(ServiceSante, pk=item_pk, mutualite=request.user.mutualite)
        if MutualiteExclusion.objects.filter(mutualite=request.user.mutualite, service=item).exists():
            messages.warning(request, "Ce service est déjà exclu globalement.")
            return redirect('parametres_mutualite')
        MutualiteExclusion.objects.create(
            mutualite=request.user.mutualite, service=item,
            motif=motif, cree_par=request.user,
        )
        messages.success(request, f"Service « {item.nom} » exclu globalement.")

    return redirect('parametres_mutualite')


@login_required
@require_POST
def mutualite_exclusion_supprimer(request, pk):
    from core.models import MutualiteExclusion
    exclusion = get_object_or_404(MutualiteExclusion, pk=pk, mutualite=request.user.mutualite)
    label = str(exclusion)
    exclusion.delete()
    messages.success(request, f"Exclusion globale supprimée : {label}")
    return redirect('parametres_mutualite')


@login_required
@require_POST
def notification_bloquer_definitif(request, pk):
    """Bloque définitivement un affilié."""
    from core.models import Notification
    notification = get_object_or_404(Notification, pk=pk, mutualite=request.user.mutualite)
    affilie = notification.affilie
    affilie.bloque = True
    affilie.bloque_definitif = True
    affilie.save(update_fields=['bloque', 'bloque_definitif'])

    Notification.objects.create(
        mutualite=request.user.mutualite,
        affilie=affilie,
        type_notification='BLOCAGE_DEF',
        message=(
            f"L'affilié {affilie.nom_complet} ({affilie.numero_affiliation}) "
            f"a été bloqué définitivement par {request.user.get_full_name() or request.user.username}."
        ),
        consommation=notification.consommation,
        plafond=notification.plafond,
        pourcentage=notification.pourcentage,
    )

    enregistrer_audit(request, 'MODIFICATION', 'affilies',
                      f"Blocage définitif plafond : {affilie.nom_complet} ({affilie.numero_affiliation})",
                      'Affilie', affilie.pk)
    messages.success(request, f"L'affilié {affilie.nom_complet} a été bloqué définitivement.")
    return redirect('core:notification_liste')
