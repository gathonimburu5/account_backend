from rest_framework.permissions import BasePermission

class HasPermission(BasePermission):

    def has_permission(self, request, view):
        permission_code = getattr(view, "permission_code", None)
        permission_codes = getattr(view, "permission_codes", None)
        if permission_code:
            return request.user.has_permission(permission_code)
        if permission_codes:
            return request.user.has_any_permission(permission_codes)
        return False