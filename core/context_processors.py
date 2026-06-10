from django.conf import settings


def mutualite_context(request):
    """Variables globales disponibles dans tous les templates."""
    mutualite = getattr(request, 'current_mutualite', None)
    if mutualite is None and request.user.is_authenticated:
        mutualite = request.user.mutualite
    if mutualite is None:
        return {
            'mutualite': None,
            'NOM_MUTUALITE': settings.MUTUALITE_NOM,
            'DEVISE': settings.MUTUALITE_DEVISE,
        }
    return {
        'mutualite': mutualite,
        'NOM_MUTUALITE': mutualite.nom,
        'DEVISE': getattr(mutualite, 'devise', settings.MUTUALITE_DEVISE),
    }
