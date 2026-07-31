from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Chambre, Hospitalisation, MouvementChambre


@receiver(pre_save, sender=Chambre)
def chambre_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Chambre.objects.get(pk=instance.pk)
            instance._old_statut = old.statut
        except Chambre.DoesNotExist:
            instance._old_statut = None
    else:
        instance._old_statut = None


@receiver(post_save, sender=Chambre)
def chambre_post_save(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_old_statut') and instance._old_statut != instance.statut:
        MouvementChambre.objects.create(
            mutualite=instance.mutualite,
            chambre=instance,
            type_mouvement='CHANGEMENT_STATUT',
            ancien_statut=instance._old_statut,
            nouveau_statut=instance.statut,
            commentaire=f"Statut changé de {instance._old_statut} à {instance.statut}"
        )


@receiver(post_save, sender=Hospitalisation)
def hospitalisation_post_save(sender, instance, created, **kwargs):
    if created:
        # Créer un mouvement d'entrée
        MouvementChambre.objects.create(
            mutualite=instance.mutualite,
            chambre=instance.chambre,
            hospitalisation=instance,
            type_mouvement='ENTREE',
            ancien_statut='LIBRE',
            nouveau_statut='OCCUPEE',
            commentaire=f"Admission de {instance.patient_nom} {instance.patient_prenom}"
        )