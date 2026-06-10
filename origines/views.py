# origines/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Origine
from .forms import OrigineForm
from core.mixins import enregistrer_audit

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
        
    return render(request, 'origines/detail.html', {
        'origine': origine,
        'affilies': affilies,
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
            obj = form.save()
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
