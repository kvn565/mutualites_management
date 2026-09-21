from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from core.models import Mutualite

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

    def test_activer_essai_sans_cle(self):
        """Mode sans clé : activer_essai active directement en ACTIF."""
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
        m.activer_essai()
        self.assertEqual(m.statut, 'ACTIF')
        self.assertFalse(m.essai_gratuit)
        self.assertIsNotNone(m.date_activation)

    def test_demande_en_attente_preservee(self):
        """Comme la référence : une nouvelle inscription reste EN_ATTENTE
        (visible dans les validations superadmin), sans aucune clé."""
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
        self.assertFalse(hasattr(m, 'cle_activation'))

    def test_pas_de_blocage_auto_avec_date_passee(self):
        """Une date d'expiration passée ne fait plus passer en EXPIRE :
        EN_ATTENTE reste EN_ATTENTE, ACTIF reste ACTIF."""
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
        m.date_expiration = timezone.now() - timedelta(days=1)
        m.save()
        m.refresh_from_db()
        self.assertEqual(m.statut, 'EN_ATTENTE')

        m.statut = 'ACTIF'
        m.save()
        m.refresh_from_db()
        self.assertEqual(m.statut, 'ACTIF')


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
        self.assertEqual(response.data['statut'], 'ACTIF')
        self.assertIsNotNone(response.data['code_mutualite'])

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
