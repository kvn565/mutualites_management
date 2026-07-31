from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Mutualite
from groupe.models import Groupe, Menu


@receiver(post_save, sender=Mutualite)
def create_default_groups(sender, instance, created, **kwargs):
    """Create default groups with menu assignments when a new mutualité is created."""
    if not created:
        return

    all_menus = Menu.objects.filter(actif=True)

    # Admin group - all menus
    admin_group = Groupe.objects.create(nom='Administrateurs', mutualite=instance)
    admin_group.menus.set(all_menus)

    # Comptables group - finance, facturation, cotisations, principal
    comptable_menus = all_menus.filter(categorie__in=['FINANCE', 'FACTURATION', 'COTISATIONS', 'PRINCIPAL'])
    comptable_group = Groupe.objects.create(nom='Comptables', mutualite=instance)
    comptable_group.menus.set(comptable_menus)

    # Agents group - principal, membres, sante, facturation, cotisations
    agent_menus = all_menus.filter(categorie__in=['PRINCIPAL', 'MEMBRES', 'SANTE', 'FACTURATION', 'COTISATIONS'])
    agent_group = Groupe.objects.create(nom='Agents', mutualite=instance)
    agent_group.menus.set(agent_menus)

    # Consultation group - only principal
    consultation_menus = all_menus.filter(categorie='PRINCIPAL')
    consultation_group = Groupe.objects.create(nom='Consultation seule', mutualite=instance)
    consultation_group.menus.set(consultation_menus)