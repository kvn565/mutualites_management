from single_tenant.views import get_active_mutualite


class SingleTenantMiddleware:
    """Middleware pour le mode single-tenant : injecte la mutualité unique si configurée."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        mutualite = get_active_mutualite()
        if mutualite:
            from core.models import set_current_mutualite
            set_current_mutualite(mutualite)
            request.current_mutualite = mutualite
            response = self.get_response(request)
            set_current_mutualite(None)
            return response
        return self.get_response(request)
