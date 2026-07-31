import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Mutualite, JournalAudit, Utilisateur

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Supprime les mutualités en attente depuis plus de 7 jours (expirées)'

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

    def handle(self, *args, **options):
        jours = options['jours']
        dry_run = options['dry_run']
        seuil = timezone.now() - timedelta(days=jours)

        mutualites_expirees = Mutualite.objects.filter(
            statut='EN_ATTENTE',
            date_creation__lt=seuil
        )

        count = mutualites_expirees.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(f'Aucune mutualité en attente depuis plus de {jours} jours.'))
            return

        self.stdout.write(f'Mutualités à supprimer ({count}) :')

        for m in mutualites_expirees:
            age = (timezone.now() - m.date_creation).days
            self.stdout.write(f'  - {m.code_mutualite} | {m.nom} | {age} jours | Admin: {m.username_admin}')

            if not dry_run:
                # Log audit avant suppression
                JournalAudit.objects.create(
                    mutualite=None,
                    utilisateur=None,
                    action='SUPPRESSION_AUTO',
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

                # Supprimer la mutualité (cascade supprimera les données liées)
                m.delete()

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n[DRY RUN] {count} mutualité(s) seraient supprimées.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n{count} mutualité(s) expirée(s) supprimée(s).'))