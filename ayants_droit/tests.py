from io import BytesIO

import openpyxl
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from affilies.models import Affilie
from ayants_droit.models import AyantDroit

User = get_user_model()


def _excel(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    return SimpleUploadedFile('ayants.xlsx', out.read(),
                              content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


class AyantDroitImportTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testagent',
            password='testpass123',
            first_name='Test',
            last_name='Agent',
            role='AGENT',
        )
        self.affilie = Affilie.objects.create(
            numero_affiliation='AFF-001',
            nom='Dupont', prenom='Jean', sexe='M',
            date_naissance='1990-01-15',
        )
        self.client.login(username='testagent', password='testpass123')

    def test_import_avec_colonne_affiliation(self):
        fichier = _excel([
            ['N_affiliation', 'Nom', 'Prenom', 'Sexe', 'Date_naissance', 'Lien_parente', 'Age_limite'],
            ['AFF-001', 'NDIMUBANDI', 'Marie', 'F', '1992-08-21', 'CONJOINTE', '18'],
            ['AFF-001', 'NDIMUBANDI', 'Paul', 'M', '2015-06-10', 'ENFANT', '21'],
        ])
        response = self.client.post(reverse('ayants_droit:importer'), {'fichier': fichier})
        self.assertEqual(response.status_code, 200)
        ayants = AyantDroit.objects.filter(affilie=self.affilie)
        self.assertEqual(ayants.count(), 2)
        conjoint = ayants.get(lien_parente='CONJOINT')
        self.assertEqual(conjoint.nom, 'NDIMUBANDI')
        self.assertEqual(conjoint.prenom, 'Marie')
        self.assertEqual(conjoint.sexe, 'F')
        enfant = ayants.get(lien_parente='ENFANT')
        self.assertEqual(enfant.age_limite, 21)

    def test_import_avec_affilie_selectionne(self):
        fichier = _excel([
            ['Nom', 'Prenom', 'Sexe', 'Date_naissance', 'Lien_parente'],
            ['NDIMUBANDI', 'Anne', 'F', '1993-01-01', 'PARENT'],
        ])
        response = self.client.post(reverse('ayants_droit:importer'),
                                    {'affilie': self.affilie.pk, 'fichier': fichier})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AyantDroit.objects.filter(affilie=self.affilie).count(), 1)
        self.assertEqual(AyantDroit.objects.get(affilie=self.affilie).lien_parente, 'PARENT')

    def test_import_affilie_introuvable(self):
        fichier = _excel([
            ['N_affiliation', 'Nom', 'Sexe', 'Date_naissance', 'Lien_parente'],
            ['AFF-999', 'X', 'M', '1990-01-01', 'ENFANT'],
        ])
        response = self.client.post(reverse('ayants_droit:importer'), {'fichier': fichier})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AyantDroit.objects.count(), 0)
        self.assertContains(response, 'Affilié introuvable')

    def test_modele_import(self):
        response = self.client.get(reverse('ayants_droit:modele_import'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])
