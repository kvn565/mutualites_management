# origines/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Origine
from .forms import OrigineForm
from core.mixins import enregistrer_audit
from django.views.decorators.http import require_POST

@login_required
def liste(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    qs = Origine.objects.filter(mutualite=request.user.mutualite)
    
    q = request.GET.get('q', '')
    type_orig = request.GET.get('type', '')
    
    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(contact__icontains=q))
    if type_orig:
        qs = qs.filter(type_origine=type_orig)
        
    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    origines = paginator.get_page(page)
    
    return render(request, 'origines/liste.html', {
        'origines': origines,
        'q': q,
        'type': type_orig,
        'total': qs.count(),
        'type_choices': Origine.TYPE_CHOICES,
    })

@login_required
def detail(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    origine = get_object_or_404(Origine, pk=pk, mutualite=request.user.mutualite)
    # Récupérer les affiliés de cette origine
    affilies = []
    try:
        affilies = origine.affilies.filter(supprime=False)[:50]
    except:
        pass

    # Exclusions
    exclusions = []
    medicaments = []
    services = []
    try:
        from .models import OrigineExclusion
        exclusions = OrigineExclusion.objects.filter(origine=origine).select_related('medicament', 'service')
        medicaments = origine.mutualite.medicament_set.all() if origine.mutualite else []
        services = origine.mutualite.servicesante_set.all() if origine.mutualite else []
    except:
        pass

    return render(request, 'origines/detail.html', {
        'origine': origine,
        'affilies': affilies,
        'exclusions': exclusions,
        'medicaments': medicaments,
        'services': services,
    })

@login_required
def ajouter(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('origines:liste')
        
    if request.method == 'POST':
        form = OrigineForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mutualite = request.user.mutualite
            obj.save()
            enregistrer_audit(request, 'CREATION', 'origines', f"Création origine : {obj.nom}", 'Origine', obj.pk)
            messages.success(request, f"✅ Origine {obj.nom} ajoutée avec succès.")
            return redirect('origines:liste')
    else:
        form = OrigineForm()
        
    return render(request, 'origines/form.html', {'form': form, 'titre': 'Ajouter une origine'})

@login_required
def modifier(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('origines:liste')
        
    obj = get_object_or_404(Origine, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = OrigineForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            enregistrer_audit(request, 'MODIFICATION', 'origines', f"Modification origine : {obj.nom}", 'Origine', obj.pk)
            messages.success(request, f"✅ Origine {obj.nom} modifiée.")
            return redirect('origines:liste')
    else:
        form = OrigineForm(instance=obj)
        
    return render(request, 'origines/form.html', {'form': form, 'obj': obj, 'titre': 'Modifier origine'})

from django.http import JsonResponse

@login_required
def ajax_creer(request):
    if request.user.est_super_admin or not request.user.peut_modifier:
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'})
    nom = request.POST.get('nom', '').strip()
    if not nom:
        return JsonResponse({'ok': False, 'error': 'Le nom est requis.'})
    obj = Origine.objects.create(
        mutualite=request.user.mutualite,
        nom=nom,
        type_origine='AUTRE',
    )
    return JsonResponse({'ok': True, 'id': obj.pk, 'text': str(obj)})


@login_required
def supprimer(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_supprimer:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('origines:liste')
        
    obj = get_object_or_404(Origine, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        nom = obj.nom
        if obj.nb_affilies > 0:
            messages.error(request, f"❌ Impossible de supprimer {nom} car elle contient des affiliés.")
            return redirect('origines:liste')
            
        obj.delete()
        enregistrer_audit(request, 'SUPPRESSION', 'origines', f"Suppression origine : {nom}", 'Origine', pk)
        messages.success(request, f"🗑️ Origine {nom} supprimée.")
        return redirect('origines:liste')
        
    return render(request, 'origines/confirm_supprimer.html', {'obj': obj})


# ── Exclusions d'origine ──────────────────────────────────

@login_required
@require_POST
def exclusion_ajouter(request, origine_pk):
    from .models import Origine
    from .models import OrigineExclusion
    origine = get_object_or_404(Origine, pk=origine_pk, mutualite=request.user.mutualite)
    type_excl = request.POST.get('type')
    item_pk = request.POST.get('item_pk')
    motif = request.POST.get('motif', '')

    if not type_excl or not item_pk:
        messages.error(request, "Veuillez sélectionner un type et un élément.")
        return redirect('origines:detail', pk=origine_pk)

    if type_excl == 'medicament':
        from pharmacie.models import Medicament
        item = get_object_or_404(Medicament, pk=item_pk, mutualite=request.user.mutualite)
        if OrigineExclusion.objects.filter(origine=origine, medicament=item).exists():
            messages.warning(request, "Ce médicament est déjà exclu pour cette origine.")
            return redirect('origines:detail', pk=origine_pk)
        OrigineExclusion.objects.create(
            mutualite=request.user.mutualite,
            origine=origine, medicament=item,
            motif=motif, cree_par=request.user,
        )
        messages.success(request, f"Médicament « {item.nom} » exclu pour l'origine {origine.nom}.")
    elif type_excl == 'service':
        from services_sante.models import ServiceSante
        item = get_object_or_404(ServiceSante, pk=item_pk, mutualite=request.user.mutualite)
        if OrigineExclusion.objects.filter(origine=origine, service=item).exists():
            messages.warning(request, "Ce service est déjà exclu pour cette origine.")
            return redirect('origines:detail', pk=origine_pk)
        OrigineExclusion.objects.create(
            mutualite=request.user.mutualite,
            origine=origine, service=item,
            motif=motif, cree_par=request.user,
        )
        messages.success(request, f"Service « {item.nom} » exclu pour l'origine {origine.nom}.")

    return redirect('origines:detail', pk=origine_pk)


@login_required
@require_POST
def exclusion_supprimer(request, pk):
    from .models import OrigineExclusion
    exclusion = get_object_or_404(OrigineExclusion, pk=pk, mutualite=request.user.mutualite)
    origine_pk = exclusion.origine.pk
    label = str(exclusion)
    exclusion.delete()
    messages.success(request, f"Exclusion supprimée : {label}")
    return redirect('origines:detail', pk=origine_pk)
