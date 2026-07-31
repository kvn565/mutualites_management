from django.core.management.base import BaseCommand, CommandError
from core.models import Mutualite
from comptabilite.models import Compte


class Command(BaseCommand):
    help = "Initialise le plan comptable SYSCOHADA pour une ou toutes les mutualités"

    def add_arguments(self, parser):
        parser.add_argument('--mutualite', type=int, help='PK de la mutualité (toutes si omis)')

    def handle(self, *args, **options):
        mutualites = Mutualite.objects.all()
        if options['mutualite']:
            mutualites = mutualites.filter(pk=options['mutualite'])

        if not mutualites.exists():
            raise CommandError("Aucune mutualité trouvée.")

        plan_base = [
            ('101', 'Capital social', 'PASSIF', '1'),
            ('106', 'Réserves / Report à nouveau', 'PASSIF', '1'),
            ('12',  "Résultat de l'exercice", 'PASSIF', '1'),
            ('13',  'Subventions', 'PASSIF', '1'),
            ('15',  'Provisions réglementées', 'PASSIF', '1'),
            ('161', 'Emprunts bancaires', 'PASSIF', '1'),
            ('162', 'Dettes financières', 'PASSIF', '1'),
            ('401', 'Fournisseurs', 'PASSIF', '4'),
            ('404', 'Personnel — rémunérations dues', 'PASSIF', '4'),
            ('411', 'Clients', 'ACTIF', '4'),
            ('421', 'Adhérents — cotisations à recevoir', 'ACTIF', '4'),
            ('431', 'Organismes sociaux', 'PASSIF', '4'),
            ('441', 'État — impôts', 'PASSIF', '4'),
            ('471', "Comptes d'attente / de régularisation", 'ACTIF', '4'),
            ('481', 'Charges constatées d\'avance', 'ACTIF', '4'),
            ('50',  'Banques', 'ACTIF', '5'),
            ('521', 'Caisse espèces', 'ACTIF', '5'),
            ('522', 'Mobile Money', 'ACTIF', '5'),
            ('523', 'Compte chèque', 'ACTIF', '5'),
            ('531', 'Titres de placement', 'ACTIF', '5'),
            ('571', 'Caisse générale', 'ACTIF', '5'),
            ('601', 'Prestations médicales', 'CHARGE', '6'),
            ('602', 'Frais pharmaceutiques', 'CHARGE', '6'),
            ('603', 'Frais d\'hospitalisation', 'CHARGE', '6'),
            ('611', 'Frais de personnel', 'CHARGE', '6'),
            ('612', 'Frais de gestion', 'CHARGE', '6'),
            ('613', 'Frais administratifs', 'CHARGE', '6'),
            ('614', 'Frais de déplacement', 'CHARGE', '6'),
            ('615', 'Honoraires', 'CHARGE', '6'),
            ('62',  'Charges financières', 'CHARGE', '6'),
            ('631', 'Dotations aux amortissements', 'CHARGE', '6'),
            ('641', 'Dotations aux provisions', 'CHARGE', '6'),
            ('701', 'Cotisations des adhérents', 'PRODUIT', '7'),
            ('702', 'Revenus de placement', 'PRODUIT', '7'),
            ('703', "Subventions d'exploitation", 'PRODUIT', '7'),
            ('704', 'Dons et legs', 'PRODUIT', '7'),
            ('72',  'Produits financiers', 'PRODUIT', '7'),
            ('75',  'Produits exceptionnels', 'PRODUIT', '7'),
            ('81',  'Engagements reçus', 'PRODUIT', '8'),
            ('82',  'Engagements donnés', 'PASSIF', '8'),
        ]

        total = 0
        for m in mutualites:
            for code, libelle, typ, classe in plan_base:
                obj, created = Compte.objects.get_or_create(
                    mutualite=m, numero=code,
                    defaults={
                        'intitule': libelle,
                        'type_compte': typ,
                        'categorie_syscohada': classe,
                        'actif': True,
                    },
                )
                if created:
                    total += 1

        self.stdout.write(self.style.SUCCESS(f"{total} comptes créés pour {mutualites.count()} mutualité(s)."))
