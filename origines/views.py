# origines/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Origine, CategorieOrigine
from .forms import OrigineForm, CategorieOrigineForm
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

    # Catégories
    categories = origine.categories.all().order_by('ordre', 'nom')

    return render(request, 'origines/detail.html', {
        'origine': origine,
        'affilies': affilies,
        'categories': categories,
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
def ajax_creer_categorie(request):
    if request.user.est_super_admin or not request.user.peut_modifier:
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'})
    nom = request.POST.get('nom', '').strip()
    origine_id = request.POST.get('origine_id')
    if not nom:
        return JsonResponse({'ok': False, 'error': 'Le nom de la catégorie est requis.'})
    if not origine_id:
        return JsonResponse({'ok': False, 'error': "L'origine est requise."})
    
    origine = get_object_or_404(Origine, pk=origine_id, mutualite=request.user.mutualite)
    obj, created = CategorieOrigine.objects.get_or_create(
        origine=origine,
        nom=nom,
        defaults={
            'mutualite': request.user.mutualite,
            'cotisation_mensuelle': origine.cotisation_mensuelle,
            'soins_ambulatoires': origine.soins_ambulatoires,
            'limite_laboratoire': origine.limite_laboratoire,
            'limite_kinesitherapie': origine.limite_kinesitherapie,
            'limite_reanimation': origine.limite_reanimation,
            'limite_imagerie_medicale': origine.limite_imagerie_medicale,
            'hopital_plafond_chambre': origine.hopital_plafond_chambre,
            'hpc_nuit': origine.hpc_nuit,
            'limite_hospitalisation_generale': origine.limite_hospitalisation_generale,
            'maternite_forfait': origine.maternite_forfait,
            'pourcentage_maternite': origine.pourcentage_maternite,
            'pharmacie_forfait': origine.pharmacie_forfait,
            'limites_medicaments': origine.limites_medicaments,
            'limites_lunettes': origine.limites_lunettes,
            'limites_dents': origine.limites_dents,
        }
    )
    return JsonResponse({'ok': True, 'id': obj.pk, 'text': f"{origine.nom} — {obj.nom}"})


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


# ── Catégories d'origine ──────────────────────────────────

@login_required
def categories_liste(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    
    qs = CategorieOrigine.objects.filter(origine__mutualite=request.user.mutualite).select_related('origine')
    
    q = request.GET.get('q', '')
    origine_id = request.GET.get('origine', '')
    
    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(origine__nom__icontains=q))
    if origine_id:
        qs = qs.filter(origine_id=origine_id)
        
    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    categories = paginator.get_page(page)
    
    origines = Origine.objects.filter(mutualite=request.user.mutualite, actif=True)
    
    return render(request, 'origines/categories_liste.html', {
        'categories': categories,
        'q': q,
        'origine_id': origine_id,
        'total': qs.count(),
        'origines': origines,
    })


@login_required
def categorie_ajouter(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('origines:categories')
        
    if request.method == 'POST':
        form = CategorieOrigineForm(request.POST, mutualite=request.user.mutualite)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mutualite = request.user.mutualite
            obj.save()
            enregistrer_audit(request, 'CREATION', 'origines', f"Création catégorie : {obj.nom}", 'CategorieOrigine', obj.pk)
            messages.success(request, f"✅ Catégorie {obj.nom} ajoutée avec succès.")
            return redirect('origines:categories')
    else:
        initial = {}
        origine_id = request.GET.get('origine')
        if origine_id:
            initial['origine'] = origine_id
        form = CategorieOrigineForm(initial=initial, mutualite=request.user.mutualite)
        
    return render(request, 'origines/categorie_form.html', {'form': form, 'titre': 'Ajouter une catégorie'})


@login_required
def categorie_modifier(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('origines:categories')
        
    obj = get_object_or_404(CategorieOrigine, pk=pk, origine__mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = CategorieOrigineForm(request.POST, instance=obj, mutualite=request.user.mutualite)
        if form.is_valid():
            form.save()
            enregistrer_audit(request, 'MODIFICATION', 'origines', f"Modification catégorie : {obj.nom}", 'CategorieOrigine', obj.pk)
            messages.success(request, f"✅ Catégorie {obj.nom} modifiée.")
            return redirect('origines:categories')
    else:
        form = CategorieOrigineForm(instance=obj, mutualite=request.user.mutualite)
        
    return render(request, 'origines/categorie_form.html', {'form': form, 'obj': obj, 'titre': 'Modifier catégorie'})


@login_required
def categorie_supprimer(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_supprimer:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('origines:categories')
        
    obj = get_object_or_404(CategorieOrigine, pk=pk, origine__mutualite=request.user.mutualite)
    if request.method == 'POST':
        nom = obj.nom
        if obj.affilies.filter(supprime=False).exists():
            messages.error(request, f"❌ Impossible de supprimer {nom} car elle contient des affiliés.")
            return redirect('origines:categories')
            
        obj.delete()
        enregistrer_audit(request, 'SUPPRESSION', 'origines', f"Suppression catégorie : {nom}", 'CategorieOrigine', pk)
        messages.success(request, f"🗑️ Catégorie {nom} supprimée.")
        return redirect('origines:categories')
        
    return render(request, 'origines/categorie_confirm_supprimer.html', {'obj': obj})
