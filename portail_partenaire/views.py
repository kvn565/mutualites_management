import json
import io
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string

from partenaires.models import UtilisateurPartenaire, Partenaire, DocumentMedical, RelationPartenaireMutualite
from affilies.models import Affilie
from ayants_droit.models import AyantDroit
from factures.models import Facture, LigneFacture
from services_sante.models import ServiceSante

from .forms import (
    ConnexionForm, InscriptionForm, RechercheMembreForm, FactureForm,
    FactureSimpleClientForm, LigneFactureFormSet, DocumentMedicalForm,
    PartenaireProfilForm, ChangerMotDePasseForm, InfoCompteForm,
    CreerUtilisateurForm,
    MedicamentForm,
)
from services_sante.forms import ServiceSanteForm
from pharmacie.models import Medicament, CategorieMedicament


def get_partenaire_from_session(request):
    pk = request.session.get('partenaire_user_id')
    if not pk:
        return None
    try:
        return UtilisateurPartenaire.objects.select_related(
            'partenaire', 'mutualite'
        ).get(pk=pk, actif=True)
    except UtilisateurPartenaire.DoesNotExist:
        return None


def get_mutualites_list(user):
    return user.partenaire.mutualites_liees


def get_mutualite_active(request, user):
    """Retourne la mutualité sélectionnée en session, ou None (toutes)."""
    pk = request.session.get('mutualite_active_pk')
    if pk:
        try:
            return user.partenaire.mutualites_liees.get(pk=int(pk))
        except (ValueError, user.partenaire.mutualites_liees.model.DoesNotExist):
            pass
    return None


def get_relations_partenaire(partenaire):
    return RelationPartenaireMutualite.objects.filter(
        partenaire=partenaire,
    ).select_related('mutualite').order_by('-date_demande')


def changer_mutualite(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')
    pk = request.GET.get('pk') or request.POST.get('pk')
    if pk:
        request.session['mutualite_active_pk'] = pk
    else:
        request.session.pop('mutualite_active_pk', None)
    request.session.modified = True
    return redirect(request.GET.get('next', 'portail_partenaire:dashboard'))


def connexion(request):
    if get_partenaire_from_session(request):
        return redirect('portail_partenaire:dashboard')

    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = UtilisateurPartenaire.objects.get(
                    username=username, actif=True,
                )
            except UtilisateurPartenaire.DoesNotExist:
                user = None

            if user and user.check_password(password):
                if user.partenaire.statut == 'EN_ATTENTE':
                    request.session['partenaire_inscrit_id'] = user.partenaire.pk
                    messages.info(
                        request,
                        f"Votre compte est en attente de validation. "
                        f"Vous serez contacté dès activation.",
                    )
                    return redirect('portail_partenaire:inscription_attente')
                elif user.partenaire.statut != 'ACTIF':
                    messages.error(
                        request,
                        f"L'établissement '{user.partenaire.nom_etablissement}' "
                        f"n'est pas actif. Contactez votre mutualité.",
                    )
                    return render(request, 'portail_partenaire/connexion.html', {'form': form})

                request.session['partenaire_user_id'] = user.pk
                request.session['partenaire_username'] = user.username
                request.session['partenaire_nom'] = str(user)
                request.session.set_expiry(28800)

                messages.success(
                    request,
                    f"Bienvenue {user.username} sur le portail {user.partenaire.nom_etablissement}.",
                )
                return redirect('portail_partenaire:dashboard')
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = ConnexionForm()

    return render(request, 'portail_partenaire/connexion.html', {'form': form})


def inscription_attente(request):
    partenaire_id = request.session.get('partenaire_inscrit_id')
    partenaire = None
    if partenaire_id:
        try:
            partenaire = Partenaire.objects.get(pk=partenaire_id)
        except Partenaire.DoesNotExist:
            pass
    if not partenaire:
        return redirect('portail_partenaire:connexion')
    return render(request, 'portail_partenaire/inscription_attente.html', {'partenaire': partenaire})


def inscription(request):
    if get_partenaire_from_session(request):
        return redirect('portail_partenaire:dashboard')

    if request.method == 'POST':
        form = InscriptionForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            request.session['partenaire_inscrit_id'] = user.partenaire.pk

            messages.success(
                request,
                f"Compte créé avec succès ! Bienvenue {user.username} sur "
                f"le portail de {user.partenaire.nom_etablissement}. "
                f"Votre compte est en attente de validation.",
            )
            return redirect('portail_partenaire:inscription_attente')
    else:
        form = InscriptionForm()

    return render(request, 'portail_partenaire/inscription.html', {'form': form})


def deconnexion(request):
    request.session.flush()
    messages.success(request, "Vous êtes déconnecté.")
    return redirect('portail_partenaire:connexion')


def dashboard(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mut_pk = request.GET.get('mutualite')
    if mut_pk:
        try:
            mutualites = mutualites.filter(pk=int(mut_pk))
            request.session['mutualite_active_pk'] = mut_pk
        except (ValueError, TypeError):
            pass
    else:
        active = get_mutualite_active(request, user)
        if active:
            mutualites = mutualites.filter(pk=active.pk)

    factures_qs = Facture.objects.filter(
        mutualite__in=mutualites, partenaire=partenaire,
    )

    stats = {
        'total_factures': factures_qs.count(),
        'en_attente': factures_qs.filter(statut='SOUMIS').count(),
        'validees': factures_qs.filter(statut='VALIDE').count(),
        'payees': factures_qs.filter(statut='PAYE').count(),
        'montant_total': factures_qs.filter(
            statut__in=['VALIDE', 'PAYE'],
        ).aggregate(Sum('montant_total'))['montant_total__sum'] or 0,
        'montant_rembourse': factures_qs.filter(
            statut__in=['VALIDE', 'PAYE'],
        ).aggregate(Sum('montant_mutualite'))['montant_mutualite__sum'] or 0,
    }

    factures_recentes = factures_qs.select_related(
        'affilie', 'mutualite',
    ).order_by('-date_creation')[:10]

    membres_recents = Affilie.objects.filter(
        mutualite__in=mutualites,
        factures__partenaire=partenaire,
    ).distinct().order_by('-date_modification')[:5]

    convention_active = partenaire.convention_active

    # Stats par mutualité
    stats_par_mutualite = []
    for m in get_mutualites_list(user):
        qs_m = Facture.objects.filter(mutualite=m, partenaire=partenaire)
        stats_par_mutualite.append({
            'mutualite': m,
            'total_factures': qs_m.count(),
            'montant_total': qs_m.filter(statut__in=['VALIDE', 'PAYE']).aggregate(
                Sum('montant_total')
            )['montant_total__sum'] or 0,
        })

    # ── Graphiques ────────────────────────────────────────
    # Répartition par statut
    statut_counts = factures_qs.values('statut').annotate(
        count=Count('id')
    ).order_by('statut')
    statut_labels = {'BROUILLON': 'Brouillon', 'SOUMIS': 'Soumise',
                     'VALIDE': 'Validée', 'PAYE': 'Payée', 'REJETE': 'Rejetée'}
    statut_couleurs = {'BROUILLON': '#94a3b8', 'SOUMIS': '#f59e0b',
                       'VALIDE': '#10b981', 'PAYE': '#3b82f6', 'REJETE': '#ef4444'}
    chart_statut = {
        'labels': [statut_labels.get(s['statut'], s['statut']) for s in statut_counts],
        'data': [s['count'] for s in statut_counts],
        'colors': [statut_couleurs.get(s['statut'], '#94a3b8') for s in statut_counts],
    }

    # Factures par mois (6 derniers mois)
    six_mois = timezone.now() - timedelta(days=180)
    mois_data = factures_qs.filter(
        date__gte=six_mois
    ).annotate(
        mois=TruncMonth('date')
    ).values('mois').annotate(
        total=Sum('montant_total'),
        rembourse=Sum('montant_mutualite'),
    ).order_by('mois')

    mois_labels = []
    mois_montants = []
    mois_rembourses = []
    for entry in mois_data:
        mois_labels.append(entry['mois'].strftime('%b %y') if entry['mois'] else '')
        mois_montants.append(float(entry['total'] or 0))
        mois_rembourses.append(float(entry['rembourse'] or 0))

    mutualite_active_obj = get_mutualite_active(request, user)
    return render(request, 'portail_partenaire/dashboard.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'mutualite_active': mut_pk,
        'mutualite_active_obj': mutualite_active_obj,
        'stats': stats,
        'factures_recentes': factures_recentes,
        'membres_recents': membres_recents,
        'convention_active': convention_active,
        'stats_par_mutualite': stats_par_mutualite,
        'chart_statut_json': json.dumps(chart_statut),
        'chart_mois_labels': json.dumps(mois_labels),
        'chart_mois_montants': json.dumps(mois_montants),
        'chart_mois_rembourses': json.dumps(mois_rembourses),
    })


def recherche_membre(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))
    form = RechercheMembreForm(request.GET)
    membres = []
    q = ''

    if form.is_valid():
        q = form.cleaned_data.get('q', '').strip()
        if q:
            base_qs = Affilie.objects.filter(
                mutualite__in=mutualite_ids, supprime=False,
            ).select_related('origine', 'mutualite')

            pk = None
            if '-' in q:
                parts = q.rsplit('-', 1)
                if len(parts) == 2:
                    try:
                        pk = int(parts[1])
                    except ValueError:
                        pk = None
            if pk is None:
                try:
                    pk = int(q)
                except ValueError:
                    pk = None

            filters = Q()
            if pk is not None:
                filters |= Q(pk=pk)
            filters |= Q(numero_carte_identite__icontains=q)
            filters |= Q(numero_affiliation__icontains=q)
            filters |= Q(nom__icontains=q)
            filters |= Q(prenom__icontains=q)
            filters |= Q(telephone__icontains=q)

            membres = list(base_qs.filter(filters).distinct()[:30])

    return render(request, 'portail_partenaire/recherche_membre.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'form': form,
        'membres': membres,
        'q': q,
    })


def detail_membre(request, pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))
    membre = get_object_or_404(
        Affilie.objects.filter(mutualite__in=mutualite_ids, supprime=False),
        pk=pk,
    )
    ayants_droit = AyantDroit.objects.filter(
        mutualite=membre.mutualite, affilie=membre, actif=True,
    )
    factures = Facture.objects.filter(
        mutualite=membre.mutualite, affilie=membre, partenaire=partenaire,
    ).select_related('partenaire').order_by('-date')[:10]

    total_consomme = Facture.objects.filter(
        mutualite=membre.mutualite, affilie=membre,
        statut__in=['SOUMIS', 'VALIDE', 'PAYE'],
    ).aggregate(total=Sum('montant_mutualite'))['total'] or 0

    from core.utils import consommation_mensuelle_affilie
    consommation_mois = consommation_mensuelle_affilie(membre)
    plafond_mensuel = membre.plafond_mensuel
    reste_plafond = (plafond_mensuel - consommation_mois) if plafond_mensuel > 0 else None

    documents = DocumentMedical.objects.filter(
        mutualite=membre.mutualite, affilie=membre,
    ).order_by('-date_creation')[:10]

    # Exclusions pour ce membre
    excluded_service_ids = set()
    excluded_medicament_ids = set()
    exclusions_actives = []
    try:
        from affilies.models import AffilieExclusion
        from origines.models import OrigineExclusion
        from core.models import MutualiteExclusion
        global_excl = MutualiteExclusion.objects.filter(mutualite=membre.mutualite).select_related('medicament', 'service')
        for e in global_excl:
            if e.medicament:
                excluded_medicament_ids.add(e.medicament.pk)
            elif e.service:
                excluded_service_ids.add(e.service.pk)
            exclusions_actives.append(e)
        affilie_excl = AffilieExclusion.objects.filter(affilie=membre).select_related('medicament', 'service')
        for e in affilie_excl:
            if e.medicament:
                excluded_medicament_ids.add(e.medicament.pk)
            elif e.service:
                excluded_service_ids.add(e.service.pk)
            exclusions_actives.append(e)
        if membre.origine:
            origin_excl = OrigineExclusion.objects.filter(origine=membre.origine).select_related('medicament', 'service')
            for e in origin_excl:
                if e.medicament:
                    excluded_medicament_ids.add(e.medicament.pk)
                elif e.service:
                    excluded_service_ids.add(e.service.pk)
                exclusions_actives.append(e)
    except Exception:
        pass

    return render(request, 'portail_partenaire/detail_membre.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'membre': membre,
        'ayants_droit': ayants_droit,
        'factures': factures,
        'documents': documents,
        'total_consomme': total_consomme,
        'consommation_mois': consommation_mois,
        'plafond_mensuel': plafond_mensuel,
        'reste_plafond': reste_plafond,
        'exclusions_actives': exclusions_actives,
        'excluded_service_ids': excluded_service_ids,
        'excluded_medicament_ids': excluded_medicament_ids,
    })


def _montant_mutualite_projete(formset):
    from decimal import Decimal
    total = Decimal('0')
    for ligne_form in formset.forms:
        cleaned = getattr(ligne_form, 'cleaned_data', None)
        if not cleaned or cleaned.get('DELETE'):
            continue
        prix = cleaned.get('prix_unitaire') or Decimal('0')
        quantite = cleaned.get('quantite') or Decimal('1')
        taux = cleaned.get('taux_applique') or Decimal('0')
        total += Decimal(quantite) * Decimal(prix) * Decimal(taux) / Decimal('100')
    return total


def ajouter_facture(request, membre_pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))
    membre = get_object_or_404(
        Affilie.objects.filter(mutualite__in=mutualite_ids, supprime=False),
        pk=membre_pk,
    )
    mutualite = membre.mutualite
    ayants_droit = AyantDroit.objects.filter(
        mutualite=mutualite, affilie=membre, actif=True, supprime=False,
    )

    if request.method == 'POST':
        if membre.bloque or membre.bloque_definitif:
            messages.error(
                request,
                f"Le membre {membre.nom_complet} est bloqué (plafond mensuel atteint). "
                f"La création de facture est refusée."
            )
            return redirect('portail_partenaire:detail_membre', pk=membre.pk)

        form = FactureForm(request.POST)
        formset = LigneFactureFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            facture = form.save(commit=False)
            facture.mutualite = mutualite
            facture.partenaire = partenaire
            facture.affilie = membre
            ayant_droit_id = request.POST.get('ayant_droit_id', '')
            if ayant_droit_id:
                facture.ayant_droit = ayants_droit.filter(pk=ayant_droit_id).first()
            facture.numero = Facture.generer_numero()
            facture.statut = 'BROUILLON'
            facture.save()

            formset.instance = facture
            lignes = formset.save()
            for ligne in lignes:
                if not ligne.mutualite_id:
                    ligne.mutualite = mutualite
                    ligne.save(update_fields=['mutualite'])

            from factures.views import _update_facture_totals
            _update_facture_totals(facture)

            messages.success(
                request,
                f"Facture {facture.numero} enregistrée en brouillon pour {membre.nom_complet}.",
            )
            return redirect('portail_partenaire:detail_facture', pk=facture.pk)
    else:
        form = FactureForm()
        formset = LigneFactureFormSet()

    ayant_droit_preselect = None
    preselection_id = request.GET.get('ayant_droit') or request.GET.get('ayant_droit_id') or ''
    if preselection_id:
        ayant_droit_preselect = ayants_droit.filter(pk=preselection_id).first()

    services = ServiceSante.objects.filter(mutualite=mutualite, actif=True)
    medicaments = Medicament.objects.filter(mutualite=mutualite, actif=True, pris_en_charge=True)
    for ligne_form in formset.forms:
        ligne_form.fields['service'].queryset = services
        ligne_form.fields['medicament'].queryset = medicaments
    medicaments_json = json.dumps([
        {
            'id': m.pk,
            'nom': str(m),
            'prix': float(m.prix_reference or 0),
            'taux': float(m.taux_remboursement or 80),
        }
        for m in medicaments
    ])

    # Exclusions pour ce membre
    excluded_service_ids = set()
    excluded_medicament_ids = set()
    exclusions_actives = []
    try:
        from affilies.models import AffilieExclusion
        from origines.models import OrigineExclusion
        from core.models import MutualiteExclusion
        # Globales
        global_excl = MutualiteExclusion.objects.filter(mutualite=mutualite).select_related('medicament', 'service')
        for e in global_excl:
            if e.medicament:
                excluded_medicament_ids.add(e.medicament.pk)
            elif e.service:
                excluded_service_ids.add(e.service.pk)
            exclusions_actives.append(e)
        # Affilié
        affilie_excl = AffilieExclusion.objects.filter(affilie=membre).select_related('medicament', 'service')
        for e in affilie_excl:
            if e.medicament:
                excluded_medicament_ids.add(e.medicament.pk)
            elif e.service:
                excluded_service_ids.add(e.service.pk)
            exclusions_actives.append(e)
        # Origine
        if membre.origine:
            origin_excl = OrigineExclusion.objects.filter(origine=membre.origine).select_related('medicament', 'service')
            for e in origin_excl:
                if e.medicament:
                    excluded_medicament_ids.add(e.medicament.pk)
                elif e.service:
                    excluded_service_ids.add(e.service.pk)
                exclusions_actives.append(e)
    except Exception:
        pass

    from core.utils import consommation_mensuelle_affilie
    consommation_mois = consommation_mensuelle_affilie(membre)
    plafond_mensuel = membre.plafond_mensuel
    reste_plafond = (plafond_mensuel - consommation_mois) if plafond_mensuel > 0 else None

    return render(request, 'portail_partenaire/ajouter_facture.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'membre': membre,
        'mutualite': mutualite,
        'ayants_droit': ayants_droit,
        'ayant_droit_preselect': ayant_droit_preselect,
        'consommation_mois': consommation_mois,
        'plafond_mensuel': plafond_mensuel,
        'reste_plafond': reste_plafond,
        'form': form,
        'formset': formset,
        'services': services,
        'medicaments': medicaments,
        'medicaments_json': medicaments_json,
        'excluded_service_ids': excluded_service_ids,
        'excluded_medicament_ids': excluded_medicament_ids,
        'exclusions_actives': exclusions_actives,
    })


def ajouter_facture_simple(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite = user.mutualite
    mode = request.GET.get('mode', '')

    if request.method == 'POST':
        mut_pk = request.POST.get('mutualite_id', user.mutualite_id)
        try:
            mutualite = mutualites.get(pk=mut_pk)
        except (ValueError, mutualites.model.DoesNotExist):
            mutualite = user.mutualite

        form = FactureSimpleClientForm(request.POST)
        formset = LigneFactureFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            facture = form.save(commit=False)
            facture.mutualite = mutualite

            if request.POST.get('mode') == 'mutualite':
                mp = Partenaire.objects.filter(mutualite=mutualite).first()
                if not mp:
                    mp = Partenaire.objects.create(
                        mutualite=mutualite,
                        code_partenaire=f"MUT-{mutualite.pk:04d}",
                        nom_etablissement=mutualite.nom,
                        type_partenaire='CENTRE_SANTE',
                    )
                facture.partenaire = mp
            else:
                facture.partenaire = partenaire

            affilie_pk = request.POST.get('affilie_id', '')
            if affilie_pk:
                try:
                    facture.affilie = Affilie.objects.get(
                        pk=affilie_pk, mutualite__in=mutualites
                    )
                except Affilie.DoesNotExist:
                    pass

            if facture.affilie:
                ayant_droit_id = request.POST.get('ayant_droit_id', '')
                if ayant_droit_id:
                    facture.ayant_droit = AyantDroit.objects.filter(
                        affilie=facture.affilie, mutualite=mutualite,
                        actif=True, supprime=False, pk=ayant_droit_id,
                    ).first()

            if facture.affilie and (facture.affilie.bloque or facture.affilie.bloque_definitif):
                messages.error(
                    request,
                    f"Le membre {facture.affilie.nom_complet} est bloqué "
                    f"(plafond mensuel atteint). La création de facture est refusée."
                )
                return redirect('portail_partenaire:detail_membre', pk=facture.affilie.pk)

            facture.numero = Facture.generer_numero()
            facture.statut = 'BROUILLON'
            facture.save()

            formset.instance = facture
            lignes = formset.save()
            for ligne in lignes:
                if not ligne.mutualite_id:
                    ligne.mutualite = mutualite
                    ligne.save(update_fields=['mutualite'])

            from factures.views import _update_facture_totals
            _update_facture_totals(facture)

            nom_client = facture.affilie.nom_complet if facture.affilie else facture.client_nom
            messages.success(request, f"Facture {facture.numero} enregistrée pour {nom_client}.")
            return redirect('portail_partenaire:detail_facture', pk=facture.pk)

    else:
        form = FactureSimpleClientForm()
        formset = LigneFactureFormSet()

    services = ServiceSante.objects.filter(mutualite__in=mutualites, actif=True)
    medicaments = Medicament.objects.filter(mutualite__in=mutualites, actif=True, pris_en_charge=True)
    for ligne_form in formset.forms:
        ligne_form.fields['service'].queryset = services
        ligne_form.fields['medicament'].queryset = medicaments
    medicaments_json = json.dumps([
        {
            'id': m.pk,
            'nom': str(m),
            'mutualite_id': m.mutualite_id,
            'prix': float(m.prix_reference or 0),
            'taux': float(m.taux_remboursement or 80),
        }
        for m in medicaments
    ])

    return render(request, 'portail_partenaire/ajouter_facture_simple.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'mutualite': mutualite,
        'form': form,
        'formset': formset,
        'services': services,
        'medicaments': medicaments,
        'medicaments_json': medicaments_json,
        'mode': mode,
    })


def detail_facture(request, pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))
    facture = get_object_or_404(
        Facture.objects.filter(
            mutualite__in=mutualite_ids, partenaire=partenaire,
        ).select_related('affilie', 'mutualite'),
        pk=pk,
    )

    documents = DocumentMedical.objects.filter(
        mutualite=facture.mutualite, facture=facture,
    ).order_by('-date_creation')

    if request.method == 'POST' and facture.statut == 'BROUILLON':
        action = request.POST.get('action')
        if action == 'soumettre':
            facture.statut = 'SOUMIS'
            facture.save(update_fields=['statut'])
            messages.success(request, f"Facture {facture.numero} soumise pour validation.")
            return redirect('portail_partenaire:detail_facture', pk=facture.pk)

    return render(request, 'portail_partenaire/detail_facture.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'facture': facture,
        'documents': documents,
    })


def imprimer_recu(request, pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))
    facture = get_object_or_404(
        Facture.objects.filter(mutualite__in=mutualite_ids, partenaire=partenaire)
        .select_related('affilie', 'mutualite'),
        pk=pk,
    )

    return render(request, 'portail_partenaire/recu_pos.html', {
        'facture': facture,
        'partenaire': partenaire,
        'mutualite': facture.mutualite,
    })


def export_pdf(request, pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))
    facture = get_object_or_404(
        Facture.objects.filter(mutualite__in=mutualite_ids, partenaire=partenaire)
        .select_related('affilie', 'mutualite'),
        pk=pk,
    )

    html = render_to_string('portail_partenaire/facture_pdf.html', {
        'facture': facture,
        'partenaire': partenaire,
        'mutualite': facture.mutualite,
    })

    try:
        import weasyprint
        pdf_bytes = weasyprint.HTML(string=html).write_pdf()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="facture_{facture.numero}.pdf"'
        return response
    except Exception:
        messages.warning(request, "Génération PDF indisponible. Utilisez l'impression navigateur à la place.")
        return redirect('portail_partenaire:detail_facture', pk=facture.pk)


def affilie_search_json(request):
    user = get_partenaire_from_session(request)
    if not user:
        return JsonResponse([], safe=False)
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    mutualites = get_mutualites_list(user)
    ids = list(mutualites.values_list('pk', flat=True))
    affilies = Affilie.objects.filter(
        mutualite__in=ids, supprime=False, actif=True
    ).filter(
        Q(numero_carte_identite__icontains=q) |
        Q(numero_affiliation__icontains=q) |
        Q(nom__icontains=q) |
        Q(prenom__icontains=q)
    )[:10]
    results = []
    for a in affilies:
        ayants_droit = list(AyantDroit.objects.filter(
            affilie=a, actif=True, supprime=False
        ).values('pk', 'nom', 'prenom', 'lien_parente'))
        results.append({
            'pk': a.pk,
            'nom': a.nom,
            'prenom': a.prenom,
            'nom_complet': a.nom_complet,
            'numero_carte_identite': a.numero_carte_identite,
            'numero_affiliation': a.numero_affiliation,
            'ayants_droit': ayants_droit,
        })
    return JsonResponse(results, safe=False)


def liste_factures(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))

    qs = Facture.objects.filter(
        mutualite__in=mutualite_ids, partenaire=partenaire,
    ).select_related('affilie', 'mutualite').order_by('-date_creation')

    statut = request.GET.get('statut', '')
    if statut:
        qs = qs.filter(statut=statut)

    mois = request.GET.get('mois', '')
    annee = request.GET.get('annee', '')
    if mois:
        qs = qs.filter(date__month=mois)
    if annee:
        qs = qs.filter(date__year=annee)

    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    factures = paginator.get_page(page)

    from datetime import datetime
    annee_courante = datetime.now().year
    annees = [str(a) for a in range(annee_courante, annee_courante - 5, -1)]

    return render(request, 'portail_partenaire/liste_factures.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'factures': factures,
        'statut': statut,
        'mois': mois,
        'annee': annee,
        'mois_choices': [
            (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
            (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
            (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre'),
        ],
        'annees': annees,
        'statut_choices': Facture.STATUT_CHOICES,
    })


def transferer_document(request, membre_pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))
    membre = get_object_or_404(
        Affilie.objects.filter(mutualite__in=mutualite_ids, supprime=False),
        pk=membre_pk,
    )
    mutualite = membre.mutualite

    if request.method == 'POST':
        form = DocumentMedicalForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.mutualite = mutualite
            doc.partenaire = partenaire
            doc.affilie = membre
            doc.cree_par_partenaire = user
            doc.save()
            messages.success(
                request,
                f"Document '{doc.get_type_document_display()}' transféré avec succès.",
            )
            return redirect('portail_partenaire:detail_membre', pk=membre.pk)
    else:
        form = DocumentMedicalForm()

    return render(request, 'portail_partenaire/transferer_document.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'membre': membre,
        'mutualite': mutualite,
        'form': form,
    })


def profil(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    relations = get_relations_partenaire(partenaire)

    return render(request, 'portail_partenaire/profil.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'relations': relations,
    })


def modifier_profil(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)

    if request.method == 'POST':
        form = PartenaireProfilForm(request.POST, request.FILES, instance=partenaire)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos informations ont été mises à jour.")
            return redirect('portail_partenaire:profil')
    else:
        form = PartenaireProfilForm(instance=partenaire)

    return render(request, 'portail_partenaire/modifier_profil.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'form': form,
    })


def configuration_compte(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)

    password_form = ChangerMotDePasseForm()
    info_form = InfoCompteForm(instance=user)

    if request.method == 'POST':
        if 'changer_mot_de_passe' in request.POST:
            password_form = ChangerMotDePasseForm(request.POST)
            if password_form.is_valid():
                if not user.check_password(password_form.cleaned_data['ancien_mot_de_passe']):
                    password_form.add_error('ancien_mot_de_passe', 'Ancien mot de passe incorrect.')
                else:
                    user.password = password_form.cleaned_data['nouveau_mot_de_passe']
                    user.save(update_fields=['password'])
                    messages.success(request, 'Mot de passe modifié avec succès.')
                    return redirect('portail_partenaire:configuration_compte')
        elif 'modifier_infos_compte' in request.POST:
            info_form = InfoCompteForm(request.POST, request.FILES, instance=user)
            if info_form.is_valid():
                info_form.save()
                messages.success(request, 'Informations du compte mises à jour.')
                return redirect('portail_partenaire:configuration_compte')

    return render(request, 'portail_partenaire/configuration_compte.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'password_form': password_form,
        'info_form': info_form,
    })


def creer_utilisateur(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)

    if request.method == 'POST':
        form = CreerUtilisateurForm(request.POST, request.FILES)
        if form.is_valid():
            new_user = form.save(partenaire=partenaire, mutualite=partenaire.mutualite)
            messages.success(request, f"Utilisateur « {new_user.username} » créé avec succès.")
            return redirect('portail_partenaire:configuration_compte')
    else:
        form = CreerUtilisateurForm()

    return render(request, 'portail_partenaire/creer_utilisateur.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'form': form,
    })


@require_POST
def bloquer_relation(request, mutualite_pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    relation = get_object_or_404(
        RelationPartenaireMutualite,
        partenaire=user.partenaire,
        mutualite_id=mutualite_pk,
        statut='ACTIVE',
    )
    relation.statut = 'BLOQUEE'
    relation.date_action = timezone.now()
    relation.bloque_par_partenaire = True
    relation.save(update_fields=['statut', 'date_action', 'bloque_par_partenaire'])
    messages.success(request, f"Relation avec {relation.mutualite.nom} bloquée.")
    return redirect('portail_partenaire:profil')


@require_POST
def debloquer_relation(request, mutualite_pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    relation = get_object_or_404(
        RelationPartenaireMutualite,
        partenaire=user.partenaire,
        mutualite_id=mutualite_pk,
        statut='BLOQUEE',
        bloque_par_partenaire=True,
    )
    relation.statut = 'ACTIVE'
    relation.date_action = timezone.now()
    relation.bloque_par_partenaire = False
    relation.save(update_fields=['statut', 'date_action', 'bloque_par_partenaire'])
    messages.success(request, f"Relation avec {relation.mutualite.nom} rétablie.")
    return redirect('portail_partenaire:profil')


def liste_medicaments(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))

    qs = Medicament.objects.filter(mutualite__in=mutualite_ids).select_related('mutualite')
    q = request.GET.get('q', '')
    forme = request.GET.get('forme', '')

    if q:
        qs = qs.filter(
            Q(nom__icontains=q) | Q(code__icontains=q) | Q(dci__icontains=q)
        )
    if forme:
        qs = qs.filter(forme=forme)

    paginator = Paginator(qs, 15)
    page = request.GET.get('page', 1)
    medicaments = paginator.get_page(page)

    return render(request, 'portail_partenaire/liste_medicaments.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'medicaments': medicaments,
        'q': q,
        'forme': forme,
        'total': qs.count(),
        'forme_choices': Medicament.FORME_CHOICES,
    })


def ajouter_medicament(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite = user.mutualite

    if request.method == 'POST':
        mut_pk = request.POST.get('mutualite_id', user.mutualite_id)
        try:
            mutualite = mutualites.get(pk=mut_pk)
        except (ValueError, mutualites.model.DoesNotExist):
            mutualite = user.mutualite

        form = MedicamentForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mutualite = mutualite
            obj.code = Medicament.generer_code()
            obj.save()
            messages.success(request, f"Médicament {obj.nom} ajouté.")
            return redirect('portail_partenaire:liste_medicaments')
    else:
        form = MedicamentForm(initial={'code': Medicament.generer_code()})

    categories = CategorieMedicament.objects.filter(mutualite__in=mutualites)
    from core.models import Mutualite as MutModel

    return render(request, 'portail_partenaire/medicament_form.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'mutualite': mutualite,
        'form': form,
        'categories': categories,
        'titre': 'Ajouter un médicament',
    })


def modifier_medicament(request, pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))
    obj = get_object_or_404(Medicament.objects.filter(mutualite__in=mutualite_ids), pk=pk)

    if request.method == 'POST':
        form = MedicamentForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"Médicament {obj.nom} modifié.")
            return redirect('portail_partenaire:liste_medicaments')
    else:
        form = MedicamentForm(instance=obj)

    categories = CategorieMedicament.objects.filter(mutualite__in=mutualites)

    return render(request, 'portail_partenaire/medicament_form.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'mutualite': obj.mutualite,
        'form': form,
        'obj': obj,
        'categories': categories,
        'titre': 'Modifier le médicament',
    })


def notification_dismiss(request):
    key = request.GET.get('key') or request.POST.get('key')
    if key:
        dismissed = list(request.session.get('notifications_dismissed', []))
        if key not in dismissed:
            dismissed.append(key)
        request.session['notifications_dismissed'] = dismissed
        request.session.modified = True
        request.session.save()
    return HttpResponse('ok')


def supprimer_medicament(request, pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))
    obj = get_object_or_404(Medicament.objects.filter(mutualite__in=mutualite_ids), pk=pk)

    if request.method == 'POST':
        nom = obj.nom
        obj.delete()
        messages.success(request, f"Médicament {nom} supprimé.")
        return redirect('portail_partenaire:liste_medicaments')

    return render(request, 'portail_partenaire/medicament_confirm_supprimer.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'mutualite': obj.mutualite,
        'obj': obj,
    })


def liste_services(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))

    qs = ServiceSante.objects.filter(mutualite__in=mutualite_ids).select_related('mutualite')
    q = request.GET.get('q', '')
    categorie = request.GET.get('categorie', '')

    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(code__icontains=q))
    if categorie:
        qs = qs.filter(categorie=categorie)

    paginator = Paginator(qs, 15)
    page = request.GET.get('page', 1)
    services = paginator.get_page(page)

    return render(request, 'portail_partenaire/liste_services.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'services': services,
        'q': q,
        'categorie': categorie,
        'total': qs.count(),
        'categorie_choices': ServiceSante.CATEGORIE_CHOICES,
    })


def ajouter_service(request):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite = user.mutualite

    if request.method == 'POST':
        mut_pk = request.POST.get('mutualite_id', user.mutualite_id)
        try:
            mutualite = mutualites.get(pk=mut_pk)
        except (ValueError, mutualites.model.DoesNotExist):
            mutualite = user.mutualite

        form = ServiceSanteForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.code = ServiceSante.generer_code(obj.categorie)
            obj.mutualite = mutualite
            obj.save()
            messages.success(request, f"Service {obj.nom} ajouté.")
            return redirect('portail_partenaire:liste_services')
    else:
        form = ServiceSanteForm(initial={
            'code': ServiceSante.generer_code('AUTRE'),
        })

    return render(request, 'portail_partenaire/service_form.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'mutualite': mutualite,
        'form': form,
        'titre': 'Ajouter un service de santé',
    })


def modifier_service(request, pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))
    obj = get_object_or_404(ServiceSante.objects.filter(mutualite__in=mutualite_ids), pk=pk)

    if request.method == 'POST':
        form = ServiceSanteForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"Service {obj.nom} modifié.")
            return redirect('portail_partenaire:liste_services')
    else:
        form = ServiceSanteForm(instance=obj)

    return render(request, 'portail_partenaire/service_form.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'mutualite': obj.mutualite,
        'form': form,
        'obj': obj,
        'titre': 'Modifier le service',
    })


def supprimer_service(request, pk):
    user = get_partenaire_from_session(request)
    if not user:
        return redirect('portail_partenaire:connexion')

    partenaire = user.partenaire
    mutualites = get_mutualites_list(user)
    mutualite_ids = list(mutualites.values_list('pk', flat=True))
    obj = get_object_or_404(ServiceSante.objects.filter(mutualite__in=mutualite_ids), pk=pk)

    if request.method == 'POST':
        nom = obj.nom
        obj.delete()
        messages.success(request, f"Service {nom} supprimé.")
        return redirect('portail_partenaire:liste_services')

    return render(request, 'portail_partenaire/service_confirm_supprimer.html', {
        'user': user,
        'partenaire': partenaire,
        'mutualites': mutualites,
        'mutualite': obj.mutualite,
        'obj': obj,
    })
