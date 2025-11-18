from rest_framework import permissions


class IsAuthenticatedReadOnlyOrAdmin(permissions.BasePermission):
    """
    认证用户可读，管理员可写
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff


class IsProfileAdmin(permissions.BasePermission):
    """
    检查用户的 UserProfile.role 是否为 ADMIN
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            from .models import UserProfile
            profile = UserProfile.objects.filter(user=request.user).first()
            return profile and profile.role == UserProfile.RoleChoices.ADMIN
        except Exception:
            return False