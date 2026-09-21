import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import deletion

from core.models import Mutualite, JournalAudit, Utilisateur

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Supprime les mutualités en attente ou suspendues depuis plus de 7 jours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--jours',
            type=int,
            default=7,
            help='Nombre de jours avant expiration (défaut: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule sans supprimer'
        )

    def _force_delete(self, obj):
        from core.nettoyage import supprimer_mutualite_complete
        supprimer_mutualite_complete(obj)

    def handle(self, *args, **options):
        jours = options['jours']
        dry_run = options['dry_run']
        seuil = timezone.now() - timedelta(days=jours)
        try:
            from single_tenant.models import SingleTenantConfig
            actif_ids = list(SingleTenantConfig.objects.filter(statut='ACTIVE').values_list('mutualite_id', flat=True))
        except Exception:
            actif_ids = []

        from django.db.models import Q
        mutualites_expirees = Mutualite.objects.filter(
            Q(statut='EN_ATTENTE', date_creation__lt=seuil) |
            Q(statut='SUSPENDU', date_creation__lt=seuil)
        )
        if actif_ids:
            mutualites_expirees = mutualites_expirees.exclude(pk__in=actif_ids)

        count = mutualites_expirees.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(f'Aucune mutualité en attente depuis plus de {jours} jours.'))
            return

        self.stdout.write(f'Mutualités à supprimer ({count}) :')

        for m in mutualites_expirees:
            age = (timezone.now() - m.date_creation).days
            self.stdout.write(f'  - {m.code_mutualite} | {m.nom} | {age} jours | Admin: {m.username_admin}')

            if not dry_run:
                JournalAudit.objects.create(
                    mutualite=None,
                    utilisateur=None,
                    action='SUPPRESSION',
                    module='core',
                    description=f"Suppression automatique : mutualité '{m.nom}' ({m.code_mutualite}) en attente depuis {age} jours",
                    objet_type='Mutualite',
                    objet_id=m.pk,
                    adresse_ip='system',
                )

                # Supprimer l'admin user associé s'il existe
                if m.username_admin:
                    try:
                        admin_user = Utilisateur.objects.get(username=m.username_admin, mutualite=m)
                        admin_user.delete()
                    except Utilisateur.DoesNotExist:
                        pass

                # Forcer la suppression avec cascade complet
                try:
                    self._force_delete(m)
                except Exception as e:
                    logger.error(f'Erreur suppression mutualité {m.code_mutualite}: {e}')