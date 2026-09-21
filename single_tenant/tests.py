from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from single_tenant.models import SingleTenantConfig
from single_tenant.views import get_active_mutualite, SingleTenantMiddleware

User = get_user_model()


class SingleTenantConfigModelTest(TestCase):
    def test_est_active_property(self):
        config = SingleTenantConfig(statut='ACTIVE')
        self.assertTrue(config.est_active)
        config.statut = 'INACTIVE'
        self.assertFalse(config.est_active)


class GetActiveMutualiteTest(TestCase):
    def test_no_config_returns_none(self):
        self.assertIsNone(get_active_mutualite())


class SingleTenantMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_middleware_sets_current_mutualite(self):
        request = self.factory.get('/')
        request.user = MagicMock(is_authenticated=True, pk=1)

        mock_mutualite = MagicMock(nom='Test', pk=1)
        with patch('single_tenant.views.get_active_mutualite') as mock_config:
            mock_config.return_value = mock_mutualite
            middleware = SingleTenantMiddleware(lambda r: None)
            middleware(request)
            self.assertEqual(request.current_mutualite.nom, 'Test')


class SingleTenantConfigViewTest(TestCase):
    def test_config_view_get(self):
        response = self.client.get('/single-tenant/config/')
        self.assertIn(response.status_code, [200, 302])
