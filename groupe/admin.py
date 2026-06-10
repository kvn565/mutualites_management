from django.contrib import admin
from .models import Groupe


@admin.register(Groupe)
class GroupeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'mutualite', 'nombre_membres', 'date_creation']
    list_filter = ['mutualite']
    search_fields = ['nom', 'description']
    filter_horizontal = ['membres']

    def nombre_membres(self, obj):
        return obj.membres.count()
    nombre_membres.short_description = 'Membres'
