import enum

from app.services.permission_service import ROLE_PERMISSIONS, Permission, Role


def check_perm(user_role, permission):
    perms = ROLE_PERMISSIONS.get(user_role, set())
    print(f"Role: {user_role}, Perm: {permission}, In perms? {permission in perms}")


# We need to know if the permission check uses the value or the name.
# It uses the passed string. Permission.MANAGE_SYSTEM is "manage_system".
# But ROLE_PERMISSIONS for super_admin has "MANAGE_SYSTEM".
# So a check for "manage_system" will fail for super_admin!

check_perm("super_admin", "manage_system")
check_perm("super_admin", "MANAGE_SYSTEM")
check_perm("admin", "manage_system")
