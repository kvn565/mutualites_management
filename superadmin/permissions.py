from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """
    Permet l'accès uniquement aux super administrateurs.
    """

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.est_super_admin
        )


class IsMutualiteAdmin(BasePermission):
    """
    Permet l'accès uniquement à l'administrateur de la mutualité concernée.
    """

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN_MUTUALITE'
        )

    def has_object_permission(self, request, view, obj):
        return obj == request.user.mutualite
