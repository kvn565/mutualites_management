from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from core.models import Mutualite, CleActivation, AuditCle

User = get_user_model()


class MutualiteModelTest(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            username='superadmin',
            password='test123',
            email='super@admin.com',
            role='SUPER_ADMIN',
        )

    def test_generer_code_unique(self):
        m1 = Mutualite.objects.create(
            nif='4000000001',
            nom='Mutualité Test 1',
            nom_responsable='Jean Dupont',
            telephone='79123456',
            email='test1@test.com',
            province='Bujumbura',
            commune='Mairie',
            created_by=self.super_admin,
        )
        self.assertTrue(m1.code_mutualite.startswith('MUT-'))
        self.assertEqual(len(m1.code_mutualite), 10)  # MUT- + 6 chars

    def test_activer_essai(self):
        m = Mutualite.objects.create(
            nif='4000000002',
            nom='Mutualité Test 2',
            nom_responsable='Pierre Nkurunziza',
            telephone='79123457',
            email='test2@test.com',
            province='Gitega',
            commune='Gitega',
            created_by=self.super_admin,
        )
        self.assertEqual(m.statut, 'EN_ATTENTE')
        self.assertFalse(m.essai_gratuit)

        m.activer_essai()
        self.assertTrue(m.essai_gratuit)
        self.assertEqual(m.statut, 'ESSAI')
        self.assertEqual(m.type_abonnement, 'ESSAI_14J')
        self.assertIsNotNone(m.date_debut_essai)
        self.assertIsNotNone(m.date_fin_essai)
        self.assertEqual((m.date_fin_essai - m.date_debut_essai).days, 14)
        self.assertIsNotNone(m.cle_activation)
        self.assertTrue(m.cle_activation.startswith('KEY-'))

    def test_licence_valide_pendant_essai(self):
        m = Mutualite.objects.create(
            nif='4000000003',
            nom='Mutualité Test 3',
            nom_responsable='Alain Kay',
            telephone='79123458',
            email='test3@test.com',
            province='Bujumbura',
            commune='Mairie',
            created_by=self.super_admin,
        )
        m.activer_essai()
        self.assertTrue(m.licence_valide)

    def test_licence_expiree(self):
        m = Mutualite.objects.create(
            nif='4000000004',
            nom='Mutualité Test 4',
            nom_responsable='Test User',
            telephone='79123459',
            email='test4@test.com',
            province='Bujumbura',
            commune='Mairie',
            created_by=self.super_admin,
        )
        m.activer_essai()
        m.date_fin_essai = timezone.now() - timedelta(days=1)
        m.date_expiration = m.date_fin_essai
        m.save()
        m._mettre_a_jour_statut()
        m.save()
        self.assertFalse(m.licence_valide)
        self.assertEqual(m.statut, 'EXPIRE')

    def test_activer_licence_payante(self):
        m = Mutualite.objects.create(
            nif='4000000005',
            nom='Mutualité Test 5',
            nom_responsable='Test User',
            telephone='79123460',
            email='test5@test.com',
            province='Bujumbura',
            commune='Mairie',
            created_by=self.super_admin,
        )
        m.activer_licence('ANNUEL', 365)
        self.assertEqual(m.statut, 'ACTIF')
        self.assertEqual(m.type_abonnement, 'ANNUEL')
        self.assertFalse(m.essai_gratuit)
        self.assertIsNotNone(m.cle_activation)
        self.assertIsNotNone(m.date_expiration)

    def test_jours_restants(self):
        m = Mutualite.objects.create(
            nif='4000000006',
            nom='Mutualité Test 6',
            nom_responsable='Test User',
            telephone='79123461',
            email='test6@test.com',
            province='Bujumbura',
            commune='Mairie',
            created_by=self.super_admin,
        )
        m.activer_essai()
        self.assertGreater(m.jours_restants, 0)

    def test_statut_en_attente_par_defaut(self):
        m = Mutualite.objects.create(
            nif='4000000007',
            nom='Mutualité Test 7',
            nom_responsable='Test User',
            telephone='79123462',
            email='test7@test.com',
            province='Bujumbura',
            commune='Mairie',
            created_by=self.super_admin,
        )
        self.assertEqual(m.statut, 'EN_ATTENTE')


class MutualiteAPITest(APITestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            username='superadmin',
            password='test123',
            email='super@admin.com',
            role='SUPER_ADMIN',
        )
        self.normal_user = User.objects.create_user(
            username='normal',
            password='test123',
            email='normal@user.com',
            role='AGENT',
        )
        self.client = APIClient()

    def test_liste_mutualites_non_auth(self):
        response = self.client.get('/api/superadmin/mutualites/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_liste_mutualites_non_superadmin(self):
        self.client.login(username='normal', password='test123')
        response = self.client.get('/api/superadmin/mutualites/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_liste_mutualites_superadmin(self):
        self.client.login(username='superadmin', password='test123')
        response = self.client.get('/api/superadmin/mutualites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_creer_mutualite(self):
        self.client.login(username='superadmin', password='test123')
        data = {
            'nif': '4000000100',
            'nom': 'Nouvelle Mutualité',
            'nom_responsable': 'Paul Biya',
            'telephone': '79123499',
            'email': 'nouvelle@mutualite.com',
            'province': 'Bujumbura',
            'commune': 'Mairie',
        }
        response = self.client.post('/api/superadmin/mutualites/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['statut'], 'ESSAI')
        self.assertTrue(response.data['essai_gratuit'])
        self.assertIsNotNone(response.data['code_mutualite'])
        self.assertIsNotNone(response.data['cle_activation'])

    def test_tableau_de_bord(self):
        self.client.login(username='superadmin', password='test123')
        response = self.client.get('/api/superadmin/tableau-de-bord/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_mutualites', response.data)
        self.assertIn('mutualites_actives', response.data)

    def test_suspendre_mutualite(self):
        self.client.login(username='superadmin', password='test123')
        m = Mutualite.objects.create(
            nif='4000000200',
            nom='Mutualité à suspendre',
            nom_responsable='Test',
            telephone='79123470',
            email='suspendre@test.com',
            province='Bujumbura',
            commune='Mairie',
            created_by=self.super_admin,
        )
        m.activer_essai()
        response = self.client.post(f'/api/superadmin/mutualites/{m.pk}/suspendre/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['statut'], 'SUSPENDU')

    def test_renouveler_licence(self):
        self.client.login(username='superadmin', password='test123')
        m = Mutualite.objects.create(
            nif='4000000300',
            nom='Mutualité licence',
            nom_responsable='Test',
            telephone='79123471',
            email='licence@test.com',
            province='Bujumbura',
            commune='Mairie',
            created_by=self.super_admin,
        )
        response = self.client.post(
            f'/api/superadmin/mutualites/{m.pk}/renouveler-licence/',
            {'type_abonnement': 'ANNUEL', 'duree_jours': 365},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['statut'], 'ACTIF')
        self.assertEqual(response.data['type_abonnement'], 'ANNUEL')

    def test_recherche_par_nif(self):
        self.client.login(username='superadmin', password='test123')
        Mutualite.objects.create(
            nif='9999999999',
            nom='Mutualité Recherche',
            nom_responsable='Chercheur',
            telephone='79123480',
            email='recherche@test.com',
            province='Bujumbura',
            commune='Mairie',
            created_by=self.super_admin,
        )
        response = self.client.get('/api/superadmin/mutualites/?search=9999999999')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class ActivationKeyFlowTest(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            username='superadmin',
            password='test123',
            email='super@admin.com',
            role='SUPER_ADMIN',
        )
        self.mutualite = Mutualite.objects.create(
            nif='4000000500',
            nom='Mutualité Test Clé',
            nom_responsable='Gestionnaire',
            telephone='79123491',
            email='gestionnaire@test.com',
            province='Bujumbura',
            commune='Mairie',
            created_by=self.super_admin,
        )
        self.mutualite.activer_essai()
        self.mutualite.date_expiration = timezone.now() - timedelta(days=1)
        self.mutualite.date_fin_essai = timezone.now() - timedelta(days=1)
        self.mutualite.statut = 'EXPIRE'
        self.mutualite.save()

    def test_generer_cle_pour_mutualite_expiree(self):
        """Une clé peut être générée pour une mutualité dont la licence est expirée."""
        self.assertEqual(self.mutualite.statut, 'EXPIRE')
        self.assertFalse(self.mutualite.licence_valide)

        cle = CleActivation.objects.create(
            mutualite=self.mutualite,
            type_plan='6MOIS',
            active=True,
            utilisee=False,
            statut='DISPONIBLE',
            cree_par=self.super_admin.username,
        )

        self.assertEqual(cle.statut, 'DISPONIBLE')
        self.assertIsNotNone(cle.cle_visible)
        self.assertTrue(cle.cle_visible.startswith(('MUT', 'MUT')) or 'MUT' in cle.cle_visible)

    def test_activer_mutualite_avec_cle_generee(self):
        """Une mutualité expirée redevient ACTIF après activation d'une clé générée."""
        cle = CleActivation.objects.create(
            mutualite=self.mutualite,
            type_plan='6MOIS',
            active=True,
            utilisee=False,
            statut='DISPONIBLE',
            cree_par=self.super_admin.username,
        )

        cle.utilisee = True
        cle.date_utilisation = timezone.now()
        cle.save()

        self.mutualite.cle_activation = cle.cle_visible
        self.mutualite.date_activation = cle.date_debut
        self.mutualite.date_expiration = cle.date_fin
        self.mutualite.type_abonnement = cle.type_plan
        self.mutualite.essai_gratuit = False
        self.mutualite.statut = 'ACTIF'
        self.mutualite.save()

        self.mutualite.refresh_from_db()
        cle.refresh_from_db()

        self.assertEqual(self.mutualite.statut, 'ACTIF')
        self.assertTrue(self.mutualite.licence_valide)
        self.assertEqual(cle.statut, 'ACTIVE')
        self.assertTrue(cle.utilisee)

    def test_generer_cle_via_vue_superadmin(self):
        """La vue cle_generer crée une clé DISPONIBLE sans erreur."""
        self.client.login(username='superadmin', password='test123')

        response = self.client.post('/superadmin/cles/generer/', {
            'mutualite': self.mutualite.pk,
            'type_plan': '6MOIS',
        })

        self.assertRedirects(response, '/superadmin/cles/')

        cle = CleActivation.objects.filter(mutualite=self.mutualite).first()
        self.assertIsNotNone(cle)
        self.assertEqual(cle.statut, 'DISPONIBLE')
        self.assertFalse(cle.utilisee)
        self.assertEqual(cle.type_plan, '6MOIS')


class ExpiredLicenseCommandTest(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            username='superadmin',
            password='test123',
        )
        self.mutualite = Mutualite.objects.create(
            nif='4000000400',
            nom='Mutualité Expirée',
            nom_responsable='Test',
            telephone='79123490',
            email='expiree@test.com',
            province='Bujumbura',
            commune='Mairie',
            created_by=self.super_admin,
        )
        self.mutualite.activer_essai()

    def test_detect_expired_licenses(self):
        self.mutualite.date_expiration = timezone.now() - timedelta(days=1)
        self.mutualite.date_fin_essai = timezone.now() - timedelta(days=1)
        self.mutualite.save()

        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command('detect_expired_licenses', stdout=out)
        self.assertIn('licence(s) expirée(s)', out.getvalue())

        self.mutualite.refresh_from_db()
        self.assertEqual(self.mutualite.statut, 'EXPIRE')
