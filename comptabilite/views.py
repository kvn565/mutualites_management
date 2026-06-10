# comptabilite/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from .models import Compte, Transaction, Ecriture
from .forms import TransactionForm, EcritureFormSet
from core.mixins import enregistrer_audit

@login_required
def dashboard(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    comptes_actifs = Compte.objects.filter(mutualite=request.user.mutualite, type_compte='ACTIF', actif=True)
    comptes_passifs = Compte.objects.filter(mutualite=request.user.mutualite, type_compte='PASSIF', actif=True)
    comptes_produits = Compte.objects.filter(mutualite=request.user.mutualite, type_compte='PRODUIT', actif=True)
    comptes_charges = Compte.objects.filter(mutualite=request.user.mutualite, type_compte='CHARGE', actif=True)
    
    total_actif = sum([c.solde_actuel for c in comptes_actifs])
    total_passif = sum([c.solde_actuel for c in comptes_passifs])
    total_produit = sum([c.solde_actuel for c in comptes_produits])
    total_charge = sum([c.solde_actuel for c in comptes_charges])
    
    resultat = total_produit - total_charge
    
    return render(request, 'comptabilite/dashboard.html', {
        'total_actif': total_actif,
        'total_passif': total_passif,
        'total_produit': total_produit,
        'total_charge': total_charge,
        'resultat': resultat,
    })

@login_required
def liste_comptes(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    comptes = Compte.objects.filter(mutualite=request.user.mutualite)
    return render(request, 'comptabilite/liste_comptes.html', {'comptes': comptes})

@login_required
def journal(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    transactions = Transaction.objects.filter(mutualite=request.user.mutualite).prefetch_related('ecritures', 'ecritures__compte')
    return render(request, 'comptabilite/journal.html', {'transactions': transactions})

@login_required
def ajouter_transaction(request):
    if request.user.est_super_admin:
        messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
        return redirect('superadmin:dashboard')
    if not request.user.peut_modifier:
        messages.error(request, "⛔ Permission refusée.")
        return redirect('comptabilite:journal')
        
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        formset = EcritureFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            # Check balance
            total_debit = 0
            total_credit = 0
            for inline_form in formset:
                if inline_form.cleaned_data and not inline_form.cleaned_data.get('DELETE'):
                    mnt = inline_form.cleaned_data.get('montant') or 0
                    mvt = inline_form.cleaned_data.get('type_mouvement')
                    if mvt == 'DEBIT': total_debit += mnt
                    elif mvt == 'CREDIT': total_credit += mnt
            
            if total_debit != total_credit:
                messages.error(request, f"❌ La transaction n'est pas équilibrée (Débit: {total_debit} ≠ Crédit: {total_credit}).")
            else:
                transaction = form.save(commit=False)
                transaction.enregistre_par = request.user
                transaction.save()
                
                formset.instance = transaction
                formset.save()
                
                enregistrer_audit(request, 'CREATION', 'comptabilite', f"Transaction : {transaction.reference}", 'Transaction', transaction.pk)
                messages.success(request, f"✅ Transaction {transaction.reference} enregistrée.")
                return redirect('comptabilite:journal')
    else:
        form = TransactionForm()
        formset = EcritureFormSet()
        
    return render(request, 'comptabilite/transaction_form.html', {'form': form, 'formset': formset})
