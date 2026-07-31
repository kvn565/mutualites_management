# ayants_droit/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import AyantDroit
from .forms import AyantDroitForm
from core.mixins import enregistrer_audit


@login_required
def liste(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')

    from .models import radier_majeurs
    radier_majeurs()

    qs = AyantDroit.objects.filter(mutualite=request.user.mutualite, supprime=False).select_related('affilie')

    q = request.GET.get('q', '')
    lien = request.GET.get('lien', '')
    statut = request.GET.get('statut', '')

    if q:
        qs = qs.filter(
            Q(nom__icontains=q) | Q(prenom__icontains=q) |
            Q(affilie__nom__icontains=q) | Q(affilie__numero_affiliation__icontains=q)
        )
    if lien:
        qs = qs.filter(lien_parente=lien)
    if statut:
        qs = qs.filter(statut=statut)

    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    ayants = paginator.get_page(page)

    return render(request, 'ayants_droit/liste.html', {
        'ayants': ayants,
        'q': q,
        'lien': lien,
        'statut': statut,
        'total': qs.count(),
        'lien_choices': AyantDroit.LIEN_CHOICES,
        'statut_choices': AyantDroit.STATUT_CHOICES,
    })


@login_required
def ajouter(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Vous êtes en mode consultation.")
        return redirect('ayants_droit:liste')

    # Pré-sélectionner l'affilié si passé en paramètre
    initial = {}
    affilie_id = request.GET.get('affilie')
    if affilie_id:
        initial['affilie'] = affilie_id

    form = AyantDroitForm(request.POST or None, user=request.user, initial=initial)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        enregistrer_audit(request, 'CREATION', 'ayants_droit',
                          f"Création ayant droit : {obj.nom_complet}", 'AyantDroit', obj.pk)
        messages.success(request, f"✅ Ayant droit {obj.nom_complet} ajouté avec succès.")
        return redirect('ayants_droit:liste')

    return render(request, 'ayants_droit/form.html', {'form': form, 'titre': 'Ajouter un ayant droit'})


@login_required
def modifier(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Vous êtes en mode consultation.")
        return redirect('ayants_droit:liste')

    obj = get_object_or_404(AyantDroit, pk=pk, supprime=False, mutualite=request.user.mutualite)
    form = AyantDroitForm(request.POST or None, instance=obj, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        enregistrer_audit(request, 'MODIFICATION', 'ayants_droit',
                          f"Modification ayant droit : {obj.nom_complet}", 'AyantDroit', obj.pk)
        messages.success(request, f"✅ Ayant droit {obj.nom_complet} modifié.")
        return redirect('ayants_droit:liste')

    return render(request, 'ayants_droit/form.html', {'form': form, 'obj': obj, 'titre': 'Modifier ayant droit'})


@login_required
def supprimer(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_supprimer:
        messages.error(request, "⛔ Permission insuffisante.")
        return redirect('ayants_droit:liste')

    obj = get_object_or_404(AyantDroit, pk=pk, is_deleted=False, mutualite=request.user.mutualite)
    if request.method == 'POST':
        nom = obj.nom_complet
        obj.delete(user=request.user)
        enregistrer_audit(request, 'SUPPRESSION', 'ayants_droit',
                          f"Suppression ayant droit : {nom}", 'AyantDroit', pk)
        messages.success(request, f"🗑️ {nom} déplacé vers la corbeille.")
        return redirect('ayants_droit:liste')

    return render(request, 'ayants_droit/confirm_supprimer.html', {'obj': obj})
