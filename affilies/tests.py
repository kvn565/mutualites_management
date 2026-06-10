from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from affilies.models import Affilie
from origines.models import Origine

User = get_user_model()


class AffilieModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testagent',
            password='testpass123',
            first_name='Test',
            last_name='Agent',
            role='AGENT',
        )
        self.origine = Origine.objects.create(
            nom='Test Entreprise',
            type_origine='ENTREPRISE',
        )

    def _create_affilie(self, **kwargs):
        defaults = {
            'numero_affiliation': 'AFF-2026-0001',
            'nom': 'Dupont',
            'prenom': 'Jean',
            'sexe': 'M',
            'date_naissance': '1990-01-15',
            'telephone': '71234567',
            'type_adhesion': 'INDIVIDUELLE',
            'statut': 'ACTIF',
            'origine': self.origine,
            'cree_par': self.user,
        }
        defaults.update(kwargs)
        return Affilie.objects.create(**defaults)

    def test_create_affilie(self):
        aff = self._create_affilie()
        self.assertEqual(aff.nom_complet, 'Dupont  Jean')
        self.assertEqual(str(aff), 'AFF-2026-0001 — Dupont Jean')

    def test_age_calculation(self):
        from datetime import date
        aff = self._create_affilie(date_naissance=date(2000, 6, 15))
        self.assertIsInstance(aff.age, int)
        self.assertGreater(aff.age, 0)

    def test_soft_delete(self):
        aff = self._create_affilie()
        aff.soft_delete()
        self.assertTrue(aff.supprime)
        self.assertFalse(aff.actif)
        self.assertIsNotNone(aff.date_suppression)

    def test_generer_numero(self):
        self._create_affilie(numero_affiliation='AFF-2026-0001')
        numero = Affilie.generer_numero()
        self.assertTrue(numero.startswith('AFF-2026-'))
        self.assertIn(numero, [f'AFF-2026-{i:04d}' for i in range(1, 100)])


class AffilieViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testagent',
            password='testpass123',
            first_name='Test',
            last_name='Agent',
            role='AGENT',
        )
        self.origine = Origine.objects.create(nom='Test', type_origine='ENTREPRISE')
        self.affilie = Affilie.objects.create(
            numero_affiliation='AFF-2026-0001',
            nom='Dupont',
            prenom='Jean',
            sexe='M',
            date_naissance='1990-01-15',
            telephone='71234567',
            type_adhesion='INDIVIDUELLE',
            statut='ACTIF',
            origine=self.origine,
            cree_par=self.user,
        )

    def test_liste_requires_login(self):
        response = self.client.get(reverse('affilies:liste'))
        self.assertNotEqual(response.status_code, 200)

    def test_liste_with_login(self):
        self.client.login(username='testagent', password='testpass123')
        response = self.client.get(reverse('affilies:liste'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dupont')

    def test_detail_view(self):
        self.client.login(username='testagent', password='testpass123')
        response = self.client.get(reverse('affilies:detail', kwargs={'pk': self.affilie.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AFF-2026-0001')

    def test_search(self):
        self.client.login(username='testagent', password='testpass123')
        response = self.client.get(reverse('affilies:liste'), {'q': 'Dupont'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dupont')

    def test_filter_by_statut(self):
        self.client.login(username='testagent', password='testpass123')
        response = self.client.get(reverse('affilies:liste'), {'statut': 'ACTIF'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dupont')
