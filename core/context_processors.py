from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from core.models import ConfigurationApp


def menus_context(request):
    if request.user.is_authenticated:
        return {'menus_autorises': request.user.menus_autorises}
    return {'menus_autorises': set()}


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
            'licence_15j': False,
        }

    ctx = {
        'mutualite': mutualite,
        'NOM_MUTUALITE': mutualite.nom,
        'DEVISE': getattr(mutualite, 'devise', settings.MUTUALITE_DEVISE),
        'MUTUALITE_PRIMARY_COLOR': getattr(mutualite, 'primary_color', '#0a5c36'),
        'MUTUALITE_ACCENT_COLOR': getattr(mutualite, 'accent_color', '#c9a84c'),
        'MUTUALITE_BACKGROUND_COLOR': getattr(mutualite, 'background_color', '#f0f4f8'),
        'MUTUALITE_BACKGROUND_IMAGE_URL': mutualite.background_image.url if mutualite.background_image else '',
        'MUTUALITE_BACKGROUND_OPACITY': str(float(mutualite.background_opacity)),
        'MUTUALITE_BACKGROUND_BRIGHTNESS': str(float(mutualite.background_brightness)),
        'MUTUALITE_TEXT_COLOR': getattr(mutualite, 'text_color', '#1e293b'),
    }

    # ── Notification licence expirant dans 15 jours ──
    ctx['licence_15j'] = False
    if mutualite and request.user.is_authenticated and not getattr(request.user, 'est_super_admin', False):
        jours = mutualite.jours_restants
        if 1 <= jours <= 15:
            dismissed = request.session.get('licence_notif_dismissed')
            if not dismissed:
                ctx['licence_15j'] = jours
            else:
                try:
                    dt = datetime.fromisoformat(dismissed)
                    if dt.tzinfo is None:
                        dt = timezone.make_aware(dt)
                    if (timezone.now() - dt) > timedelta(hours=24):
                        ctx['licence_15j'] = jours
                except (ValueError, TypeError):
                    ctx['licence_15j'] = jours

    return ctx


def app_config(request):
    config = ConfigurationApp.get_config()
    return {
        'APP_NOM': config.nom_app,
        'APP_LOGO': config.logo_app,
        'APP_FAVICON': config.favicon,
        'APP_PRIMARY_COLOR': config.primary_color,
        'APP_ACCENT_COLOR': config.accent_color,
        'APP_BACKGROUND_COLOR': config.background_color,
        'APP_BACKGROUND_IMAGE_URL': config.background_image.url if config.background_image else '',
        'APP_BACKGROUND_OPACITY': str(float(config.background_opacity)),
        'APP_BACKGROUND_BRIGHTNESS': str(float(config.background_brightness)),
        'APP_TEXT_COLOR': config.text_color,
    }


def notifications_portail(request):
    """Notifications pour le portail partenaire."""
    ctx = {
        'notifications': [],
        'nb_notifications': 0,
    }

    # Vérifier si on est sur le portail partenaire
    partenaire_user_id = request.session.get('partenaire_user_id')
    if not partenaire_user_id:
        return ctx

    from partenaires.models import UtilisateurPartenaire
    try:
        user = UtilisateurPartenaire.objects.get(pk=partenaire_user_id, actif=True)
    except UtilisateurPartenaire.DoesNotExist:
        return ctx

    partenaire = user.partenaire
    mutualite_id = request.session.get('mutualite_active_pk')

    # Couleurs de la mutualité active (pour le thème du portail)
    from core.models import Mutualite
    from core.models import ConfigurationApp
    try:
        config = ConfigurationApp.objects.first()
        default_primary = config.primary_color if config else '#0a5c36'
        default_accent = config.accent_color if config else '#c9a84c'
        default_bg = config.background_color if config else '#f0f4f8'
        default_bg_img = config.background_image.url if config and config.background_image else ''
        default_bg_opacity = float(config.background_opacity) if config else 0.25
        default_bg_brightness = float(config.background_brightness) if config else 0.40
    except Exception:
        default_primary, default_accent, default_bg = '#0a5c36', '#c9a84c', '#f0f4f8'
        default_bg_img = ''
        default_bg_opacity = 0.25
        default_bg_brightness = 0.40

    active_mutualite = None
    if mutualite_id:
        try:
            active_mutualite = Mutualite.objects.get(pk=mutualite_id)
        except Mutualite.DoesNotExist:
            pass
    if active_mutualite:
        ctx['MUTUALITE_PRIMARY_COLOR'] = getattr(active_mutualite, 'primary_color', None) or default_primary
        ctx['MUTUALITE_ACCENT_COLOR'] = getattr(active_mutualite, 'accent_color', None) or default_accent
        ctx['MUTUALITE_BACKGROUND_COLOR'] = getattr(active_mutualite, 'background_color', None) or default_bg
        ctx['MUTUALITE_BACKGROUND_IMAGE_URL'] = active_mutualite.background_image.url if active_mutualite.background_image else default_bg_img
        ctx['MUTUALITE_BACKGROUND_OPACITY'] = float(active_mutualite.background_opacity)
        ctx['MUTUALITE_BACKGROUND_BRIGHTNESS'] = float(active_mutualite.background_brightness)
        ctx['MUTUALITE_TEXT_COLOR'] = getattr(active_mutualite, 'text_color', None) or '#1e293b'
    else:
        ctx['MUTUALITE_PRIMARY_COLOR'] = default_primary
        ctx['MUTUALITE_ACCENT_COLOR'] = default_accent
        ctx['MUTUALITE_BACKGROUND_COLOR'] = default_bg
        ctx['MUTUALITE_BACKGROUND_IMAGE_URL'] = default_bg_img
        ctx['MUTUALITE_BACKGROUND_OPACITY'] = default_bg_opacity
        ctx['MUTUALITE_BACKGROUND_BRIGHTNESS'] = default_bg_brightness
        ctx['MUTUALITE_TEXT_COLOR'] = '#1e293b'

    # Partenaire theme colors (fallback to mutualite or app config)
    ctx['PARTENAIRE_PRIMARY_COLOR'] = getattr(partenaire, 'primary_color', None) or ctx['MUTUALITE_PRIMARY_COLOR']
    ctx['PARTENAIRE_ACCENT_COLOR'] = getattr(partenaire, 'accent_color', None) or ctx['MUTUALITE_ACCENT_COLOR']
    ctx['PARTENAIRE_BACKGROUND_COLOR'] = getattr(partenaire, 'background_color', None) or ctx['MUTUALITE_BACKGROUND_COLOR']
    ctx['PARTENAIRE_TEXT_COLOR'] = getattr(partenaire, 'text_color', None) or ctx['MUTUALITE_TEXT_COLOR']
    ctx['PARTENAIRE_BACKGROUND_IMAGE_URL'] = partenaire.background_image.url if partenaire.background_image else ctx['MUTUALITE_BACKGROUND_IMAGE_URL']
    ctx['PARTENAIRE_BACKGROUND_OPACITY'] = float(getattr(partenaire, 'background_opacity', None) or ctx['MUTUALITE_BACKGROUND_OPACITY'])
    ctx['PARTENAIRE_BACKGROUND_BRIGHTNESS'] = float(getattr(partenaire, 'background_brightness', None) or ctx['MUTUALITE_BACKGROUND_BRIGHTNESS'])

    mutualite_ids = list(partenaire.mutualites_liees.values_list('pk', flat=True))
    if mutualite_id:
        try:
            mutualite_ids = [int(mutualite_id)]
        except (ValueError, TypeError):
            pass

    if not mutualite_ids:
        return ctx

    dismissed = set(request.session.get('notifications_dismissed', []))

    # ── Nouveaux affiliés enregistrés ──
    from affilies.models import Affilie
    nouveaux_affilies = Affilie.objects.filter(
        mutualite__in=mutualite_ids, supprime=False,
    ).select_related('mutualite').order_by('-date_creation')[:5]

    for a in nouveaux_affilies:
        key = f"affilie_{a.pk}"
        if key not in dismissed:
            ctx['notifications'].append({
                'key': key,
                'icone': 'bi-person-plus',
                'couleur': '#10b981',
                'message': f"Nouvel affilié : {a.nom_complet} ({a.numero_affiliation})",
                'url': f"/portail/membres/{a.pk}/",
                'date': a.date_creation,
            })

    # ── Nouvelles cotisations payées ──
    from cotisations.models import Cotisation
    nouvelles_cotisations = Cotisation.objects.filter(
        mutualite__in=mutualite_ids, statut='PAYE',
    ).select_related('affilie').order_by('-date_creation')[:5]

    for c in nouvelles_cotisations:
        key = f"cotisation_{c.pk}"
        if key not in dismissed:
            ctx['notifications'].append({
                'key': key,
                'icone': 'bi-cash-stack',
                'couleur': '#3b82f6',
                'message': f"Cotisation {c.reference} - {c.montant} BIF - {c.affilie.nom_complet}",
                'url': f"/portail/membres/{c.affilie.pk}/",
                'date': c.date_creation,
            })

    # ── Nouveaux ayants droit ajoutés ──
    from ayants_droit.models import AyantDroit
    nouveaux_ayants_droit = AyantDroit.objects.filter(
        mutualite__in=mutualite_ids, supprime=False,
    ).select_related('affilie').order_by('-date_creation')[:5]

    for ad in nouveaux_ayants_droit:
        key = f"ayantdroit_{ad.pk}"
        if key not in dismissed:
            ctx['notifications'].append({
                'key': key,
                'icone': 'bi-people',
                'couleur': '#8b5cf6',
                'message': f"Nouvel ayant droit : {ad.nom_complet} ({ad.get_lien_parente_display()}) - {ad.affilie.nom_complet}",
                'url': f"/portail/membres/{ad.affilie.pk}/",
                'date': ad.date_creation,
            })

    # ── Exclusion individuelle (1 affilié spécifique) ──
    from affilies.models import AffilieExclusion
    exclusions_affilie = AffilieExclusion.objects.filter(
        mutualite__in=mutualite_ids,
    ).select_related('medicament', 'service', 'affilie').order_by('-date_creation')[:5]

    for e in exclusions_affilie:
        key = f"affilie_exclusion_{e.pk}"
        if key not in dismissed:
            nom = e.medicament.nom if e.medicament else e.service.nom
            type_excl = 'médicament' if e.medicament else 'service'
            ctx['notifications'].append({
                'key': key,
                'icone': 'bi-person-x',
                'couleur': '#dc2626',
                'message': f"Exclusion individuelle ({type_excl}) : {nom} - {e.affilie.nom_complet}",
                'url': f"/portail/membres/{e.affilie.pk}/",
                'date': e.date_creation,
            })

    # ── Exclusion globale (tous les affiliés de la mutualité, tous partenaires) ──
    from core.models import MutualiteExclusion
    exclusions_globales = MutualiteExclusion.objects.filter(
        mutualite__in=mutualite_ids,
    ).select_related('medicament', 'service').order_by('-date_creation')[:5]

    for e in exclusions_globales:
        key = f"mutualite_exclusion_{e.pk}"
        if key not in dismissed:
            nom = e.medicament.nom if e.medicament else e.service.nom
            type_excl = 'médicament' if e.medicament else 'service'
            ctx['notifications'].append({
                'key': key,
                'icone': 'bi-shield-exclamation',
                'couleur': '#dc2626',
                'message': f"Exclusion globale ({type_excl}) : {nom} - Tous les affiliés",
                'url': f"/portail/",
                'date': e.date_creation,
            })

    # ── Exclusion par groupe d'origine ──
    from origines.models import OrigineExclusion
    exclusions_origine = OrigineExclusion.objects.filter(
        mutualite__in=mutualite_ids,
    ).select_related('medicament', 'service', 'origine').order_by('-date_creation')[:5]

    for e in exclusions_origine:
        key = f"origine_exclusion_{e.pk}"
        if key not in dismissed:
            nom = e.medicament.nom if e.medicament else e.service.nom
            type_excl = 'médicament' if e.medicament else 'service'
            ctx['notifications'].append({
                'key': key,
                'icone': 'bi-people',
                'couleur': '#dc2626',
                'message': f"Exclusion groupe ({e.origine.nom}) ({type_excl}) : {nom}",
                'url': f"/portail/",
                'date': e.date_creation,
            })

    # Trier par date (plus récentes d'abord)
    ctx['notifications'].sort(key=lambda n: n['date'], reverse=True)
    ctx['nb_notifications'] = len(ctx['notifications'])

    return ctx


def notification_plafond_context(request):
    """Badge de notifications plafond pour la mutualité."""
    ctx = {'nb_notifications_plafond': 0, 'notifications_plafond_recents': []}
    if request.user.is_authenticated:
        mutualite = getattr(request, 'current_mutualite', None) or request.user.mutualite
        if mutualite:
            from core.models import Notification
            qs = Notification.objects.filter(mutualite=mutualite)
            ctx['nb_notifications_plafond'] = qs.filter(vue=False).count()
            ctx['notifications_plafond_recents'] = qs.select_related('affilie').order_by('-date_creation')[:5]
    return ctx


def superadmin_notifications(request):
    ctx = {'superadmin_nb_messages_nouveaux': 0}
    if request.user.is_authenticated and request.user.est_super_admin:
        from aide.models import MessageSuperAdmin
        ctx['superadmin_nb_messages_nouveaux'] = MessageSuperAdmin.objects.filter(statut='NOUVEAU').count()
    return ctx


def superadmin_pending_validations(request):
    """Notifications pour le SuperAdmin : mutualités et partenaires en attente de validation."""
    ctx = {
        'superadmin_nb_mutualites_en_attente': 0,
        'superadmin_nb_partenaires_en_attente': 0,
    }
    if request.user.is_authenticated and request.user.est_super_admin:
        from core.models import Mutualite
        from partenaires.models import Partenaire
        ctx['superadmin_nb_mutualites_en_attente'] = Mutualite.objects.filter(statut='EN_ATTENTE').count()
        ctx['superadmin_nb_partenaires_en_attente'] = Partenaire.objects.filter(statut='EN_ATTENTE').count()
    return ctx
