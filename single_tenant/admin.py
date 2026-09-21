from django.contrib import admin
from .models import SingleTenantConfig


@admin.register(SingleTenantConfig)
class SingleTenantConfigAdmin(admin.ModelAdmin):
    list_display = ['nom_instance', 'mutualite', 'statut', 'date_activation', 'created_at']
    list_filter = ['statut']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('Mutualité', {'fields': ['mutualite', 'nom_instance']}),
        ('Statut', {'fields': ['statut', 'date_activation']}),
        ('Audit', {'fields': ['created_at', 'updated_at']}),
    ]

    def has_add_permission(self, request):
        return not SingleTenantConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return True
