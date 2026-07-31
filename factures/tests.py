from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta

from core.models import Mutualite
from partenaires.models import Partenaire
from services_sante.models import ServiceSante
from affilies.models import Affilie
from .models import Facture, LigneFacture

User = get_user_model()


class FactureModelTest(TestCase):
    def setUp(self):
        self.mutualite = Mutualite.objects.create(
            nif='4000002001', nom='Mutualité Factures',
            nom_responsable='Test', telephone='79123400',
            email='fact@test.com', province='Bujumbura', commune='Mairie',
        )
        self.user = User.objects.create_user(
            username='agent_fact', password='test123',
            mutualite=self.mutualite, role='AGENT',
        )
        self.partenaire = Partenaire.objects.create(
            mutualite=self.mutualite, type_partenaire='HOPITAL',
            nom_etablissement='Hôpital Test', created_by=self.user,
        )
        self.affilie = Affilie.objects.create(
            mutualite=self.mutualite, numero_affiliation='MEM-00001',
            nom='Dupont', prenom='Jean', sexe='M',
            date_naissance=date(1990, 1, 1),
        )

    def test_generer_numero_format(self):
        numero = Facture.generer_numero()
        self.assertRegex(numero, r'^FAC-\d{6}-\d+$')

    def test_generer_numero_mensuel(self):
        today = timezone.now()
        prefix = today.strftime('FAC-%Y%m-')
        n1 = Facture.generer_numero()
        Facture.objects.create(
            numero=n1, mutualite=self.mutualite,
            date=today.date(), partenaire=self.partenaire,
            affilie=self.affilie, cree_par=self.user,
        )
        n2 = Facture.generer_numero()
        self.assertTrue(n2.startswith(prefix))
        num1 = int(n1.split('-')[2])
        num2 = int(n2.split('-')[2])
        self.assertEqual(num2, num1 + 1)

    def test_default_statut(self):
        f = Facture.objects.create(
            numero='FAC-202606-0001', mutualite=self.mutualite,
            date=date(2026, 6, 10), partenaire=self.partenaire,
            affilie=self.affilie, cree_par=self.user,
        )
        self.assertEqual(f.statut, 'BROUILLON')

    def test_str_representation(self):
        f = Facture.objects.create(
            numero='FAC-202606-0002', mutualite=self.mutualite,
            date=date(2026, 6, 10), partenaire=self.partenaire,
            affilie=self.affilie, cree_par=self.user,
        )
        self.assertIn(f.numero, str(f))
        self.assertIn(self.partenaire.nom_etablissement, str(f))

    def test_tenant_isolation(self):
        other_mut = Mutualite.objects.create(
            nif='4000002002', nom='Autre Mut',
            nom_responsable='Autre', telephone='79123401',
            email='autre@test.com', province='Gitega', commune='Gitega',
        )
        other_part = Partenaire.objects.create(
            mutualite=other_mut, type_partenaire='PHARMACIE',
            nom_etablissement='Pharmacie Autre', created_by=self.user,
        )
        other_aff = Affilie.objects.create(
            mutualite=other_mut, numero_affiliation='MEM-00002',
            nom='Pierre', prenom='Paul', sexe='M',
            date_naissance=date(1985, 5, 5),
        )
        Facture.objects.create(
            numero='FAC-202606-0003', mutualite=self.mutualite,
            date=date(2026, 6, 10), partenaire=self.partenaire,
            affilie=self.affilie, cree_par=self.user,
        )
        Facture.objects.create(
            numero='FAC-202606-0004', mutualite=other_mut,
            date=date(2026, 6, 10), partenaire=other_part,
            affilie=other_aff, cree_par=self.user,
        )
        self.assertEqual(Facture.objects.filter(mutualite=self.mutualite).count(), 1)
        self.assertEqual(Facture.objects.all().count(), 2)


class LigneFactureModelTest(TestCase):
    def setUp(self):
        self.mutualite = Mutualite.objects.create(
            nif='4000003001', nom='Mutualité Lignes',
            nom_responsable='Test', telephone='79123410',
            email='lignes@test.com', province='Bujumbura', commune='Mairie',
        )
        self.user = User.objects.create_user(
            username='agent_ligne', password='test123',
            mutualite=self.mutualite, role='AGENT',
        )
        self.partenaire = Partenaire.objects.create(
            mutualite=self.mutualite, type_partenaire='HOPITAL',
            nom_etablissement='Hôpital Ligne', created_by=self.user,
        )
        self.affilie = Affilie.objects.create(
            mutualite=self.mutualite, numero_affiliation='MEM-00010',
            nom='Test', prenom='User', sexe='F',
            date_naissance=date(1995, 3, 15),
        )
        self.service = ServiceSante.objects.create(
            mutualite=self.mutualite, code='CONS-001',
            nom='Consultation générale', categorie='CONSULTATION',
            taux_prise_en_charge=80,
        )
        self.facture = Facture.objects.create(
            numero='FAC-202606-0010', mutualite=self.mutualite,
            date=date(2026, 6, 10), partenaire=self.partenaire,
            affilie=self.affilie, cree_par=self.user,
        )

    def test_total_ligne(self):
        ligne = LigneFacture.objects.create(
            facture=self.facture, mutualite=self.mutualite,
            service=self.service, designation='Consultation',
            quantite=2, prix_unitaire=5000, taux_applique=80,
        )
        self.assertEqual(ligne.total_ligne, 10000)

    def test_part_mutualite(self):
        ligne = LigneFacture.objects.create(
            facture=self.facture, mutualite=self.mutualite,
            service=self.service, designation='Consultation',
            quantite=1, prix_unitaire=10000, taux_applique=80,
        )
        self.assertEqual(ligne.part_mutualite, 8000)

    def test_part_patient(self):
        ligne = LigneFacture.objects.create(
            facture=self.facture, mutualite=self.mutualite,
            service=self.service, designation='Consultation',
            quantite=1, prix_unitaire=10000, taux_applique=80,
        )
        self.assertEqual(ligne.part_patient, 2000)

    def test_arrondi(self):
        ligne = LigneFacture.objects.create(
            facture=self.facture, mutualite=self.mutualite,
            service=self.service, designation='Médicament',
            quantite=3, prix_unitaire=3333, taux_applique=75,
        )
        self.assertEqual(ligne.total_ligne, 9999)
        self.assertEqual(ligne.part_mutualite, 7499.25)
        self.assertEqual(ligne.part_patient, 2499.75)


class FactureWorkflowTest(TestCase):
    def setUp(self):
        self.mutualite = Mutualite.objects.create(
            nif='4000004001', nom='Mutualité Workflow',
            nom_responsable='Test', telephone='79123420',
            email='wf@test.com', province='Bujumbura', commune='Mairie',
        )
        self.admin = User.objects.create_user(
            username='admin_wf', password='test123',
            mutualite=self.mutualite, role='ADMIN_MUTUALITE',
        )
        self.agent = User.objects.create_user(
            username='agent_wf', password='test123',
            mutualite=self.mutualite, role='AGENT',
        )
        self.comptable = User.objects.create_user(
            username='compta_wf', password='test123',
            mutualite=self.mutualite, role='COMPTABLE',
        )
        self.super_admin = User.objects.create_superuser(
            username='super_wf', password='test123',
        )
        self.partenaire = Partenaire.objects.create(
            mutualite=self.mutualite, type_partenaire='CLINIQUE',
            nom_etablissement='Clinique Workflow', created_by=self.admin,
        )
        self.affilie = Affilie.objects.create(
            mutualite=self.mutualite, numero_affiliation='MEM-00020',
            nom='Workflow', prenom='Test', sexe='M',
            date_naissance=date(1980, 7, 7),
        )
        self.service = ServiceSante.objects.create(
            mutualite=self.mutualite, code='LAB-001',
            nom='Analyse sanguine', categorie='LABORATOIRE',
            taux_prise_en_charge=80,
        )

    def _creer_facture(self, statut='BROUILLON'):
        f = Facture.objects.create(
            numero=Facture.generer_numero(), mutualite=self.mutualite,
            date=date(2026, 6, 10), partenaire=self.partenaire,
            affilie=self.affilie, statut=statut, cree_par=self.agent,
        )
        LigneFacture.objects.create(
            facture=f, mutualite=self.mutualite,
            service=self.service, designation='Analyse',
            quantite=1, prix_unitaire=5000, taux_applique=80,
        )
        return f

    # --- Super Admin blocked ---
    def test_super_admin_bloque_liste(self):
        self.client.login(username='super_wf', password='test123')
        response = self.client.get('/factures/')
        self.assertRedirects(response, '/superadmin/')

    def test_super_admin_bloque_detail(self):
        f = self._creer_facture()
        self.client.login(username='super_wf', password='test123')
        response = self.client.get(f'/factures/{f.pk}/')
        self.assertRedirects(response, '/superadmin/')

    def test_super_admin_bloque_ajouter(self):
        self.client.login(username='super_wf', password='test123')
        response = self.client.get('/factures/ajouter/')
        self.assertRedirects(response, '/superadmin/')

    # --- Login required ---
    def test_liste_requires_login(self):
        response = self.client.get('/factures/')
        self.assertNotEqual(response.status_code, 200)

    # --- Workflow: soumettre -> valider -> marquer_paye ---
    def test_soumettre(self):
        f = self._creer_facture('BROUILLON')
        self.client.login(username='agent_wf', password='test123')
        response = self.client.post(f'/factures/{f.pk}/soumettre/', follow=True)
        f.refresh_from_db()
        self.assertEqual(f.statut, 'SOUMIS')

    def test_valider(self):
        f = self._creer_facture('SOUMIS')
        self.client.login(username='compta_wf', password='test123')
        response = self.client.post(f'/factures/{f.pk}/valider/', follow=True)
        f.refresh_from_db()
        self.assertEqual(f.statut, 'VALIDE')

    def test_marquer_paye(self):
        f = self._creer_facture('VALIDE')
        self.client.login(username='compta_wf', password='test123')
        response = self.client.post(f'/factures/{f.pk}/marquer-paye/', follow=True)
        f.refresh_from_db()
        self.assertEqual(f.statut, 'PAYE')

    def test_rejeter(self):
        f = self._creer_facture('SOUMIS')
        self.client.login(username='compta_wf', password='test123')
        response = self.client.post(
            f'/factures/{f.pk}/rejeter/',
            {'motif_rejet': 'Document incomplet'},
            follow=True,
        )
        f.refresh_from_db()
        self.assertEqual(f.statut, 'REJETE')
        self.assertEqual(f.motif_rejet, 'Document incomplet')

    # --- Permission checks ---
    def test_agent_peut_pas_valider(self):
        f = self._creer_facture('SOUMIS')
        self.client.login(username='agent_wf', password='test123')
        response = self.client.post(f'/factures/{f.pk}/valider/', follow=True)
        f.refresh_from_db()
        self.assertEqual(f.statut, 'SOUMIS')

    def test_agent_peut_pas_payer(self):
        f = self._creer_facture('VALIDE')
        self.client.login(username='agent_wf', password='test123')
        response = self.client.post(f'/factures/{f.pk}/marquer-paye/', follow=True)
        f.refresh_from_db()
        self.assertEqual(f.statut, 'VALIDE')

    def test_modifier_bloque_pour_valide(self):
        f = self._creer_facture('VALIDE')
        self.client.login(username='agent_wf', password='test123')
        response = self.client.get(f'/factures/{f.pk}/modifier/')
        self.assertRedirects(response, f'/factures/{f.pk}/')

    def test_supprimer_bloque_pour_valide(self):
        f = self._creer_facture('VALIDE')
        self.client.login(username='agent_wf', password='test123')
        response = self.client.get(f'/factures/{f.pk}/supprimer/')
        self.assertRedirects(response, '/factures/')

    # --- Wrong workflow transitions ---
    def test_soumettre_depuis_valide_impossible(self):
        f = self._creer_facture('VALIDE')
        self.client.login(username='agent_wf', password='test123')
        response = self.client.post(f'/factures/{f.pk}/soumettre/')
        self.assertEqual(response.status_code, 404)

    def test_valider_depuis_brouillon_impossible(self):
        f = self._creer_facture('BROUILLON')
        self.client.login(username='compta_wf', password='test123')
        response = self.client.post(f'/factures/{f.pk}/valider/')
        self.assertEqual(response.status_code, 404)

    def test_rejeter_avec_motif_vide_refuse(self):
        f = self._creer_facture('SOUMIS')
        self.client.login(username='compta_wf', password='test123')
        response = self.client.post(
            f'/factures/{f.pk}/rejeter/',
            {'motif_rejet': ''},
            follow=True,
        )
        f.refresh_from_db()
        self.assertEqual(f.statut, 'SOUMIS')

    # --- Tenant isolation ---
    def test_isolation_autre_mutualite(self):
        other_mut = Mutualite.objects.create(
            nif='4000004002', nom='Autre Mut',
            nom_responsable='Autre', telephone='79123421',
            email='autre@test.com', province='Gitega', commune='Gitega',
        )
        other_part = Partenaire.objects.create(
            mutualite=other_mut, type_partenaire='PHARMACIE',
            nom_etablissement='Pharmacie Autre', created_by=self.admin,
        )
        other_aff = Affilie.objects.create(
            mutualite=other_mut, numero_affiliation='MEM-00021',
            nom='Autre', prenom='User', sexe='F',
            date_naissance=date(1990, 1, 1),
        )
        f_other = Facture.objects.create(
            numero='FAC-202606-0099', mutualite=other_mut,
            date=date(2026, 6, 10), partenaire=other_part,
            affilie=other_aff, cree_par=self.admin,
        )
        self.client.login(username='agent_wf', password='test123')
        response = self.client.get(f'/factures/{f_other.pk}/')
        self.assertEqual(response.status_code, 404)

    # --- Liste and journal ---
    def test_liste_filtre_par_statut(self):
        self._creer_facture('BROUILLON')
        f2 = self._creer_facture('VALIDE')
        self.client.login(username='agent_wf', password='test123')
        response = self.client.get('/factures/?statut=VALIDE')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f2.numero)

    def test_liste_recherche_par_numero(self):
        f = self._creer_facture('BROUILLON')
        self.client.login(username='agent_wf', password='test123')
        response = self.client.get(f'/factures/?q={f.numero[:10]}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f.numero)

    def test_journal_affiche_valide_uniquement(self):
        self._creer_facture('BROUILLON')
        f2 = self._creer_facture('VALIDE')
        self.client.login(username='agent_wf', password='test123')
        response = self.client.get('/factures/journal/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f2.numero)

    # --- Ajouter ---
    def test_ajouter_view_get(self):
        self.client.login(username='agent_wf', password='test123')
        response = self.client.get('/factures/ajouter/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'factures/form.html')

    def test_ajouter_view_post(self):
        self.client.login(username='agent_wf', password='test123')
        data = {
            'numero': Facture.generer_numero(),
            'date': '2026-06-10',
            'partenaire': self.partenaire.pk,
            'affilie': self.affilie.pk,
            'statut': 'BROUILLON',
            'lignes-TOTAL_FORMS': '1',
            'lignes-INITIAL_FORMS': '0',
            'lignes-MIN_NUM_FORMS': '0',
            'lignes-MAX_NUM_FORMS': '1000',
            'lignes-0-service': self.service.pk,
            'lignes-0-designation': 'Analyse',
            'lignes-0-quantite': '2',
            'lignes-0-prix_unitaire': '5000',
            'lignes-0-taux_applique': '80',
        }
        response = self.client.post('/factures/ajouter/', data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Facture.objects.count(), 1)
        facture = Facture.objects.first()
        self.assertEqual(facture.mutualite, self.mutualite)
        self.assertEqual(facture.cree_par, self.agent)
        self.assertEqual(facture.lignes.count(), 1)
        ligne = facture.lignes.first()
        self.assertEqual(ligne.quantite, 2)
        self.assertEqual(ligne.prix_unitaire, 5000)
        self.assertEqual(ligne.taux_applique, 80)
        self.assertEqual(ligne.total_ligne, 10000)
        facture.refresh_from_db()
        self.assertEqual(facture.montant_total, 10000)
        self.assertEqual(facture.montant_mutualite, 8000)
        self.assertEqual(facture.montant_ticket_moderateur, 2000)
