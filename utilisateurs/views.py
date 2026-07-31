# utilisateurs/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from core.models import Utilisateur
from groupe.models import Groupe
from core.mixins import enregistrer_audit, AdminRequiredMixin
from .forms import UtilisateurForm, UtilisateurEditForm

@login_required
def liste(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.est_admin:
        messages.error(request, "⛔ Accès réservé aux administrateurs.")
        return redirect('dashboard:index')

    qs = Utilisateur.objects.filter(mutualite=request.user.mutualite)
    q = request.GET.get('q', '')
    role = request.GET.get('role', '')

    if q:
        qs = qs.filter(
            Q(username__icontains=q) | 
            Q(nom__icontains=q) | 
            Q(prenom__icontains=q)
        )
    if role:
        qs = qs.filter(role=role)

    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    utilisateurs = paginator.get_page(page)

    return render(request, 'utilisateurs/liste.html', {
        'utilisateurs': utilisateurs,
        'q': q,
        'role': role,
        'total': qs.count(),
        'role_choices': Utilisateur.ROLE_CHOICES,
    })

@login_required
def ajouter(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.est_admin:
        messages.error(request, "⛔ Accès réservé aux administrateurs.")
        return redirect('dashboard:index')

    groupes = Groupe.objects.filter(mutualite=request.user.mutualite)

    if request.method == 'POST':
        form = UtilisateurForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mutualite = request.user.mutualite
            obj.save()
            groupe_ids = request.POST.getlist('groupes')
            if groupe_ids:
                obj.groupes.set(Groupe.objects.filter(pk__in=groupe_ids, mutualite=request.user.mutualite))
            enregistrer_audit(request, 'CREATION', 'utilisateurs', f"Création utilisateur : {obj.username}", 'Utilisateur', obj.pk)
            messages.success(request, f"✅ Utilisateur {obj.username} ajouté avec succès.")
            return redirect('utilisateurs:liste')
    else:
        form = UtilisateurForm()

    return render(request, 'utilisateurs/form.html', {'form': form, 'titre': 'Ajouter un utilisateur', 'groupes': groupes})

@login_required
def modifier(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.est_admin:
        messages.error(request, "⛔ Accès réservé aux administrateurs.")
        return redirect('dashboard:index')

    obj = get_object_or_404(Utilisateur, pk=pk, mutualite=request.user.mutualite)
    groupes = Groupe.objects.filter(mutualite=request.user.mutualite)

    if request.method == 'POST':
        form = UtilisateurEditForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            groupe_ids = request.POST.getlist('groupes')
            obj.groupes.set(Groupe.objects.filter(pk__in=groupe_ids, mutualite=request.user.mutualite))
            enregistrer_audit(request, 'MODIFICATION', 'utilisateurs', f"Modification utilisateur : {obj.username}", 'Utilisateur', obj.pk)
            messages.success(request, f"✅ Utilisateur {obj.username} modifié avec succès.")
            return redirect('utilisateurs:liste')
    else:
        form = UtilisateurEditForm(instance=obj)

    return render(request, 'utilisateurs/form.html', {'form': form, 'obj': obj, 'titre': 'Modifier un utilisateur', 'groupes': groupes})

@login_required
def supprimer(request, pk):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.est_admin:
        messages.error(request, "⛔ Accès réservé aux administrateurs.")
        return redirect('dashboard:index')

    obj = get_object_or_404(Utilisateur, pk=pk, mutualite=request.user.mutualite)
    
    if obj == request.user:
        messages.error(request, "❌ Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('utilisateurs:liste')

    if request.method == 'POST':
        username = obj.username
        obj.delete()
        enregistrer_audit(request, 'SUPPRESSION', 'utilisateurs', f"Suppression utilisateur : {username}", 'Utilisateur', pk)
        messages.success(request, f"🗑️ Utilisateur {username} supprimé.")
        return redirect('utilisateurs:liste')

    return render(request, 'utilisateurs/confirm_supprimer.html', {'obj': obj})


