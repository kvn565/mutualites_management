from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Mutualite


class Command(BaseCommand):
    help = "Détecte les mutualités dont la licence a expiré et met à jour leur statut."

    def handle(self, *args, **options):
        now = timezone.now()
        expirees = Mutualite.objects.filter(
            statut__in=['ESSAI', 'ACTIF'],
            date_expiration__lt=now,
        )
        count = expirees.count()
        for mutualite in expirees:
            mutualite.statut = 'EXPIRE'
            mutualite.save(update_fields=['statut'])

        essai_expire = Mutualite.objects.filter(
            statut='ESSAI',
            date_fin_essai__lt=now,
        ).exclude(pk__in=expirees.values_list('pk', flat=True))
        for mutualite in essai_expire:
            mutualite.statut = 'EXPIRE'
            mutualite.save(update_fields=['statut'])

        total = count + essai_expire.count()
        self.stdout.write(self.style.SUCCESS(f"{total} licence(s) expirée(s) détectée(s) et mise(s) à jour."))
