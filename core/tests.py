from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UtilisateurModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Jean',
            last_name='Dupont',
            role='AGENT',
        )

    def test_nom_complet(self):
        self.assertEqual(self.user.nom_complet, 'Dupont Jean')

    def test_initiales(self):
        self.assertEqual(self.user.initiales, 'JD')

    def test_est_agent(self):
        self.assertTrue(self.user.est_agent)

    def test_est_admin_false(self):
        self.assertFalse(self.user.est_admin)

    def test_est_comptable_false(self):
        self.assertFalse(self.user.est_comptable)

    def test_peut_modifier_true(self):
        self.assertTrue(self.user.peut_modifier)

    def test_peut_supprimer_false(self):
        self.assertFalse(self.user.peut_supprimer)

    def test_super_admin_has_all_perms(self):
        admin = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')
        self.assertTrue(admin.est_super_admin)
        self.assertTrue(admin.est_admin)
        self.assertTrue(admin.est_comptable)
        self.assertTrue(admin.peut_modifier)
        self.assertTrue(admin.peut_supprimer)

    def test_consultation_peut_pas_modifier(self):
        consult = User.objects.create_user(
            username='consult', password='testpass',
            role='CONSULTATION'
        )
        self.assertFalse(consult.peut_modifier)
        self.assertFalse(consult.peut_supprimer)


class JournalAuditModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='audituser', password='testpass',
            role='AGENT'
        )

    def test_create_audit_log(self):
        from core.models import JournalAudit
        log = JournalAudit.objects.create(
            utilisateur=self.user,
            action='CREATION',
            module='affilies',
            description='Test audit',
            objet_type='Affilie',
            objet_id=1,
            adresse_ip='127.0.0.1',
        )
        self.assertEqual(str(log), 'Création — affilies — ' + log.date_action.strftime('%d/%m/%Y %H:%M'))
        self.assertEqual(JournalAudit.objects.count(), 1)


class HistoriqueConnexionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='connuser', password='testpass'
        )

    def test_terminer_session(self):
        from core.models import HistoriqueConnexion
        h = HistoriqueConnexion.objects.create(
            utilisateur=self.user,
            adresse_ip='127.0.0.1',
            user_agent='TestAgent',
        )
        self.assertIsNone(h.date_deconnexion)
        h.terminer_session()
        self.assertIsNotNone(h.date_deconnexion)


class MutualiteModelTest(TestCase):
    def test_create_mutualite(self):
        from core.models import Mutualite
        m = Mutualite.objects.create(nom='Mutuelle ABC', nif='1234567890')
        self.assertIn('Mutuelle ABC', str(m))
        self.assertEqual(m.nif, '1234567890')

    def test_mutualite_slug_auto(self):
        from core.models import Mutualite
        m = Mutualite.objects.create(nom='Ma Mutualité')
        self.assertTrue(m.slug.startswith('ma-mutualite'))

class InscriptionViewTest(TestCase):
    def test_inscription_get(self):
        response = self.client.get('/connexion/inscription/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/inscription.html')

    def test_inscription_post_success(self):
        from core.models import Mutualite
        data = {
            'nom_mutualite': 'Mutuelle Test',
            'sigle': 'MT',
            'prenom_admin': 'Admin',
            'nom_admin': 'Test',
            'email_admin': 'admin@test.com',
            'username': 'admin_test',
            'password': 'Test1234!',
            'confirm_password': 'Test1234!',
        }
        response = self.client.post('/connexion/inscription/', data)
        self.assertRedirects(response, '/connexion/')
        self.assertEqual(Mutualite.objects.count(), 1)
        self.assertEqual(Mutualite.objects.first().nom, 'Mutuelle Test')

    def test_inscription_password_mismatch(self):
        data = {
            'nom_mutualite': 'Mutuelle Test',
            'prenom_admin': 'Admin',
            'nom_admin': 'Test',
            'email_admin': 'admin@test.com',
            'username': 'admin_test',
            'password': 'Test1234!',
            'confirm_password': 'Different!',
        }
        response = self.client.post('/connexion/inscription/', data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ne correspondent pas')

    def test_mutualite_slug_unique(self):
        from core.models import Mutualite
        m1 = Mutualite.objects.create(nom='Test')
        m2 = Mutualite.objects.create(nom='Test')
        self.assertNotEqual(m1.slug, m2.slug)
