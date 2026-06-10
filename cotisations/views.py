# cotisations/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone

from .models import Cotisation
from .forms import CotisationForm
from core.mixins import enregistrer_audit

@login_required
def liste(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    qs = Cotisation.objects.filter(mutualite=request.user.mutualite).select_related('affilie')
    
    q = request.GET.get('q', '')
    statut = request.GET.get('statut', '')
    annee = request.GET.get('annee', '')
    
    if q:
        qs = qs.filter(
            Q(reference__icontains=q) | 
            Q(affilie__nom__icontains=q) |
            Q(affilie__numero_affiliation__icontains=q)
        )
    if statut:
        qs = qs.filter(statut=statut)
    if annee:
        qs = qs.filter(annee=annee)
        
    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    cotisations = paginator.get_page(page)
    
    return render(request, 'cotisations/liste.html', {
        'cotisations': cotisations,
        'q': q,
        'statut': statut,
        'annee': annee,
        'total': qs.count(),
        'statut_choices': Cotisation.STATUT_CHOICES,
    })

@login_required
def ajouter(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('cotisations:liste')
        
    if request.method == 'POST':
        form = CotisationForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            if not obj.reference:
                obj.reference = Cotisation.generer_reference()
            obj.enregistre_par = request.user
            obj.save()
            enregistrer_audit(request, 'CREATION', 'cotisations', f"Paiement cotisation : {obj.reference}", 'Cotisation', obj.pk)
            messages.success(request, f"✅ Cotisation {obj.reference} enregistrée avec succès.")
            return redirect('cotisations:liste')
    else:
        form = CotisationForm(initial={'reference': Cotisation.generer_reference()})
        
    return render(request, 'cotisations/form.html', {'form': form, 'titre': 'Enregistrer une cotisation'})

@login_required
def modifier(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('cotisations:liste')
        
    obj = get_object_or_404(Cotisation, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = CotisationForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            enregistrer_audit(request, 'MODIFICATION', 'cotisations', f"Modification cotisation : {obj.reference}", 'Cotisation', obj.pk)
            messages.success(request, f"✅ Cotisation {obj.reference} modifiée.")
            return redirect('cotisations:liste')
    else:
        form = CotisationForm(instance=obj)
        
    return render(request, 'cotisations/form.html', {'form': form, 'obj': obj, 'titre': 'Modifier la cotisation'})

@login_required
def supprimer(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_supprimer:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('cotisations:liste')
        
    obj = get_object_or_404(Cotisation, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        reference = obj.reference
        obj.delete()
        enregistrer_audit(request, 'SUPPRESSION', 'cotisations', f"Suppression cotisation : {reference}", 'Cotisation', pk)
        messages.success(request, f"🗑️ Cotisation {reference} supprimée.")
        return redirect('cotisations:liste')
        
    return render(request, 'cotisations/confirm_supprimer.html', {'obj': obj})


@login_required
def detail(request, pk):
    """Détail d'une cotisation."""
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    cotisation = get_object_or_404(Cotisation.objects.select_related('affilie', 'enregistre_par'), pk=pk, mutualite=request.user.mutualite)
    return render(request, 'cotisations/detail.html', {'cotisation': cotisation})


@login_required
def journal(request):
    """Journal mensuel des cotisations payées."""
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    now = timezone.now()
    annee = int(request.GET.get('annee', now.year))
    mois = request.GET.get('mois', '')

    qs = Cotisation.objects.filter(mutualite=request.user.mutualite, statut='PAYE', annee=annee).select_related('affilie')
    if mois:
        try:
            qs = qs.filter(mois=int(mois))
        except ValueError:
            pass

    total_montant = qs.aggregate(total=Sum('montant'))['total'] or 0
    nb_paiements = qs.count()

    paginator = Paginator(qs.order_by('-date_paiement', '-date_emission'), 10)
    page = request.GET.get('page', 1)
    cotisations = paginator.get_page(page)

    # Années disponibles pour le filtre
    annees = list(range(now.year, now.year - 5, -1))
    mois_choices = [
        (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
        (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
        (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre'),
    ]

    return render(request, 'cotisations/journal.html', {
        'cotisations': cotisations,
        'total_montant': total_montant,
        'nb_paiements': nb_paiements,
        'annee': annee,
        'mois': mois,
        'annees': annees,
        'mois_choices': mois_choices,
    })


@login_required
def valider_paiement(request, pk):
    """Marquer une cotisation comme payée."""
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_valider:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('cotisations:liste')

    obj = get_object_or_404(Cotisation, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        obj.statut = 'PAYE'
        obj.date_paiement = timezone.now().date()
        obj.save(update_fields=['statut', 'date_paiement'])
        enregistrer_audit(request, 'VALIDATION', 'cotisations', f"Validation paiement : {obj.reference}", 'Cotisation', pk)
        messages.success(request, f"✅ Cotisation {obj.reference} marquée comme payée.")
    return redirect('cotisations:liste')
