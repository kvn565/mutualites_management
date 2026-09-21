from rest_framework import serializers
from core.models import Mutualite


class MutualiteListSerializer(serializers.ModelSerializer):
    statut_display = serializers.SerializerMethodField()

    class Meta:
        model = Mutualite
        fields = [
            'id', 'code_mutualite', 'nif', 'nom', 'sigle', 'type_mutualite',
            'nom_responsable', 'telephone', 'email',
            'province', 'commune',
            'statut', 'statut_display',
            'essai_gratuit', 'date_debut_essai', 'date_fin_essai',
            'type_abonnement', 'date_activation', 'date_expiration',
            'max_utilisateurs',
            'date_creation',
        ]

    def get_statut_display(self, obj):
        return obj.get_statut_display()


class MutualiteDetailSerializer(serializers.ModelSerializer):
    statut_display = serializers.SerializerMethodField()
    total_utilisateurs = serializers.SerializerMethodField()

    class Meta:
        model = Mutualite
        fields = [
            'id', 'code_mutualite', 'nif', 'nom', 'sigle', 'type_mutualite',
            'nom_responsable', 'fonction_responsable', 'telephone', 'email',
            'province', 'commune', 'adresse',
            'essai_gratuit', 'date_debut_essai', 'date_fin_essai',
            'date_activation', 'date_expiration',
            'type_abonnement', 'max_utilisateurs',
            'statut', 'statut_display',
            'username_admin', 'email_admin',
            'total_utilisateurs',
            'date_creation', 'date_modification',
        ]

    def get_statut_display(self, obj):
        return obj.get_statut_display()

    def get_total_utilisateurs(self, obj):
        return obj.utilisateurs.count()


class MutualiteCreateSerializer(serializers.ModelSerializer):
    password_admin = serializers.CharField(write_only=True, required=False)
    username_admin = serializers.CharField(required=False)
    email_admin = serializers.EmailField(required=False)

    class Meta:
        model = Mutualite
        fields = [
            'nif', 'nom', 'sigle', 'type_mutualite',
            'nom_responsable', 'fonction_responsable',
            'telephone', 'email',
            'province', 'commune', 'adresse',
            'username_admin', 'email_admin', 'password_admin',
            'max_utilisateurs',
            'statut', 'essai_gratuit', 'code_mutualite',
        ]
        read_only_fields = ['statut', 'essai_gratuit', 'code_mutualite']

    def create(self, validated_data):
        import secrets
        from django.contrib.auth import get_user_model
        from django.db import transaction

        User = get_user_model()
        password_admin = validated_data.pop('password_admin', None)
        username_admin = validated_data.pop('username_admin', None)
        email_admin = validated_data.pop('email_admin', None)

        with transaction.atomic():
            mutualite = Mutualite.objects.create(**validated_data)

            admin_username = username_admin or f"admin_{mutualite.code_mutualite.lower()}"
            admin_email = email_admin or validated_data.get('email', '')
            admin_password = password_admin or secrets.token_urlsafe(12)

            User.objects.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                first_name=validated_data.get('nom_responsable', '').split()[0] if validated_data.get('nom_responsable') else '',
                last_name=' '.join(validated_data.get('nom_responsable', '').split()[1:]) if validated_data.get('nom_responsable') else '',
                role='ADMIN_MUTUALITE',
                mutualite=mutualite,
                telephone=validated_data.get('telephone', ''),
                actif=True,
            )

            mutualite.username_admin = admin_username
            mutualite.email_admin = admin_email
            mutualite.activer_essai()

        return mutualite


class DashboardSerializer(serializers.Serializer):
    total_mutualites = serializers.IntegerField()
    mutualites_essai = serializers.IntegerField()
    mutualites_actives = serializers.IntegerField()
    mutualites_suspendues = serializers.IntegerField()
    mutualites_expirees = serializers.IntegerField()
    mutualites_bloquees = serializers.IntegerField()
    total_utilisateurs = serializers.IntegerField()
