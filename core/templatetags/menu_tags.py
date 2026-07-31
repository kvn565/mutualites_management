import re
from django import template
from django.apps import apps

register = template.Library()


@register.filter
def video_embed_url(value):
    if not value:
        return ''
    match = re.search(r'youtube\.com/watch\?v=([\w-]+)', value)
    if match:
        return f'https://www.youtube.com/embed/{match.group(1)}'
    match = re.search(r'youtu\.be/([\w-]+)', value)
    if match:
        return f'https://www.youtube.com/embed/{match.group(1)}'
    match = re.search(r'vimeo\.com/(\d+)', value)
    if match:
        return f'https://player.vimeo.com/video/{match.group(1)}'
    return value


@register.simple_tag(takes_context=True)
def menu_autorise(context, url_name):
    menus = context.get('menus_autorises', None)
    if menus is None:
        return True
    return url_name in menus


@register.simple_tag(takes_context=True)
def section_autorise(context, *url_names):
    menus = context.get('menus_autorises', None)
    if menus is None:
        return True
    return any(url in menus for url in url_names)


@register.inclusion_tag('groupe/sidebar_menu.html', takes_context=True)
def render_sidebar_menu(context):
    """Render sidebar menu dynamically from Menu model."""
    request = context.get('request')
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return {'menus_by_categorie': []}

    user = request.user
    mutualite = getattr(user, 'mutualite', None)

    # Get user's authorized menus
    menus_autorises = user.menus_autorises

    # Get all active menus ordered by categorie and ordre
    Menu = apps.get_model('groupe', 'Menu')
    menus_qs = Menu.objects.filter(actif=True).order_by('categorie', 'ordre')

    # Filter by user's permissions
    if not (user.est_admin or user.est_super_admin):
        menus_qs = menus_qs.filter(url_name__in=menus_autorises)

    # Group by category
    menus_by_categorie = {}
    for menu in menus_qs:
        if menu.categorie not in menus_by_categorie:
            menus_by_categorie[menu.categorie] = []
        menus_by_categorie[menu.categorie].append(menu)

    # Define category order and labels
    category_order = [
        ('PRINCIPAL', 'Principal'),
        ('MEMBRES', 'Membres'),
        ('SANTE', 'Santé'),
        ('FACTURATION', 'Facturation'),
        ('COTISATIONS', 'Cotisations'),
        ('FINANCE', 'Finance & Comptabilité'),
        ('ADMIN', 'Administration'),
        ('OUTILS', 'Outils'),
        ('SUPERADMIN', 'Super Admin'),
    ]

    ordered_categories = []
    for cat_key, cat_label in category_order:
        if cat_key in menus_by_categorie:
            ordered_categories.append({
                'key': cat_key,
                'label': cat_label,
                'menus': menus_by_categorie[cat_key]
            })

    return {
        'ordered_categories': ordered_categories,
        'user': user,
        'mutualite': mutualite,
    }