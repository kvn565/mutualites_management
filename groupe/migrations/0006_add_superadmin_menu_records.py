from django.db import migrations


def add_superadmin_menus(apps, schema_editor):
    Menu = apps.get_model('groupe', 'Menu')
    menus = [
        # Mutualite : messages et docs dans OUTILS
        ('Mes messages', 'aide:message_list', 'bi-chat-left-text-fill', 'OUTILS', 175),
        ('Documents officiels', 'aide:doc_superadmin_list', 'bi-file-earmark-text-fill', 'OUTILS', 176),
        ('Écrire au SuperAdmin', 'aide:message_create', 'bi-envelope-plus-fill', 'OUTILS', 177),
        # SuperAdmin : gestion messages et documents dans SUPERADMIN
        ('Messages mutualités', 'aide:superadmin_message_list', 'bi-chat-dots-fill', 'SUPERADMIN', 200),
        ('Documents plateforme', 'aide:superadmin_document_list', 'bi-file-earmark-richtext-fill', 'SUPERADMIN', 210),
        ('Nouveau document', 'aide:superadmin_document_create', 'bi-file-plus-fill', 'SUPERADMIN', 220),
    ]
    for nom, url_name, icone, categorie, ordre in menus:
        Menu.objects.get_or_create(
            url_name=url_name,
            defaults=dict(nom=nom, icone=icone, categorie=categorie, ordre=ordre),
        )


def remove_superadmin_menus(apps, schema_editor):
    Menu = apps.get_model('groupe', 'Menu')
    url_names = [
        'aide:message_list',
        'aide:doc_superadmin_list',
        'aide:message_create',
        'aide:superadmin_message_list',
        'aide:superadmin_document_list',
        'aide:superadmin_document_create',
    ]
    Menu.objects.filter(url_name__in=url_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('groupe', '0005_groupe_deleted_at_groupe_deleted_by_and_more'),
    ]

    operations = [
        migrations.RunPython(add_superadmin_menus, remove_superadmin_menus),
    ]
