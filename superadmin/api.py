from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import models
from datetime import timedelta

from core.models import Mutualite
from .serializers import (
    MutualiteListSerializer,
    MutualiteDetailSerializer,
    MutualiteCreateSerializer,
    DashboardSerializer,
)
from .permissions import IsSuperAdmin


class MutualiteViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    """
    API de gestion des mutualités clientes de la plateforme.

    ## Endpoints

    ### CRUD
    - `GET /api/superadmin/mutualites/` — Liste toutes les mutualités
    - `POST /api/superadmin/mutualites/` — Enregistrer une nouvelle mutualité
    - `GET /api/superadmin/mutualites/{id}/` — Détail d'une mutualité
    - `PUT /api/superadmin/mutualites/{id}/` — Modifier une mutualité

    ### Actions
    - `POST /api/superadmin/mutualites/{id}/suspendre/` — Suspendre une mutualité
    - `POST /api/superadmin/mutualites/{id}/reactiver/` — Réactiver une mutualité
    - `POST /api/superadmin/mutualites/{id}/renouveler-licence/` — Renouveler la licence
    - `POST /api/superadmin/mutualites/{id}/prolonger-essai/` — Prolonger l'essai gratuit

    ### Filtres
    - `GET /api/superadmin/mutualites/?search=...` — Recherche par nom, NIF, téléphone
    - `GET /api/superadmin/mutualites/?statut=ESSAI` — Filtrer par statut
    """
    queryset = Mutualite.objects.all()
    permission_classes = [IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['statut', 'type_mutualite', 'essai_gratuit']
    search_fields = ['nom', 'nif', 'telephone', 'nom_responsable', 'code_mutualite', 'email']
    ordering_fields = ['date_creation', 'nom', 'statut']
    ordering = ['-date_creation']

    def get_serializer_class(self):
        if self.action == 'create':
            return MutualiteCreateSerializer
        if self.action in ('retrieve', 'update', 'partial_update'):
            return MutualiteDetailSerializer
        return MutualiteListSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def suspendre(self, request, pk=None):
        """Suspendre une mutualité."""
        mutualite = self.get_object()
        if mutualite.statut not in ('ACTIF', 'ESSAI'):
            return Response(
                {"detail": f"Impossible de suspendre une mutualité avec le statut '{mutualite.get_statut_display()}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mutualite.statut = 'SUSPENDU'
        mutualite.save()
        serializer = MutualiteDetailSerializer(mutualite)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reactiver(self, request, pk=None):
        """Réactiver une mutualité suspendue."""
        mutualite = self.get_object()
        if mutualite.statut != 'SUSPENDU':
            return Response(
                {"detail": "Seules les mutualités suspendues peuvent être réactivées."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if mutualite.essai_gratuit:
            mutualite.activer_essai()
        else:
            mutualite.statut = 'ACTIF'
            mutualite.save()
        serializer = MutualiteDetailSerializer(mutualite)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='renouveler-licence')
    def renouveler_licence(self, request, pk=None):
        """Renouveler la licence d'une mutualité."""
        mutualite = self.get_object()
        type_abonnement = request.data.get('type_abonnement', 'MENSUEL')
        duree_jours = int(request.data.get('duree_jours', 30))

        mutualite.activer_licence(type_abonnement, duree_jours)
        serializer = MutualiteDetailSerializer(mutualite)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def prolonger_essai(self, request, pk=None):
        """Prolonger la période d'essai gratuit."""
        mutualite = self.get_object()
        jours = int(request.data.get('jours', 7))

        if mutualite.date_fin_essai:
            mutualite.date_fin_essai += timedelta(days=jours)
        else:
            mutualite.date_fin_essai = timezone.now() + timedelta(days=jours)
        mutualite.date_expiration = mutualite.date_fin_essai
        mutualite.statut = 'ESSAI'
        mutualite.save()

        serializer = MutualiteDetailSerializer(mutualite)
        return Response(serializer.data)


class DashboardAPIView(APIView):
    """Tableau de bord super admin avec les statistiques des mutualités."""
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        stats = {
            'total_mutualites': Mutualite.objects.count(),
            'mutualites_essai': Mutualite.objects.filter(statut='ESSAI').count(),
            'mutualites_actives': Mutualite.objects.filter(statut='ACTIF').count(),
            'mutualites_suspendues': Mutualite.objects.filter(statut='SUSPENDU').count(),
            'mutualites_expirees': Mutualite.objects.filter(statut='EXPIRE').count(),
            'mutualites_bloquees': Mutualite.objects.filter(statut='BLOQUE').count(),
            'total_utilisateurs': Mutualite.objects.aggregate(
                total=models.Count('utilisateurs')
            )['total'] or 0,
        }
        serializer = DashboardSerializer(stats)
        return Response(serializer.data)
