from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from affilies.models import Affilie
from origines.models import Origine
from affilies.views import (
    prochain_numero_affiliation,
    formater_numero_affiliation,
    largeur_affiliation_defaut,
    format_affiliation_defaut,
)

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
        self.assertEqual(aff.nom_complet, 'Dupont Jean')
        self.assertEqual(str(aff), 'AFF-2026-0001 — Dupont Jean')

    def test_age_calculation(self):
        from datetime import date
        aff = self._create_affilie(date_naissance=date(2000, 6, 15))
        self.assertIsInstance(aff.age, int)
        self.assertGreater(aff.age, 0)

    def test_soft_delete(self):
        aff = self._create_affilie()
        aff.delete(user=self.user)
        self.assertTrue(aff.supprime)
        self.assertFalse(aff.actif)
        self.assertIsNotNone(aff.date_suppression)

    def test_auto_affiliation_id(self):
        """Vérifie que l'ID est auto-généré au format code_mutualite-PK."""
        aff = Affilie.objects.create(
            nom='Test',
            prenom='Auto',
            sexe='M',
            date_naissance='1990-01-15',
        )
        self.assertIsNotNone(aff.numero_affiliation)
        self.assertIn(str(aff.pk), aff.numero_affiliation)
        self.assertRegex(aff.numero_affiliation, r'^MUT-\d+$')


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


class AffilieImportNumeroTest(TestCase):
    def test_formater_numero_affiliation(self):
        self.assertEqual(formater_numero_affiliation(1, 1), 'AFF-1')
        self.assertEqual(formater_numero_affiliation(1, 2), 'AFF-01')
        self.assertEqual(formater_numero_affiliation(1, 3), 'AFF-001')
        self.assertEqual(formater_numero_affiliation(12, 4), 'AFF-0012')
        self.assertEqual(formater_numero_affiliation(1, 5), 'AFF-00001')

    def test_prochain_numero_affiliation(self):
        Affilie.objects.create(
            numero_affiliation='AFF-001',
            nom='Dupont', prenom='Jean', sexe='M',
            date_naissance='1990-01-15',
        )
        Affilie.objects.create(
            numero_affiliation='AFF-005',
            nom='Martin', prenom='Paul', sexe='M',
            date_naissance='1985-03-20',
        )
        self.assertEqual(prochain_numero_affiliation(), 6)

    def test_largeur_defaut_sans_import(self):
        self.assertEqual(largeur_affiliation_defaut(), 1)
        self.assertEqual(format_affiliation_defaut(), '0-1')

    def test_largeur_defaut_apres_import(self):
        Affilie.objects.create(
            numero_affiliation='AFF-0001',
            nom='Dupont', prenom='Jean', sexe='M',
            date_naissance='1990-01-15',
        )
        self.assertEqual(largeur_affiliation_defaut(), 4)
        self.assertEqual(format_affiliation_defaut(), '0000-0001')
