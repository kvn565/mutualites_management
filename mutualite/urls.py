from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from core.views import landing_view, parametres_mutualite, activer_licence

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_view, name='landing'),
    path('connexion/', include('core.urls')),
    path('parametres-mutualite/', parametres_mutualite, name='parametres_mutualite'),
    path('licence/', activer_licence, name='activer_licence'),
    path('dashboard/', include('dashboard.urls')),
    path('affilies/', include('affilies.urls')),
    path('ayants-droit/', include('ayants_droit.urls')),
    path('services/', include('services_sante.urls')),
    path('partenaires/', include('partenaires.urls')),
    path('origines/', include('origines.urls')),
    path('factures/', include('factures.urls')),
    path('cotisations/', include('cotisations.urls')),
    path('pharmacie/', include('pharmacie.urls')),
    path('comptabilite/', include('comptabilite.urls')),
    path('utilisateurs/', include('utilisateurs.urls')),
    path('ventilations/', include('ventilations.urls')),
    path('corbeille/', include('corbeille.urls')),
    path('groupes/', include('groupe.urls')),
    path('aide/', include('aide.urls')),
    path('portail/', include('portail_partenaire.urls')),
    path('chambres/', include('gestion_chambres.urls')),
    path('superadmin/', include('superadmin.urls')),
    path('api/superadmin/', include('superadmin.api_urls')),
    path('single-tenant/', include('single_tenant.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Mutualité de Santé — Administration"
admin.site.site_title = "Mutualité Admin"
admin.site.index_title = "Gestion de la Mutualité"
admin.site.site_url = reverse_lazy('superadmin:dashboard')
