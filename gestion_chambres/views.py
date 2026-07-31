from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from core.mixins import MutualiteRequiredMixin
from .models import TypeChambre, Chambre, Hospitalisation, MouvementChambre, Etablissement, Service, Soin
from .forms import TypeChambreForm, ChambreForm, HospitalisationForm, HospitalisationSortieForm, MouvementChambreForm, EtablissementForm, ServiceForm, SoinForm


# ════════════════════════════════════════════════════════════════
#  TABLEAU DE BORD
# ════════════════════════════════════════════════════════════════

@login_required
def dashboard(request):
    mutualite = request.user.mutualite
    if not mutualite:
        messages.error(request, "Aucune mutualité associée.")
        return redirect('core:dashboard')

    # Statistiques chambres
    chambres = Chambre.objects.filter(mutualite=mutualite)
    stats_chambres = {
        'total': chambres.count(),
        'libres': chambres.filter(statut='LIBRE').count(),
        'occupees': chambres.filter(statut='OCCUPEE').count(),
        'maintenance': chambres.filter(statut='MAINTENANCE').count(),
        'reservees': chambres.filter(statut='RESERVEE').count(),
        'hors_service': chambres.filter(statut='HORS_SERVICE').count(),
    }

    # Hospitalisations en cours
    hospitalisations_actives = Hospitalisation.objects.filter(
        mutualite=mutualite, statut__in=['EN_COURS', 'PROLONGEE']
    ).select_related('chambre', 'chambre__type_chambre')

    # Hospitalisations prévues (prochains 7 jours)
    hospitalisations_prevues = Hospitalisation.objects.filter(
        mutualite=mutualite, statut='PREVUE',
        date_entree__gte=timezone.now(),
        date_entree__lte=timezone.now() + timezone.timedelta(days=7)
    ).select_related('chambre', 'chambre__type_chambre').order_by('date_entree')[:10]

    # Par type de chambre
    par_type = chambres.values('type_chambre__nom').annotate(
        total=Count('id'),
        libres=Count('id', filter=Q(statut='LIBRE')),
        occupees=Count('id', filter=Q(statut='OCCUPEE'))
    ).order_by('type_chambre__nom')

    context = {
        'stats_chambres': stats_chambres,
        'hospitalisations_actives': hospitalisations_actives,
        'hospitalisations_prevues': hospitalisations_prevues,
        'par_type': par_type,
    }
    return render(request, 'gestion_chambres/dashboard.html', context)


# ════════════════════════════════════════════════════════════════
#  TYPES DE CHAMBRES
# ════════════════════════════════════════════════════════════════

@login_required
def type_chambre_liste(request):
    mutualite = request.user.mutualite
    types = TypeChambre.objects.filter(mutualite=mutualite).order_by('ordre', 'nom')
    return render(request, 'gestion_chambres/type_chambre_liste.html', {'types': types})


@login_required
def type_chambre_creer(request):
    if request.method == 'POST':
        form = TypeChambreForm(request.POST)
        if form.is_valid():
            type_chambre = form.save(commit=False)
            type_chambre.mutualite = request.user.mutualite
            type_chambre.save()
            messages.success(request, f"Type de chambre « {type_chambre.nom} » créé.")
            return redirect('gestion_chambres:type_chambre_liste')
    else:
        form = TypeChambreForm(initial={'mutualite': request.user.mutualite})
    return render(request, 'gestion_chambres/type_chambre_form.html', {'form': form, 'titre': 'Nouveau type de chambre'})


@login_required
def type_chambre_modifier(request, pk):
    type_chambre = get_object_or_404(TypeChambre, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = TypeChambreForm(request.POST, instance=type_chambre)
        if form.is_valid():
            form.save()
            messages.success(request, f"Type de chambre « {type_chambre.nom} » modifié.")
            return redirect('gestion_chambres:type_chambre_liste')
    else:
        form = TypeChambreForm(instance=type_chambre)
    return render(request, 'gestion_chambres/type_chambre_form.html', {'form': form, 'titre': f'Modifier {type_chambre.nom}'})


@login_required
def type_chambre_supprimer(request, pk):
    type_chambre = get_object_or_404(TypeChambre, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        nom = type_chambre.nom
        type_chambre.delete()
        messages.success(request, f"Type de chambre « {nom} » supprimé.")
        return redirect('gestion_chambres:type_chambre_liste')
    return render(request, 'gestion_chambres/confirm_delete.html', {'objet': type_chambre})


# ════════════════════════════════════════════════════════════════
#  CHAMBRES
# ════════════════════════════════════════════════════════════════

@login_required
def chambre_liste(request):
    mutualite = request.user.mutualite
    chambres = Chambre.objects.filter(mutualite=mutualite).select_related('type_chambre')

    # Filtres
    statut = request.GET.get('statut')
    type_chambre_id = request.GET.get('type_chambre')
    etage = request.GET.get('etage')

    if statut:
        chambres = chambres.filter(statut=statut)
    if type_chambre_id:
        chambres = chambres.filter(type_chambre_id=type_chambre_id)
    if etage:
        chambres = chambres.filter(etage=etage)

    types = TypeChambre.objects.filter(mutualite=mutualite)
    etages = chambres.values_list('etage', flat=True).distinct()

    context = {
        'chambres': chambres,
        'types': types,
        'etages': etages,
        'filtres': {'statut': statut, 'type_chambre': type_chambre_id, 'etage': etage},
    }
    return render(request, 'gestion_chambres/chambre_liste.html', context)


@login_required
def chambre_detail(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk, mutualite=request.user.mutualite)
    hospitalisation_active = chambre.hospitalisation_active
    historiques = chambre.mouvements.select_related('hospitalisation', 'utilisateur')[:20]

    context = {
        'chambre': chambre,
        'hospitalisation_active': hospitalisation_active,
        'historiques': historiques,
    }
    return render(request, 'gestion_chambres/chambre_detail.html', context)


@login_required
def chambre_creer(request):
    if request.method == 'POST':
        form = ChambreForm(request.POST)
        if form.is_valid():
            chambre = form.save(commit=False)
            chambre.mutualite = request.user.mutualite
            chambre.save()
            messages.success(request, f"Chambre « {chambre.numero} » créée.")
            return redirect('gestion_chambres:chambre_liste')
    else:
        form = ChambreForm(initial={'mutualite': request.user.mutualite, 'statut': 'LIBRE'})
    return render(request, 'gestion_chambres/chambre_form.html', {'form': form, 'titre': 'Nouvelle chambre'})


@login_required
def chambre_modifier(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = ChambreForm(request.POST, instance=chambre)
        if form.is_valid():
            form.save()
            messages.success(request, f"Chambre « {chambre.numero} » modifiée.")
            return redirect('gestion_chambres:chambre_detail', pk=chambre.pk)
    else:
        form = ChambreForm(instance=chambre)
    return render(request, 'gestion_chambres/chambre_form.html', {'form': form, 'titre': f'Modifier {chambre}', 'chambre': chambre})


@login_required
def chambre_changer_statut(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        ancien = chambre.statut
        nouveau = request.POST.get('statut')
        if nouveau in dict(Chambre.STATUT_CHOICES):
            if chambre.statut == 'OCCUPEE' and nouveau != 'OCCUPEE' and chambre.hospitalisation_active:
                messages.error(request, "Impossible : un patient occupe cette chambre.")
            else:
                chambre.statut = nouveau
                chambre.save()
                MouvementChambre.objects.create(
                    mutualite=request.user.mutualite,
                    chambre=chambre,
                    type_mouvement='CHANGEMENT_STATUT',
                    ancien_statut=ancien,
                    nouveau_statut=nouveau,
                    utilisateur=request.user,
                    commentaire=f"Changement manuel de {ancien} vers {nouveau}"
                )
                messages.success(request, f"Statut changé : {ancien} → {nouveau}")
    return redirect('gestion_chambres:chambre_detail', pk=chambre.pk)


# ════════════════════════════════════════════════════════════════
#  HOSPITALISATIONS
# ════════════════════════════════════════════════════════════════

@login_required
def hospitalisation_liste(request):
    mutualite = request.user.mutualite
    hospitalisations = Hospitalisation.objects.filter(mutualite=mutualite).select_related('chambre', 'chambre__type_chambre')

    statut = request.GET.get('statut')
    if statut:
        hospitalisations = hospitalisations.filter(statut=statut)

    q = request.GET.get('q')
    if q:
        hospitalisations = hospitalisations.filter(
            Q(patient_nom__icontains=q) | Q(patient_prenom__icontains=q) |
            Q(numero_dossier__icontains=q) | Q(chambre__numero__icontains=q)
        )

    context = {
        'hospitalisations': hospitalisations,
        'statut_filtre': statut,
        'q': q,
    }
    return render(request, 'gestion_chambres/hospitalisation_liste.html', context)


@login_required
def hospitalisation_detail(request, pk):
    hosp = get_object_or_404(Hospitalisation, pk=pk, mutualite=request.user.mutualite)
    mouvements = hosp.mouvements.select_related('chambre', 'utilisateur')
    return render(request, 'gestion_chambres/hospitalisation_detail.html', {
        'hospitalisation': hosp,
        'mouvements': mouvements,
    })


@login_required
def hospitalisation_creer(request):
    if request.method == 'POST':
        form = HospitalisationForm(request.POST, mutualite=request.user.mutualite)
        if form.is_valid():
            hosp = form.save(commit=False)
            hosp.mutualite = request.user.mutualite
            hosp.created_by = request.user
            hosp.statut = 'EN_COURS'
            hosp.save()

            # Mettre à jour la chambre
            chambre = hosp.chambre
            chambre.statut = 'OCCUPEE'
            chambre.save(update_fields=['statut'])

            MouvementChambre.objects.create(
                mutualite=request.user.mutualite,
                chambre=chambre,
                hospitalisation=hosp,
                type_mouvement='ENTREE',
                ancien_statut='LIBRE',
                nouveau_statut='OCCUPEE',
                utilisateur=request.user,
                commentaire=f"Admission de {hosp.patient_nom} {hosp.patient_prenom}"
            )

            messages.success(request, f"Hospitalisation {hosp.numero_dossier} créée.")
            return redirect('gestion_chambres:hospitalisation_detail', pk=hosp.pk)
    else:
        form = HospitalisationForm(mutualite=request.user.mutualite, initial={'date_entree': timezone.now()})
    return render(request, 'gestion_chambres/hospitalisation_form.html', {'form': form, 'titre': 'Nouvelle hospitalisation'})


@login_required
def hospitalisation_sortie(request, pk):
    hosp = get_object_or_404(Hospitalisation, pk=pk, mutualite=request.user.mutualite)
    if hosp.statut not in ['EN_COURS', 'PROLONGEE']:
        messages.error(request, "Cette hospitalisation n'est pas en cours.")
        return redirect('gestion_chambres:hospitalisation_detail', pk=hosp.pk)

    if request.method == 'POST':
        form = HospitalisationSortieForm(request.POST, instance=hosp)
        if form.is_valid():
            hosp = form.save(commit=False)
            hosp.terminer(
                mode_sortie=form.cleaned_data['mode_sortie'],
                diagnostic_sortie=form.cleaned_data['diagnostic_sortie'],
                user=request.user
            )
            MouvementChambre.objects.create(
                mutualite=request.user.mutualite,
                chambre=hosp.chambre,
                hospitalisation=hosp,
                type_mouvement='SORTIE',
                ancien_statut='OCCUPEE',
                nouveau_statut='LIBRE',
                utilisateur=request.user,
                commentaire=f"Sortie : {hosp.get_mode_sortie_display()}"
            )
            messages.success(request, f"Sortie enregistrée pour {hosp.patient_nom} {hosp.patient_prenom}.")
            return redirect('gestion_chambres:hospitalisation_detail', pk=hosp.pk)
    else:
        form = HospitalisationSortieForm(instance=hosp, initial={'date_sortie_reelle': timezone.now()})

    return render(request, 'gestion_chambres/hospitalisation_sortie.html', {'form': form, 'hospitalisation': hosp})


@login_required
def hospitalisation_prolonger(request, pk):
    hosp = get_object_or_404(Hospitalisation, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        nouvelle_date = request.POST.get('date_sortie_prevue')
        if nouvelle_date:
            hosp.prolonger(nouvelle_date)
            messages.success(request, "Hospitalisation prolongée.")
    return redirect('gestion_chambres:hospitalisation_detail', pk=hosp.pk)


@login_required
def hospitalisation_transfert(request, pk):
    hosp = get_object_or_404(Hospitalisation, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        nouvelle_chambre_id = request.POST.get('chambre')
        nouvelle_chambre = get_object_or_404(Chambre, pk=nouvelle_chambre_id, mutualite=request.user.mutualite, statut='LIBRE')

        ancienne_chambre = hosp.chambre
        ancienne_chambre.statut = 'LIBRE'
        ancienne_chambre.save(update_fields=['statut'])

        nouvelle_chambre.statut = 'OCCUPEE'
        nouvelle_chambre.save(update_fields=['statut'])

        hosp.chambre = nouvelle_chambre
        hosp.save(update_fields=['chambre'])

        MouvementChambre.objects.create(
            mutualite=request.user.mutualite,
            chambre=ancienne_chambre,
            hospitalisation=hosp,
            type_mouvement='TRANSFERT_SORTANT',
            ancien_statut='OCCUPEE',
            nouveau_statut='LIBRE',
            utilisateur=request.user,
            commentaire=f"Transfert vers {nouvelle_chambre}"
        )
        MouvementChambre.objects.create(
            mutualite=request.user.mutualite,
            chambre=nouvelle_chambre,
            hospitalisation=hosp,
            type_mouvement='TRANSFERT_ENTRANT',
            ancien_statut='LIBRE',
            nouveau_statut='OCCUPEE',
            utilisateur=request.user,
            commentaire=f"Transfert depuis {ancienne_chambre}"
        )

        messages.success(request, f"Patient transféré de {ancienne_chambre} vers {nouvelle_chambre}.")
        return redirect('gestion_chambres:hospitalisation_detail', pk=hosp.pk)

    chambres_libres = Chambre.objects.filter(mutualite=request.user.mutualite, statut='LIBRE').exclude(pk=hosp.chambre.pk)
    return render(request, 'gestion_chambres/hospitalisation_transfert.html', {
        'hospitalisation': hosp,
        'chambres_libres': chambres_libres,
    })


# ════════════════════════════════════════════════════════════════
#  ÉTABLISSEMENTS
# ════════════════════════════════════════════════════════════════

@login_required
def etablissement_liste(request):
    mutualite = request.user.mutualite
    etablissements = Etablissement.objects.filter(mutualite=mutualite).annotate(
        nb_services=Count('services'),
        nb_chambres=Count('chambres'),
        nb_chambres_libres=Count('chambres', filter=Q(chambres__statut='LIBRE')),
    ).order_by('nom')
    return render(request, 'gestion_chambres/etablissement_liste.html', {'etablissements': etablissements})


@login_required
def etablissement_creer(request):
    if request.method == 'POST':
        form = EtablissementForm(request.POST)
        if form.is_valid():
            etablissement = form.save(commit=False)
            etablissement.mutualite = request.user.mutualite
            etablissement.save()
            messages.success(request, f"Établissement « {etablissement.nom} » créé.")
            return redirect('gestion_chambres:etablissement_liste')
    else:
        form = EtablissementForm(initial={'mutualite': request.user.mutualite})
    return render(request, 'gestion_chambres/etablissement_form.html', {'form': form, 'titre': 'Nouvel établissement'})


@login_required
def etablissement_modifier(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = EtablissementForm(request.POST, instance=etablissement)
        if form.is_valid():
            form.save()
            messages.success(request, f"Établissement « {etablissement.nom} » modifié.")
            return redirect('gestion_chambres:etablissement_liste')
    else:
        form = EtablissementForm(instance=etablissement)
    return render(request, 'gestion_chambres/etablissement_form.html', {'form': form, 'titre': f'Modifier {etablissement.nom}'})


@login_required
def etablissement_supprimer(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        nom = etablissement.nom
        etablissement.delete()
        messages.success(request, f"Établissement « {nom} » supprimé.")
        return redirect('gestion_chambres:etablissement_liste')
    return render(request, 'gestion_chambres/confirm_delete.html', {'objet': etablissement})


# ════════════════════════════════════════════════════════════════
#  SERVICES
# ════════════════════════════════════════════════════════════════

@login_required
def service_liste(request):
    mutualite = request.user.mutualite
    services = Service.objects.filter(mutualite=mutualite).select_related('etablissement').annotate(
        nb_chambres=Count('chambres'),
        chambres_libres=Count('chambres', filter=Q(chambres__statut='LIBRE')),
    ).order_by('etablissement', 'ordre', 'nom')
    return render(request, 'gestion_chambres/service_liste.html', {'services': services})


@login_required
def service_creer(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST, mutualite=request.user.mutualite)
        if form.is_valid():
            service = form.save(commit=False)
            service.mutualite = request.user.mutualite
            service.save()
            messages.success(request, f"Service « {service.nom} » créé.")
            return redirect('gestion_chambres:service_liste')
    else:
        form = ServiceForm(mutualite=request.user.mutualite, initial={'mutualite': request.user.mutualite})
    return render(request, 'gestion_chambres/service_form.html', {'form': form, 'titre': 'Nouveau service'})


@login_required
def service_modifier(request, pk):
    service = get_object_or_404(Service, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service, mutualite=request.user.mutualite)
        if form.is_valid():
            form.save()
            messages.success(request, f"Service « {service.nom} » modifié.")
            return redirect('gestion_chambres:service_liste')
    else:
        form = ServiceForm(instance=service, mutualite=request.user.mutualite)
    return render(request, 'gestion_chambres/service_form.html', {'form': form, 'titre': f'Modifier {service.nom}'})


@login_required
def service_supprimer(request, pk):
    service = get_object_or_404(Service, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        nom = service.nom
        service.delete()
        messages.success(request, f"Service « {nom} » supprimé.")
        return redirect('gestion_chambres:service_liste')
    return render(request, 'gestion_chambres/confirm_delete.html', {'objet': service})


# ════════════════════════════════════════════════════════════════
#  SOINS
# ════════════════════════════════════════════════════════════════

@login_required
def soin_liste(request, hospitalisation_pk):
    hospitalisation = get_object_or_404(Hospitalisation, pk=hospitalisation_pk, mutualite=request.user.mutualite)
    soins = hospitalisation.soins_realises.select_related('realise_par').order_by('-date_heure')
    return render(request, 'gestion_chambres/soin_liste.html', {'hospitalisation': hospitalisation, 'soins': soins})


@login_required
def soin_creer(request, hospitalisation_pk):
    hospitalisation = get_object_or_404(Hospitalisation, pk=hospitalisation_pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = SoinForm(request.POST, mutualite=request.user.mutualite)
        if form.is_valid():
            soin = form.save(commit=False)
            soin.mutualite = request.user.mutualite
            soin.hospitalisation = hospitalisation
            soin.realise_par = request.user
            soin.save()
            messages.success(request, f"Soin ajouté.")
            return redirect('gestion_chambres:soin_liste', hospitalisation_pk=hospitalisation.pk)
    else:
        form = SoinForm(mutualite=request.user.mutualite, initial={'hospitalisation': hospitalisation, 'date_heure': timezone.now()})
        form.fields['hospitalisation'].widget = forms.HiddenInput()
    return render(request, 'gestion_chambres/soin_form.html', {'form': form, 'titre': 'Nouveau soin', 'hospitalisation': hospitalisation})


@login_required
def soin_modifier(request, pk):
    soin = get_object_or_404(Soin, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = SoinForm(request.POST, instance=soin, mutualite=request.user.mutualite)
        if form.is_valid():
            form.save()
            messages.success(request, f"Soin modifié.")
            return redirect('gestion_chambres:soin_liste', hospitalisation_pk=soin.hospitalisation.pk)
    else:
        form = SoinForm(instance=soin, mutualite=request.user.mutualite)
        form.fields['hospitalisation'].widget = forms.HiddenInput()
    return render(request, 'gestion_chambres/soin_form.html', {'form': form, 'titre': f'Modifier soin', 'hospitalisation': soin.hospitalisation})


@login_required
def soin_supprimer(request, pk):
    soin = get_object_or_404(Soin, pk=pk, mutualite=request.user.mutualite)
    hosp_pk = soin.hospitalisation.pk
    if request.method == 'POST':
        soin.delete()
        messages.success(request, f"Soin supprimé.")
        return redirect('gestion_chambres:soin_liste', hospitalisation_pk=hosp_pk)
    return render(request, 'gestion_chambres/confirm_delete.html', {'objet': soin})


# ════════════════════════════════════════════════════════════════
#  API / AJAX
# ════════════════════════════════════════════════════════════════
#  ÉTABLISSEMENTS
# ════════════════════════════════════════════════════════════════

@login_required
def etablissement_liste(request):
    mutualite = request.user.mutualite
    etablissements = Etablissement.objects.filter(mutualite=mutualite).order_by('nom')
    return render(request, 'gestion_chambres/etablissement_liste.html', {'etablissements': etablissements})


@login_required
def etablissement_creer(request):
    if request.method == 'POST':
        form = EtablissementForm(request.POST)
        if form.is_valid():
            etablissement = form.save(commit=False)
            etablissement.mutualite = request.user.mutualite
            etablissement.save()
            messages.success(request, f"Établissement « {etablissement.nom} » créé.")
            return redirect('gestion_chambres:etablissement_liste')
    else:
        form = EtablissementForm(initial={'mutualite': request.user.mutualite})
    return render(request, 'gestion_chambres/etablissement_form.html', {'form': form, 'titre': 'Nouvel établissement'})


@login_required
def etablissement_modifier(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = EtablissementForm(request.POST, instance=etablissement)
        if form.is_valid():
            form.save()
            messages.success(request, f"Établissement « {etablissement.nom} » modifié.")
            return redirect('gestion_chambres:etablissement_liste')
    else:
        form = EtablissementForm(instance=etablissement)
    return render(request, 'gestion_chambres/etablissement_form.html', {'form': form, 'titre': f'Modifier {etablissement.nom}'})


@login_required
def etablissement_supprimer(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        nom = etablissement.nom
        etablissement.delete()
        messages.success(request, f"Établissement « {nom} » supprimé.")
        return redirect('gestion_chambres:etablissement_liste')
    return render(request, 'gestion_chambres/confirm_delete.html', {'objet': etablissement})


# ════════════════════════════════════════════════════════════════
#  SERVICES
# ════════════════════════════════════════════════════════════════

@login_required
def service_liste(request):
    mutualite = request.user.mutualite
    services = Service.objects.filter(mutualite=mutualite).select_related('etablissement').order_by('etablissement', 'ordre', 'nom')
    return render(request, 'gestion_chambres/service_liste.html', {'services': services})


@login_required
def service_creer(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST, mutualite=request.user.mutualite)
        if form.is_valid():
            service = form.save(commit=False)
            service.mutualite = request.user.mutualite
            service.save()
            messages.success(request, f"Service « {service.nom} » créé.")
            return redirect('gestion_chambres:service_liste')
    else:
        form = ServiceForm(mutualite=request.user.mutualite)
    return render(request, 'gestion_chambres/service_form.html', {'form': form, 'titre': 'Nouveau service'})


@login_required
def service_modifier(request, pk):
    service = get_object_or_404(Service, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service, mutualite=request.user.mutualite)
        if form.is_valid():
            form.save()
            messages.success(request, f"Service « {service.nom} » modifié.")
            return redirect('gestion_chambres:service_liste')
    else:
        form = ServiceForm(instance=service, mutualite=request.user.mutualite)
    return render(request, 'gestion_chambres/service_form.html', {'form': form, 'titre': f'Modifier {service.nom}'})


@login_required
def service_supprimer(request, pk):
    service = get_object_or_404(Service, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        nom = service.nom
        service.delete()
        messages.success(request, f"Service « {nom} » supprimé.")
        return redirect('gestion_chambres:service_liste')
    return render(request, 'gestion_chambres/confirm_delete.html', {'objet': service})


# ════════════════════════════════════════════════════════════════
#  SOINS
# ════════════════════════════════════════════════════════════════

@login_required
def soin_liste(request, hospitalisation_pk):
    hospitalisation = get_object_or_404(Hospitalisation, pk=hospitalisation_pk, mutualite=request.user.mutualite)
    soins = hospitalisation.soins_realises.select_related('realise_par').order_by('-date_heure')
    return render(request, 'gestion_chambres/soin_liste.html', {'hospitalisation': hospitalisation, 'soins': soins})


@login_required
def soin_creer(request, hospitalisation_pk):
    hospitalisation = get_object_or_404(Hospitalisation, pk=hospitalisation_pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = SoinForm(request.POST)
        if form.is_valid():
            soin = form.save(commit=False)
            soin.hospitalisation = hospitalisation
            soin.mutualite = request.user.mutualite
            soin.realise_par = request.user
            soin.save()
            messages.success(request, f"Soin ajouté.")
            return redirect('gestion_chambres:soin_liste', hospitalisation_pk=hospitalisation.pk)
    else:
        form = SoinForm(initial={'hospitalisation': hospitalisation, 'date_heure': timezone.now()})
    return render(request, 'gestion_chambres/soin_form.html', {'form': form, 'hospitalisation': hospitalisation, 'titre': 'Nouveau soin'})


@login_required
def soin_modifier(request, pk):
    soin = get_object_or_404(Soin, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = SoinForm(request.POST, instance=soin)
        if form.is_valid():
            form.save()
            messages.success(request, f"Soin modifié.")
            return redirect('gestion_chambres:soin_liste', hospitalisation_pk=soin.hospitalisation.pk)
    else:
        form = SoinForm(instance=soin)
    return render(request, 'gestion_chambres/soin_form.html', {'form': form, 'hospitalisation': soin.hospitalisation, 'titre': f'Modifier soin'})


@login_required
def soin_supprimer(request, pk):
    soin = get_object_or_404(Soin, pk=pk, mutualite=request.user.mutualite)
    hospitalisation_pk = soin.hospitalisation.pk
    if request.method == 'POST':
        soin.delete()
        messages.success(request, f"Soin supprimé.")
        return redirect('gestion_chambres:soin_liste', hospitalisation_pk=hospitalisation_pk)
    return render(request, 'gestion_chambres/confirm_delete.html', {'objet': soin})


# ════════════════════════════════════════════════════════════════
#  API / AJAX
# ════════════════════════════════════════════════════════════════

@login_required
@require_POST
def api_chambres_disponibles(request):
    type_id = request.POST.get('type_chambre')
    qs = Chambre.objects.filter(mutualite=request.user.mutualite, statut='LIBRE')
    if type_id:
        qs = qs.filter(type_chambre_id=type_id)
    data = [{'id': c.id, 'numero': c.numero, 'etage': c.etage, 'aile': c.aile, 'type': c.type_chambre.nom} for c in qs]
    return JsonResponse({'chambres': data})


@login_required
@require_POST
def api_occuper_chambre(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk, mutualite=request.user.mutualite)
    if chambre.statut != 'LIBRE':
        return JsonResponse({'success': False, 'error': 'Chambre non disponible'}, status=400)
    chambre.statut = 'OCCUPEE'
    chambre.save(update_fields=['statut'])
    MouvementChambre.objects.create(
        mutualite=request.user.mutualite,
        chambre=chambre,
        type_mouvement='ENTREE',
        ancien_statut='LIBRE',
        nouveau_statut='OCCUPEE',
        utilisateur=request.user,
        commentaire="Occupation rapide via API"
    )
    return JsonResponse({'success': True, 'statut': 'OCCUPEE'})


@login_required
@require_POST
def api_liberer_chambre(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk, mutualite=request.user.mutualite)
    if chambre.statut != 'OCCUPEE':
        return JsonResponse({'success': False, 'error': 'Chambre non occupée'}, status=400)
    chambre.statut = 'LIBRE'
    chambre.save(update_fields=['statut'])
    MouvementChambre.objects.create(
        mutualite=request.user.mutualite,
        chambre=chambre,
        type_mouvement='SORTIE',
        ancien_statut='OCCUPEE',
        nouveau_statut='LIBRE',
        utilisateur=request.user,
        commentaire="Libération rapide via API"
    )
    return JsonResponse({'success': True, 'statut': 'LIBRE'})