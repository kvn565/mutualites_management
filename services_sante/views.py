# services_sante/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import ServiceSante
from .forms import ServiceSanteForm
from core.mixins import enregistrer_audit

@login_required
def liste(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    qs = ServiceSante.objects.filter(mutualite=request.user.mutualite)
    
    q = request.GET.get('q', '')
    categorie = request.GET.get('categorie', '')
    
    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(code__icontains=q))
    if categorie:
        qs = qs.filter(categorie=categorie)
        
    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    services = paginator.get_page(page)
    
    return render(request, 'services_sante/liste.html', {
        'services': services,
        'q': q,
        'categorie': categorie,
        'total': qs.count(),
        'categorie_choices': ServiceSante.CATEGORIE_CHOICES,
    })

@login_required
def detail(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    service = get_object_or_404(ServiceSante, pk=pk, mutualite=request.user.mutualite)
    return render(request, 'services_sante/detail.html', {
        'service': service,
    })

@login_required
def ajouter(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('services_sante:liste')
        
    if request.method == 'POST':
        form = ServiceSanteForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            if not obj.code:
                # Generate a code if none is provided
                obj.code = ServiceSante.generer_code(obj.categorie)
            obj.save()
            enregistrer_audit(request, 'CREATION', 'services_sante', f"Création service : {obj.nom}", 'ServiceSante', obj.pk)
            messages.success(request, f"✅ Service {obj.nom} ajouté avec succès.")
            return redirect('services_sante:liste')
    else:
        form = ServiceSanteForm()
        
    return render(request, 'services_sante/form.html', {'form': form, 'titre': 'Ajouter un service de santé'})

@login_required
def modifier(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('services_sante:liste')
        
    obj = get_object_or_404(ServiceSante, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = ServiceSanteForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            enregistrer_audit(request, 'MODIFICATION', 'services_sante', f"Modification service : {obj.nom}", 'ServiceSante', obj.pk)
            messages.success(request, f"✅ Service {obj.nom} modifié.")
            return redirect('services_sante:liste')
    else:
        form = ServiceSanteForm(instance=obj)
        
    return render(request, 'services_sante/form.html', {'form': form, 'obj': obj, 'titre': 'Modifier le service'})

@login_required
def supprimer(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_supprimer:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('services_sante:liste')
        
    obj = get_object_or_404(ServiceSante, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        nom = obj.nom
        # In a real scenario, you'd check if it's used in bills
        obj.delete()
        enregistrer_audit(request, 'SUPPRESSION', 'services_sante', f"Suppression service : {nom}", 'ServiceSante', pk)
        messages.success(request, f"🗑️ Service {nom} supprimé.")
        return redirect('services_sante:liste')
        
    return render(request, 'services_sante/confirm_supprimer.html', {'obj': obj})
