from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from core.views import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView
from .models import Groupe
from .forms import GroupeForm


class GroupeListView(CrudListView):
    model = Groupe
    context_object_name = 'groupes'
    module_name = 'groupe'
    search_fields = ['nom']
    list_template = 'groupe/liste.html'
    titre = 'Liste des groupes'


class GroupeCreateView(CrudCreateView):
    model = Groupe
    form_class = GroupeForm
    module_name = 'groupe'
    form_template = 'groupe/form.html'
    titre = 'Ajouter un groupe'
    success_message_create = "✅ Groupe {obj} créé avec succès."

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.mutualite = self.request.user.mutualite
        obj.cree_par = self.request.user
        obj.save()
        form.save_m2m()
        from core.mixins import enregistrer_audit
        enregistrer_audit(
            self.request, 'CREATION', 'groupe',
            f"Création groupe : {obj.nom}", 'Groupe', obj.pk,
        )
        from django.contrib import messages
        messages.success(self.request, self.success_message_create.format(obj=obj))
        return super(CrudCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('groupe:liste')


class GroupeUpdateView(CrudUpdateView):
    model = Groupe
    form_class = GroupeForm
    module_name = 'groupe'
    form_template = 'groupe/form.html'
    titre = 'Modifier le groupe'
    success_message_update = "✅ Groupe {obj} modifié avec succès."

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.save()
        form.save_m2m()
        from core.mixins import enregistrer_audit
        enregistrer_audit(
            self.request, 'MODIFICATION', 'groupe',
            f"Modification groupe : {obj.nom}", 'Groupe', obj.pk,
        )
        from django.contrib import messages
        messages.success(self.request, self.success_message_update.format(obj=obj))
        return super(CrudUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('groupe:liste')


class GroupeDeleteView(CrudDeleteView):
    model = Groupe
    module_name = 'groupe'
    confirm_delete_template = 'groupe/confirm_supprimer.html'
    success_message_delete = "🗑️ Groupe {obj} supprimé."
    soft_delete = False

    def get_success_url(self):
        return reverse_lazy('groupe:liste')
