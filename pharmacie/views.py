# pharmacie/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from django.http import JsonResponse
from .models import Medicament, CategorieMedicament
from .forms import MedicamentForm
from core.mixins import enregistrer_audit

@login_required
def liste(request):
    if not request.user.mutualite and request.user.est_super_admin:
        messages.warning(request, "⛔ Aucune mutualité associée.")
        return redirect('superadmin:dashboard')
    qs = Medicament.objects.filter(mutualite=request.user.mutualite)
    
    q = request.GET.get('q', '')
    forme = request.GET.get('forme', '')
    
    if q:
        qs = qs.filter(
            Q(nom__icontains=q) | 
            Q(code__icontains=q) |
            Q(dci__icontains=q)
        )
    if forme:
        qs = qs.filter(forme=forme)
        
    paginator = Paginator(qs, 5)
    page = request.GET.get('page', 1)
    medicaments = paginator.get_page(page)
    
    return render(request, 'pharmacie/liste.html', {
        'medicaments': medicaments,
        'q': q,
        'forme': forme,
        'total': qs.count(),
        'forme_choices': Medicament.FORME_CHOICES,
    })

@login_required
def ajouter(request):
    if not request.user.mutualite and request.user.est_super_admin:
        messages.warning(request, "⛔ Aucune mutualité associée.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('pharmacie:liste')
        
    if request.method == 'POST':
        form = MedicamentForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mutualite = request.user.mutualite
            obj.save()
            enregistrer_audit(request, 'CREATION', 'pharmacie', f"Création médicament : {obj.nom}", 'Medicament', obj.pk)
            messages.success(request, f"✅ Médicament {obj.nom} ajouté.")
            return redirect('pharmacie:liste')
    else:
        form = MedicamentForm(initial={'code': Medicament.generer_code()})
        
    return render(request, 'pharmacie/form.html', {'form': form, 'titre': 'Ajouter un médicament'})

@login_required
def modifier(request, pk):
    if not request.user.mutualite and request.user.est_super_admin:
        messages.warning(request, "⛔ Aucune mutualité associée.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('pharmacie:liste')
        
    obj = get_object_or_404(Medicament, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        form = MedicamentForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            enregistrer_audit(request, 'MODIFICATION', 'pharmacie', f"Modification médicament : {obj.nom}", 'Medicament', obj.pk)
            messages.success(request, f"✅ Médicament {obj.nom} modifié.")
            return redirect('pharmacie:liste')
    else:
        form = MedicamentForm(instance=obj)
        
    return render(request, 'pharmacie/form.html', {'form': form, 'obj': obj, 'titre': 'Modifier le médicament'})

@login_required
def ajax_creer_categorie(request):
    if (not request.user.mutualite and request.user.est_super_admin) or not request.user.peut_modifier:
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'})
    nom = request.POST.get('nom', '').strip()
    if not nom:
        return JsonResponse({'ok': False, 'error': 'Le nom est requis.'})
    obj = CategorieMedicament.objects.create(
        mutualite=request.user.mutualite,
        nom=nom,
    )
    return JsonResponse({'ok': True, 'id': obj.pk, 'text': str(obj)})


@login_required
def supprimer(request, pk):
    if not request.user.mutualite and request.user.est_super_admin:
        messages.warning(request, "⛔ Aucune mutualité associée.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_supprimer:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('pharmacie:liste')
        
    obj = get_object_or_404(Medicament, pk=pk, mutualite=request.user.mutualite)
    if request.method == 'POST':
        nom = obj.nom
        obj.delete(user=request.user)
        enregistrer_audit(request, 'SUPPRESSION', 'pharmacie', f"Suppression médicament : {nom}", 'Medicament', pk)
        messages.success(request, f"🗑️ Médicament {nom} supprimé.")
        return redirect('pharmacie:liste')
        
    return render(request, 'pharmacie/confirm_supprimer.html', {'obj': obj})
