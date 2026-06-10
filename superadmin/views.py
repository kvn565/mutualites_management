from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model, authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.hashers import make_password

import json
from django.db.models import Count, Sum

from core.models import JournalAudit, Mutualite, CleActivation, AuditCle, HistoriqueConnexion
from factures.models import Facture
from affilies.models import Affilie
from .forms import MutualiteForm, SuperAdminUtilisateurForm

User = get_user_model()


class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.est_super_admin

    def handle_no_permission(self):
        messages.error(self.request, "Accès réservé aux super administrateurs.")
        return redirect('dashboard:index')

def superadmin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.est_super_admin):
            messages.error(request, "Accès réservé à l'administrateur.")
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


class DashboardView(SuperAdminRequiredMixin, TemplateView):
    template_name = 'superadmin/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()

        total_membres = Affilie.objects.filter(supprime=False).count()
        total_factures = Facture.objects.count()

        ctx['stats'] = {
            'total_mutualites': Mutualite.objects.count(),
            'mutualites_essai': Mutualite.objects.filter(statut='ESSAI').count(),
            'mutualites_actives': Mutualite.objects.filter(statut='ACTIF').count(),
            'mutualites_suspendues': Mutualite.objects.filter(statut='SUSPENDU').count(),
            'mutualites_expirees': Mutualite.objects.filter(statut='EXPIRE').count(),
            'mutualites_bloquees': Mutualite.objects.filter(statut='BLOQUE').count(),
            'total_utilisateurs': User.objects.count(),
            'total_membres': total_membres,
            'total_factures': total_factures,
        }

        mutualites_qs = Mutualite.objects.annotate(
            nb_membres=Count('affilies', filter=Q(affilies__supprime=False)),
            nb_factures=Count('factures'),
        ).order_by('nom')

        ctx['chart_mutualites'] = json.dumps([
            {
                'nom': m.nom,
                'nb_membres': getattr(m, 'nb_membres', 0),
                'nb_factures': getattr(m, 'nb_factures', 0),
            }
            for m in mutualites_qs
        ])

        ctx['mutualites_liste'] = Mutualite.objects.all().order_by('nom')

        ctx['derniers_audits'] = JournalAudit.objects.filter(
            module='superadmin',
        ).order_by('-date_action')[:10]

        seuil_expiration = now + timedelta(days=3)
        ctx['essai_expirant'] = Mutualite.objects.filter(
            statut='ESSAI',
            date_fin_essai__lte=seuil_expiration,
        )

        ctx['mutualites_sans_licence'] = Mutualite.objects.filter(
            statut__in=['EN_ATTENTE', 'EXPIRE'],
        )

        seuil_7j = now + timedelta(days=7)
        ctx['expiration_proche'] = Mutualite.objects.filter(
            statut__in=['ACTIF', 'ESSAI'],
            date_expiration__lte=seuil_7j,
            date_expiration__gte=now,
        )

        return ctx


@superadmin_required
def mutualites_liste(request):
    q = request.GET.get('q', '')
    statut = request.GET.get('statut', '')

    mutualites = Mutualite.objects.all()

    if q:
        mutualites = mutualites.filter(
            Q(nom__icontains=q) | Q(nif__icontains=q) |
            Q(telephone__icontains=q) | Q(nom_responsable__icontains=q) |
            Q(code_mutualite__icontains=q)
        )

    if statut:
        mutualites = mutualites.filter(statut=statut.upper())

    paginator = Paginator(mutualites, 10)
    page_number = request.GET.get('page')
    mutualites_page = paginator.get_page(page_number)

    return render(request, 'superadmin/mutualites_liste.html', {
        'mutualites': mutualites_page,
        'q': q,
        'statut': statut,
        'paginator': paginator,
    })


@superadmin_required
def mutualite_creer(request):
    if request.method == 'POST':
        form = MutualiteForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                mutualite = form.save(commit=False)
                mutualite.created_by = request.user
                mutualite.save()

                admin_username = form.cleaned_data.get('username_admin') or f"admin_{mutualite.code_mutualite.lower()}"
                admin_email = form.cleaned_data.get('email_admin') or mutualite.email
                admin_password = form.cleaned_data.get('password_admin') or User.objects.make_random_password()

                admin_user = User.objects.create_user(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password,
                    first_name=mutualite.nom_responsable.split()[0] if mutualite.nom_responsable else '',
                    last_name=' '.join(mutualite.nom_responsable.split()[1:]) if mutualite.nom_responsable else '',
                    role='ADMIN_MUTUALITE',
                    mutualite=mutualite,
                    telephone=mutualite.telephone,
                    actif=True,
                )

                mutualite.username_admin = admin_username
                mutualite.email_admin = admin_email
                mutualite.activer_essai(cree_par=request.user)

                JournalAudit.objects.create(
                    mutualite=mutualite,
                    utilisateur=request.user,
                    action='CREATION',
                    module='superadmin',
                    description=f"Mutualité '{mutualite.nom}' enregistrée par {request.user.username}",
                    objet_type='Mutualite',
                    objet_id=mutualite.pk,
                    adresse_ip=request.META.get('REMOTE_ADDR', ''),
                )

                messages.success(
                    request,
                    f"Mutualité « {mutualite.nom} » enregistrée. "
                    f"Administrateur créé : {admin_username} / mot de passe : {admin_password}. "
                    f"Essai gratuit de 14 jours activé !"
                )
                return redirect('superadmin:mutualite_detail', pk=mutualite.pk)
    else:
        form = MutualiteForm()

    return render(request, 'superadmin/mutualite_form.html', {
        'form': form,
        'titre': "Enregistrer une nouvelle mutualité",
    })


@superadmin_required
def mutualite_modifier(request, pk):
    mutualite = get_object_or_404(Mutualite, pk=pk)
    if request.method == 'POST':
        form = MutualiteForm(request.POST, instance=mutualite)
        if form.is_valid():
            form.save()
            JournalAudit.objects.create(
                mutualite=mutualite,
                utilisateur=request.user,
                action='MODIFICATION',
                module='superadmin',
                description=f"Mutualité '{mutualite.nom}' modifiée par {request.user.username}",
                objet_type='Mutualite',
                objet_id=mutualite.pk,
                adresse_ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, f"Mutualité « {mutualite.nom} » modifiée.")
            return redirect('superadmin:mutualite_detail', pk=pk)
    else:
        form = MutualiteForm(instance=mutualite)

    return render(request, 'superadmin/mutualite_form.html', {
        'form': form,
        'titre': 'Modifier mutualité',
        'mutualite': mutualite,
    })


@superadmin_required
def mutualite_detail(request, pk):
    mutualite = get_object_or_404(Mutualite, pk=pk)
    utilisateurs = mutualite.utilisateurs.all().order_by('-date_creation')
    journaux = JournalAudit.objects.filter(mutualite=mutualite).order_by('-date_action')[:20]

    return render(request, 'superadmin/mutualite_detail.html', {
        'mutualite': mutualite,
        'utilisateurs': utilisateurs,
        'journaux': journaux,
    })


@superadmin_required
def mutualite_suspendre(request, pk):
    mutualite = get_object_or_404(Mutualite, pk=pk)
    if mutualite.statut not in ('ACTIF', 'ESSAI'):
        messages.warning(request, f"La mutualité « {mutualite.nom} » ne peut pas être suspendue (statut : {mutualite.get_statut_display()}).")
        return redirect('superadmin:mutualite_detail', pk=pk)

    mutualite.statut = 'SUSPENDU'
    mutualite.save()

    JournalAudit.objects.create(
        mutualite=mutualite,
        utilisateur=request.user,
        action='MODIFICATION',
        module='superadmin',
        description=f"Mutualité '{mutualite.nom}' suspendue par {request.user.username}",
        objet_type='Mutualite',
        objet_id=mutualite.pk,
        adresse_ip=request.META.get('REMOTE_ADDR', ''),
    )
    messages.warning(request, f"Mutualité « {mutualite.nom} » suspendue.")
    return redirect('superadmin:mutualite_detail', pk=pk)


@superadmin_required
def mutualite_reactiver(request, pk):
    mutualite = get_object_or_404(Mutualite, pk=pk)
    if mutualite.statut != 'SUSPENDU':
        messages.info(request, f"La mutualité « {mutualite.nom} » n'est pas suspendue.")
        return redirect('superadmin:mutualite_detail', pk=pk)

    if mutualite.essai_gratuit:
        mutualite.activer_essai()
    else:
        mutualite.statut = 'ACTIF'
        mutualite.save()

    JournalAudit.objects.create(
        mutualite=mutualite,
        utilisateur=request.user,
        action='MODIFICATION',
        module='superadmin',
        description=f"Mutualité '{mutualite.nom}' réactivée par {request.user.username}",
        objet_type='Mutualite',
        objet_id=mutualite.pk,
        adresse_ip=request.META.get('REMOTE_ADDR', ''),
    )
    messages.success(request, f"Mutualité « {mutualite.nom} » réactivée.")
    return redirect('superadmin:mutualite_detail', pk=pk)


@superadmin_required
def mutualite_renouveler_licence(request, pk):
    mutualite = get_object_or_404(Mutualite, pk=pk)
    if request.method == 'POST':
        type_abonnement = request.POST.get('type_abonnement', 'MENSUEL')
        duree_jours = int(request.POST.get('duree_jours', 30))

        mutualite.activer_licence(type_abonnement, duree_jours)

        JournalAudit.objects.create(
            mutualite=mutualite,
            utilisateur=request.user,
            action='MODIFICATION',
            module='superadmin',
            description=f"Licence renouvelée pour '{mutualite.nom}' : {type_abonnement}, {duree_jours} jours, par {request.user.username}",
            objet_type='Mutualite',
            objet_id=mutualite.pk,
            adresse_ip=request.META.get('REMOTE_ADDR', ''),
        )
        messages.success(request, f"Licence renouvelée pour « {mutualite.nom} » jusqu'au {mutualite.date_expiration.strftime('%d/%m/%Y')}.")
        return redirect('superadmin:mutualite_detail', pk=pk)

    return render(request, 'superadmin/renouveler_licence.html', {
        'mutualite': mutualite,
    })


@superadmin_required
def mutualite_essai_prolonger(request, pk):
    mutualite = get_object_or_404(Mutualite, pk=pk)
    if request.method == 'POST':
        jours = int(request.POST.get('jours', 7))
        from datetime import timedelta
        if mutualite.date_fin_essai:
            mutualite.date_fin_essai += timedelta(days=jours)
        else:
            mutualite.date_fin_essai = timezone.now() + timedelta(days=jours)
        mutualite.date_expiration = mutualite.date_fin_essai
        mutualite.statut = 'ESSAI'
        mutualite.save()

        JournalAudit.objects.create(
            mutualite=mutualite,
            utilisateur=request.user,
            action='MODIFICATION',
            module='superadmin',
            description=f"Essai prolongé de {jours} jours pour '{mutualite.nom}' par {request.user.username}",
            objet_type='Mutualite',
            objet_id=mutualite.pk,
            adresse_ip=request.META.get('REMOTE_ADDR', ''),
        )
        messages.success(request, f"Essai prolongé de {jours} jours pour « {mutualite.nom} ».")
        return redirect('superadmin:mutualite_detail', pk=pk)

    return render(request, 'superadmin/prolonger_essai.html', {
        'mutualite': mutualite,
    })


@superadmin_required
def utilisateurs_liste(request):
    q = request.GET.get('q', '')
    role = request.GET.get('role', '')
    mutualite_id = request.GET.get('mutualite', '')

    utilisateurs = User.objects.all().order_by('-date_creation')

    if q:
        utilisateurs = utilisateurs.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(nom__icontains=q) |
            Q(prenom__icontains=q) |
            Q(telephone__icontains=q)
        )
    if role:
        utilisateurs = utilisateurs.filter(role=role)
    if mutualite_id:
        utilisateurs = utilisateurs.filter(mutualite_id=mutualite_id)

    paginator = Paginator(utilisateurs, 10)
    page_number = request.GET.get('page')
    utilisateurs_page = paginator.get_page(page_number)

    mutualites = Mutualite.objects.all().order_by('nom')

    return render(request, 'superadmin/utilisateurs_liste.html', {
        'utilisateurs': utilisateurs_page,
        'paginator': paginator,
        'q': q,
        'role': role,
        'mutualite_id': mutualite_id,
        'mutualites': mutualites,
    })


@superadmin_required
def utilisateur_creer(request):
    if request.method == 'POST':
        form = SuperAdminUtilisateurForm(request.POST)
        if form.is_valid():
            user = form.save()
            JournalAudit.objects.create(
                mutualite=user.mutualite,
                utilisateur=request.user,
                action='CREATION',
                module='superadmin',
                description=f"Utilisateur '{user.username}' créé par {request.user.username}",
                objet_type='Utilisateur',
                objet_id=user.pk,
                adresse_ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, f"Utilisateur « {user.nom_complet or user.username} » créé avec succès.")
            return redirect('superadmin:utilisateurs_liste')
    else:
        form = SuperAdminUtilisateurForm()

    return render(request, 'superadmin/utilisateur_form.html', {
        'form': form,
        'titre': 'Créer un utilisateur',
        'is_create': True,
    })


@superadmin_required
def utilisateur_modifier(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = SuperAdminUtilisateurForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            JournalAudit.objects.create(
                mutualite=user.mutualite,
                utilisateur=request.user,
                action='MODIFICATION',
                module='superadmin',
                description=f"Utilisateur '{user.username}' modifié par {request.user.username}",
                objet_type='Utilisateur',
                objet_id=user.pk,
                adresse_ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, f"Utilisateur « {user.nom_complet or user.username} » modifié.")
            return redirect('superadmin:utilisateurs_liste')
    else:
        form = SuperAdminUtilisateurForm(instance=user)

    return render(request, 'superadmin/utilisateur_form.html', {
        'form': form,
        'titre': "Modifier l'utilisateur",
        'user': user,
    })


@superadmin_required
def utilisateur_supprimer(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'Vous ne pouvez pas supprimer votre propre compte.')
        return redirect('superadmin:utilisateurs_liste')
    if user.est_super_admin:
        messages.error(request, 'Vous ne pouvez pas supprimer un super administrateur.')
        return redirect('superadmin:utilisateurs_liste')

    if request.method == 'POST':
        nom = user.nom_complet or user.username
        user.delete()
        JournalAudit.objects.create(
            mutualite=user.mutualite,
            utilisateur=request.user,
            action='SUPPRESSION',
            module='superadmin',
            description=f"Utilisateur '{nom}' supprimé par {request.user.username}",
            objet_type='Utilisateur',
            objet_id=pk,
            adresse_ip=request.META.get('REMOTE_ADDR', ''),
        )
        messages.success(request, f"Utilisateur « {nom} » supprimé.")
        return redirect('superadmin:utilisateurs_liste')

    return render(request, 'superadmin/utilisateur_confirm_supprimer.html', {
        'user': user,
    })


@superadmin_required
def cles_liste(request):
    q = request.GET.get('q', '')
    statut = request.GET.get('statut', '')
    type_plan = request.GET.get('type_plan', '')

    cles = CleActivation.objects.all().select_related('mutualite')

    if q:
        cles = cles.filter(
            Q(cle_visible__icontains=q) |
            Q(mutualite__nom__icontains=q) |
            Q(mutualite__nif__icontains=q)
        )
    if statut:
        cles = cles.filter(statut=statut)
    if type_plan:
        cles = cles.filter(type_plan=type_plan)

    paginator = Paginator(cles, 10)
    page_number = request.GET.get('page')
    cles_page = paginator.get_page(page_number)

    return render(request, 'superadmin/cles_liste.html', {
        'cles': cles_page,
        'paginator': paginator,
        'q': q,
        'statut': statut,
        'type_plan': type_plan,
    })


@superadmin_required
def cle_generer(request):
    mutualites = Mutualite.objects.all().order_by('nom')

    if request.method == 'POST':
        mutualite_id = request.POST.get('mutualite')
        type_plan = request.POST.get('type_plan')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not mutualite_id or not type_plan:
            messages.error(request, 'Veuillez sélectionner une mutualité et un type de plan.')
            return redirect('superadmin:cles_generer')

        mutualite = get_object_or_404(Mutualite, pk=mutualite_id)

        try:
            from datetime import datetime

            if type_plan == 'PERSONNALISE':
                if not date_debut or not date_fin:
                    messages.error(request, 'Veuillez spécifier les dates de début et fin pour un plan personnalisé.')
                    return redirect('superadmin:cles_generer')
                dt_debut = datetime.strptime(date_debut, '%Y-%m-%d').replace(tzinfo=timezone.get_current_timezone())
                dt_fin = datetime.strptime(date_fin, '%Y-%m-%d').replace(tzinfo=timezone.get_current_timezone())
            else:
                dt_debut = timezone.now()
                plan_to_duree = {
                    'ESSAI': 14, '1MOIS': 30, '6MOIS': 182,
                    '12MOIS': 365, '24MOIS': 730,
                }
                duree_jours = plan_to_duree.get(type_plan, 30)
                dt_debut = timezone.now()
                dt_fin = dt_debut + timedelta(days=duree_jours)

            cle = CleActivation.objects.create(
                mutualite=mutualite,
                type_plan=type_plan,
                date_debut=dt_debut,
                date_fin=dt_fin,
                active=True,
                utilisee=False,
                statut='DISPONIBLE',
                cree_par=request.user.username,
                notes=f"Générée par {request.user.username}",
            )

            AuditCle.objects.create(
                cle=cle,
                mutualite=mutualite,
                action='CREEE',
                message=f"Clé {cle.cle_visible} générée pour {mutualite.nom} ({cle.label_plan})",
                ip_address=request.META.get('REMOTE_ADDR', ''),
            )

            messages.success(
                request,
                f"Clé générée avec succès pour « {mutualite.nom} ».<br>"
                f"<strong>Clé :</strong> <code>{cle.cle_visible}</code><br>"
                f"<strong>Plan :</strong> {cle.label_plan}<br>"
                f"<strong>Validité :</strong> du {dt_debut.strftime('%d/%m/%Y')} au {dt_fin.strftime('%d/%m/%Y')}"
            )
            return redirect('superadmin:cles_liste')

        except Exception as e:
            messages.error(request, f"Erreur lors de la génération : {e}")
            return redirect('superadmin:cles_generer')

    return render(request, 'superadmin/cle_generer.html', {
        'mutualites': mutualites,
    })


@superadmin_required
def cle_activer(request, pk):
    cle = get_object_or_404(CleActivation, pk=pk)
    mutualite = cle.mutualite

    if cle.statut != 'DISPONIBLE':
        messages.warning(request, f"Cette clé a déjà le statut « {cle.get_statut_display()} ».")
        return redirect('superadmin:cles_liste')

    cle.utilisee = True
    cle.date_utilisation = timezone.now()
    cle.save()

    mutualite.cle_activation = cle.cle_visible
    mutualite.date_activation = cle.date_debut
    mutualite.date_expiration = cle.date_fin
    mutualite.type_abonnement = cle.type_plan
    mutualite.essai_gratuit = (cle.type_plan == 'ESSAI')
    mutualite.statut = 'ACTIF'
    mutualite.save()

    AuditCle.objects.create(
        cle=cle,
        mutualite=mutualite,
        action='ACTIVEE',
        message=f"Clé {cle.cle_visible} activée pour {mutualite.nom}",
        ip_address=request.META.get('REMOTE_ADDR', ''),
    )

    messages.success(request, f"Clé activée pour « {mutualite.nom} ». Expire le {cle.date_fin.strftime('%d/%m/%Y')}.")
    return redirect('superadmin:cles_liste')


@superadmin_required
def cle_revoquer(request, pk):
    cle = get_object_or_404(CleActivation, pk=pk)
    if cle.statut == 'REVOQUEE':
        messages.warning(request, 'Cette clé est déjà révoquée.')
        return redirect('superadmin:cles_liste')

    if request.method == 'POST':
        motif = request.POST.get('motif', '')
        cle.active = False
        cle.motif_revocation = motif
        cle.save()

        AuditCle.objects.create(
            cle=cle,
            mutualite=cle.mutualite,
            action='REVOQUEE',
            message=f"Clé {cle.cle_visible} révoquée : {motif or 'Aucun motif'}",
            ip_address=request.META.get('REMOTE_ADDR', ''),
        )

        messages.success(request, f"Clé « {cle.cle_visible} » révoquée.")
        return redirect('superadmin:cles_liste')

    return render(request, 'superadmin/cle_revoquer.html', {'cle': cle})


@superadmin_required
def mutualite_factures(request, pk):
    mutualite = get_object_or_404(Mutualite, pk=pk)
    factures = Facture.objects.filter(mutualite=mutualite).select_related(
        'partenaire', 'affilie', 'ayant_droit'
    ).order_by('-date', '-pk')
    paginator = Paginator(factures, 10)

    page = request.GET.get('page')
    factures_page = paginator.get_page(page)

    from django.db.models import Sum
    stats = Facture.objects.filter(mutualite=mutualite).aggregate(
        total=Sum('montant_total'),
        part_mutualite=Sum('montant_mutualite'),
        part_patient=Sum('montant_ticket_moderateur'),
        nb_brouillon=Count('pk', filter=Q(statut='BROUILLON')),
        nb_soumis=Count('pk', filter=Q(statut='SOUMIS')),
        nb_valide=Count('pk', filter=Q(statut='VALIDE')),
        nb_paye=Count('pk', filter=Q(statut='PAYE')),
    )

    return render(request, 'superadmin/mutualite_factures.html', {
        'mutualite': mutualite,
        'factures': factures_page,
        'paginator': paginator,
        'stats': stats,
    })


@superadmin_required
def mutualite_membres(request, pk):
    mutualite = get_object_or_404(Mutualite, pk=pk)
    affilies = Affilie.objects.filter(mutualite=mutualite, supprime=False).order_by('-date_adhesion')

    paginator = Paginator(affilies, 10)
    page = request.GET.get('page')
    affilies_page = paginator.get_page(page)

    stats = Affilie.objects.filter(mutualite=mutualite, supprime=False).aggregate(
        total=Count('pk'),
        actifs=Count('pk', filter=Q(statut='ACTIF')),
        en_attente=Count('pk', filter=Q(statut='EN_ATTENTE')),
        suspendus=Count('pk', filter=Q(statut='SUSPENDU')),
        radios=Count('pk', filter=Q(statut='RADIE')),
    )

    return render(request, 'superadmin/mutualite_membres.html', {
        'mutualite': mutualite,
        'affilies': affilies_page,
        'paginator': paginator,
        'stats': stats,
    })


@superadmin_required
def suivi_factures(request):
    mutualites = Mutualite.objects.annotate(
        nb_factures=Count('factures'),
    ).order_by('nom')

    return render(request, 'superadmin/suivi_factures.html', {
        'mutualites': mutualites,
    })


@superadmin_required
def suivi_membres(request):
    mutualites = Mutualite.objects.annotate(
        nb_affilies=Count('affilies', filter=Q(affilies__supprime=False)),
    ).order_by('nom')

    return render(request, 'superadmin/membres_liste.html', {
        'mutualites': mutualites,
    })


@superadmin_required
def audit_connexions(request):
    q = request.GET.get('q', '')
    mutualite_id = request.GET.get('mutualite', '')

    connexions = HistoriqueConnexion.objects.select_related(
        'utilisateur', 'mutualite'
    ).order_by('-date_connexion')

    if q:
        connexions = connexions.filter(
            Q(utilisateur__username__icontains=q) |
            Q(utilisateur__nom__icontains=q) |
            Q(utilisateur__prenom__icontains=q) |
            Q(adresse_ip__icontains=q) |
            Q(user_agent__icontains=q)
        )
    if mutualite_id:
        connexions = connexions.filter(mutualite_id=mutualite_id)

    paginator = Paginator(connexions, 10)
    page = request.GET.get('page')
    connexions_page = paginator.get_page(page)

    mutualites = Mutualite.objects.all().order_by('nom')

    return render(request, 'superadmin/audit_connexions.html', {
        'connexions': connexions_page,
        'paginator': paginator,
        'q': q,
        'mutualite_id': mutualite_id,
        'mutualites': mutualites,
    })
