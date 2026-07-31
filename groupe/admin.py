from django.contrib import admin
from .models import Groupe, Menu


@admin.register(Groupe)
class GroupeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'mutualite', 'nombre_membres', 'date_creation']
    list_filter = ['mutualite']
    search_fields = ['nom', 'description']
    filter_horizontal = ['membres', 'menus']

    def nombre_membres(self, obj):
        return obj.membres.count()
    nombre_membres.short_description = 'Membres'


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['nom', 'url_name', 'categorie', 'ordre', 'actif']
    list_filter = ['categorie', 'actif']
    search_fields = ['nom', 'url_name']
    list_editable = ['ordre', 'actif']
