from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date


from core.models import Mutualite
from .models import Partenaire, Convention, UtilisateurPartenaire

User = get_user_model()


class PartenaireModelTest(TestCase):
    def setUp(self):
        self.mutualite = Mutualite.objects.create(
            nif='4000000501',
            nom='Mutualité Test',
            nom_responsable='Test',
            telephone='79123456',
            email='test@mutualite.com',
            province='Bujumbura',
            commune='Mairie',
        )
        self.user = User.objects.create_user(
            username='agent',
            password='test123',
            mutualite=self.mutualite,
            role='AGENT',
        )

    def test_code_partenaire_genere_automatiquement(self):
        p = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='HOPITAL',
            nom_etablissement='Hôpital Central',
            created_by=self.user,
        )
        self.assertTrue(p.code_partenaire.startswith('HOP-'))
        self.assertEqual(p.code_partenaire, 'HOP-0001')

    def test_code_incremente_par_type(self):
        Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='HOPITAL',
            nom_etablissement='Hôpital A',
            created_by=self.user,
        )
        p2 = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='HOPITAL',
            nom_etablissement='Hôpital B',
            created_by=self.user,
        )
        self.assertEqual(p2.code_partenaire, 'HOP-0002')

    def test_code_independant_par_type(self):
        hop = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='HOPITAL',
            nom_etablissement='Hôpital A',
            created_by=self.user,
        )
        pha = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='PHARMACIE',
            nom_etablissement='Pharmacie B',
            created_by=self.user,
        )
        self.assertEqual(hop.code_partenaire, 'HOP-0001')
        self.assertEqual(pha.code_partenaire, 'PHA-0001')

    def test_code_prefixes_tous_les_types(self):
        types = [
            ('HOPITAL', 'HOP'), ('CENTRE_SANTE', 'CDS'), ('CLINIQUE', 'CLI'),
            ('PHARMACIE', 'PHA'), ('LABORATOIRE', 'LAB'), ('AMBULANCE', 'AMB'),
            ('CABINET_MEDICAL', 'CAB'), ('DENTISTE', 'DEN'), ('OPTICIEN', 'OPT'),
            ('KINESITHERAPEUTE', 'KIN'), ('AUTRE', 'AUT'),
        ]
        for type_partenaire, expected_prefix in types:
            p = Partenaire.objects.create(
                mutualite=self.mutualite,
                type_partenaire=type_partenaire,
                nom_etablissement=f'Test {type_partenaire}',
                created_by=self.user,
            )
            self.assertTrue(
                p.code_partenaire.startswith(f'{expected_prefix}-'),
                f'{type_partenaire} should produce prefix {expected_prefix}, got {p.code_partenaire}',
            )

    def test_generer_code_class_method(self):
        code = Partenaire.generer_code('HOPITAL')
        self.assertEqual(code, 'HOP-0001')
        Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='HOPITAL',
            nom_etablissement='Hôpital',
            created_by=self.user,
        )
        code = Partenaire.generer_code('HOPITAL')
        self.assertEqual(code, 'HOP-0002')

    def test_str_representation(self):
        p = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='PHARMACIE',
            nom_etablissement='Pharmacie du Centre',
            created_by=self.user,
        )
        self.assertIn(p.code_partenaire, str(p))
        self.assertIn('Pharmacie du Centre', str(p))
        self.assertEqual(str(p), f"{p.code_partenaire} — Pharmacie du Centre")

    def test_default_statut(self):
        p = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='CLINIQUE',
            nom_etablissement='Clinique Test',
            created_by=self.user,
        )
        self.assertEqual(p.statut, 'EN_ATTENTE')

    def test_convention_active_sans_date_fin(self):
        p = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='LABORATOIRE',
            nom_etablissement='Labo Test',
            date_debut_convention=timezone.now().date(),
            created_by=self.user,
        )
        self.assertTrue(p.convention_active)

    def test_convention_active_avec_date_fin_future(self):
        p = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='LABORATOIRE',
            nom_etablissement='Labo Test',
            date_debut_convention=timezone.now().date() - timedelta(days=30),
            date_fin_convention=timezone.now().date() + timedelta(days=30),
            created_by=self.user,
        )
        self.assertTrue(p.convention_active)

    def test_convention_active_avec_date_fin_passee(self):
        p = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='LABORATOIRE',
            nom_etablissement='Labo Test',
            date_debut_convention=timezone.now().date() - timedelta(days=60),
            date_fin_convention=timezone.now().date() - timedelta(days=1),
            created_by=self.user,
        )
        self.assertFalse(p.convention_active)

    def test_convention_active_sans_dates(self):
        p = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='LABORATOIRE',
            nom_etablissement='Labo Test',
            created_by=self.user,
        )
        self.assertFalse(p.convention_active)

    def test_tenant_isolation_partenaire(self):
        other_mut = Mutualite.objects.create(
            nif='4000000502',
            nom='Autre Mut',
            nom_responsable='Autre',
            telephone='79123457',
            email='autre@test.com',
            province='Gitega',
            commune='Gitega',
        )
        p1 = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='HOPITAL',
            nom_etablissement='Hôpital A',
            created_by=self.user,
        )
        p2 = Partenaire.objects.create(
            mutualite=other_mut,
            type_partenaire='PHARMACIE',
            nom_etablissement='Pharmacie B',
            created_by=self.user,
        )
        self.assertEqual(Partenaire.objects.filter(mutualite=self.mutualite).count(), 1)
        self.assertEqual(Partenaire.objects.all().count(), 2)

    def test_nb_factures_property(self):
        p = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='HOPITAL',
            nom_etablissement='Hôpital Test',
            created_by=self.user,
        )
        self.assertEqual(p.nb_factures, 0)

    def test_created_by_and_dates_set_auto(self):
        p = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='DENTISTE',
            nom_etablissement='Dentiste Test',
            created_by=self.user,
        )
        self.assertIsNotNone(p.date_creation)
        self.assertIsNotNone(p.date_modification)
        self.assertEqual(p.created_by, self.user)


class ConventionModelTest(TestCase):
    def setUp(self):
        self.mutualite = Mutualite.objects.create(
            nif='4000000601',
            nom='Mutualité Conventions',
            nom_responsable='Test',
            telephone='79123460',
            email='conv@test.com',
            province='Bujumbura',
            commune='Mairie',
            date_expiration=timezone.now() + timedelta(days=365),
        )
        self.user = User.objects.create_user(
            username='agent_conv',
            password='test123',
            mutualite=self.mutualite,
            role='AGENT',
        )
        self.partenaire = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='HOPITAL',
            nom_etablissement='Hôpital Test',
            created_by=self.user,
        )

    def test_numero_convention_genere_automatiquement(self):
        c = Convention.objects.create(
            partenaire=self.partenaire,
            mutualite=self.mutualite,
            date_debut=date(2026, 1, 1),
            date_fin=date(2027, 1, 1),
            created_by=self.user,
        )
        self.assertTrue(c.numero_convention.startswith('CONV-2026-'))

    def test_numero_convention_incremente(self):
        c1 = Convention.objects.create(
            partenaire=self.partenaire,
            mutualite=self.mutualite,
            date_debut=date(2026, 1, 1),
            date_fin=date(2027, 1, 1),
            created_by=self.user,
        )
        c2 = Convention.objects.create(
            partenaire=self.partenaire,
            mutualite=self.mutualite,
            date_debut=date(2026, 2, 1),
            date_fin=date(2027, 2, 1),
            created_by=self.user,
        )
        self.assertEqual(c1.numero_convention, 'CONV-2026-0001')
        self.assertEqual(c2.numero_convention, 'CONV-2026-0002')

    def test_numero_convention_collision_avoidance(self):
        # Créer manuellement un numero pour tester le saut d'index
        Convention.objects.create(
            partenaire=self.partenaire,
            mutualite=self.mutualite,
            numero_convention='CONV-2026-0005',
            date_debut=date(2026, 1, 1),
            date_fin=date(2027, 1, 1),
            created_by=self.user,
        )
        c = Convention.objects.create(
            partenaire=self.partenaire,
            mutualite=self.mutualite,
            date_debut=date(2026, 1, 1),
            date_fin=date(2027, 1, 1),
            created_by=self.user,
        )
        self.assertEqual(c.numero_convention, 'CONV-2026-0006')

    def test_accepter_demande_partenaire(self):
        self.client.login(username='agent_conv', password='test123')
        p_attente = Partenaire.all_objects.create(
            mutualite=None,
            type_partenaire='CLINIQUE',
            nom_etablissement='Clinique En Attente',
            statut='EN_ATTENTE',
        )
        from django.urls import reverse
        response = self.client.get(reverse('partenaires:accepter_demande', args=[p_attente.pk]))
        self.assertEqual(response.status_code, 302)
        p_attente.refresh_from_db()
        self.assertEqual(p_attente.statut, 'ACTIF')
        self.assertEqual(p_attente.mutualite, self.mutualite)
        self.assertTrue(Convention.objects.filter(partenaire=p_attente, mutualite=self.mutualite).exists())


    def test_mutualite_auto_assignee_depuis_partenaire(self):
        c = Convention.objects.create(
            partenaire=self.partenaire,
            date_debut=date(2026, 1, 1),
            date_fin=date(2027, 1, 1),
            created_by=self.user,
        )
        self.assertEqual(c.mutualite, self.mutualite)

    def test_str_representation(self):
        c = Convention.objects.create(
            partenaire=self.partenaire,
            mutualite=self.mutualite,
            date_debut=date(2026, 1, 1),
            date_fin=date(2027, 1, 1),
            created_by=self.user,
        )
        self.assertIn(c.numero_convention, str(c))
        self.assertIn(self.partenaire.nom_etablissement, str(c))

    def test_default_statut(self):
        c = Convention.objects.create(
            partenaire=self.partenaire,
            mutualite=self.mutualite,
            date_debut=date(2026, 1, 1),
            date_fin=date(2027, 1, 1),
            created_by=self.user,
        )
        self.assertEqual(c.statut, 'ACTIVE')

    def test_tenant_isolation_convention(self):
        other_mut = Mutualite.objects.create(
            nif='4000000602',
            nom='Autre Mut',
            nom_responsable='Autre',
            telephone='79123461',
            email='autre2@test.com',
            province='Gitega',
            commune='Gitega',
        )
        other_part = Partenaire.objects.create(
            mutualite=other_mut,
            type_partenaire='PHARMACIE',
            nom_etablissement='Pharmacie Autre',
            created_by=self.user,
        )
        c1 = Convention.objects.create(
            partenaire=self.partenaire,
            mutualite=self.mutualite,
            date_debut=date(2026, 1, 1),
            date_fin=date(2027, 1, 1),
            created_by=self.user,
        )
        c2 = Convention.objects.create(
            partenaire=other_part,
            mutualite=other_mut,
            date_debut=date(2026, 1, 1),
            date_fin=date(2027, 1, 1),
            created_by=self.user,
        )
        self.assertEqual(Convention.objects.filter(mutualite=self.mutualite).count(), 1)
        self.assertEqual(Convention.objects.all().count(), 2)


class UtilisateurPartenaireModelTest(TestCase):
    def setUp(self):
        self.mutualite = Mutualite.objects.create(
            nif='4000000701',
            nom='Mutualité Users',
            nom_responsable='Test',
            telephone='79123470',
            email='users@test.com',
            province='Bujumbura',
            commune='Mairie',
        )
        self.user = User.objects.create_user(
            username='agent_users',
            password='test123',
            mutualite=self.mutualite,
            role='AGENT',
        )
        self.partenaire = Partenaire.objects.create(
            mutualite=self.mutualite,
            type_partenaire='PHARMACIE',
            nom_etablissement='Pharmacie Test',
            created_by=self.user,
        )

    def test_mutualite_auto_assignee_depuis_partenaire(self):
        up = UtilisateurPartenaire.objects.create(
            partenaire=self.partenaire,
            username='pharmacien1',
            password='secret123',
            role='PHARMACIEN',
        )
        self.assertEqual(up.mutualite, self.mutualite)

    def test_str_representation(self):
        up = UtilisateurPartenaire.objects.create(
            partenaire=self.partenaire,
            username='gestionnaire1',
            password='secret123',
            role='GESTIONNAIRE',
        )
        self.assertIn(up.username, str(up))
        self.assertIn(self.partenaire.nom_etablissement, str(up))

    def test_default_role(self):
        up = UtilisateurPartenaire.objects.create(
            partenaire=self.partenaire,
            username='default_role',
            password='secret123',
        )
        self.assertEqual(up.role, 'GESTIONNAIRE')

    def test_default_actif(self):
        up = UtilisateurPartenaire.objects.create(
            partenaire=self.partenaire,
            username='default_actif',
            password='secret123',
        )
        self.assertTrue(up.actif)

    def test_tenant_isolation_utilisateur_partenaire(self):
        other_mut = Mutualite.objects.create(
            nif='4000000702',
            nom='Autre Mut',
            nom_responsable='Autre',
            telephone='79123471',
            email='autre3@test.com',
            province='Gitega',
            commune='Gitega',
        )
        other_part = Partenaire.objects.create(
            mutualite=other_mut,
            type_partenaire='HOPITAL',
            nom_etablissement='Hôpital Autre',
            created_by=self.user,
        )
        up1 = UtilisateurPartenaire.objects.create(
            partenaire=self.partenaire,
            username='user1',
            password='pass1',
            role='MEDECIN',
        )
        up2 = UtilisateurPartenaire.objects.create(
            partenaire=other_part,
            username='user2',
            password='pass2',
            role='RECEPTIONNISTE',
        )
        self.assertEqual(
            UtilisateurPartenaire.objects.filter(mutualite=self.mutualite).count(), 1
        )
        self.assertEqual(UtilisateurPartenaire.objects.all().count(), 2)


