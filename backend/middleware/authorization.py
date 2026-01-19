from functools import wraps
from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.auth import UserRole, TokenData
from .auth import get_current_user

security = HTTPBearer()


def require_roles(*roles: UserRole):
    """
    Dependency decorator that requires specific roles.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: TokenData = Depends(require_roles(UserRole.ADMIN))):
            return {"message": "Admin access granted"}
    """
    async def role_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if current_user.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role assignment required"
            )

        if current_user.role not in roles:
            logger = __import__("logging").getLogger(__name__)
            logger.warning(
                f"Access denied: user {current_user.user_id} with role "
                f"{current_user.role} attempted to access resource requiring {roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role(s): {', '.join(r.value for r in roles)}"
            )

        return current_user

    return role_checker


def require_admin():
    """Require admin role."""
    return require_roles(UserRole.ADMIN)


def require_analyst_or_admin():
    """Require analyst or admin role."""
    return require_roles(UserRole.ANALYST, UserRole.ADMIN)


class Permission:
    """Permission definitions."""

    @staticmethod
    def can_view_documents(roles: List[UserRole]) -> bool:
        """Check if role can view documents."""
        return UserRole.VIEWER in roles or UserRole.ANALYST in roles or UserRole.ADMIN in roles

    @staticmethod
    def can_upload_documents(roles: List[UserRole]) -> bool:
        """Check if role can upload documents."""
        return UserRole.ANALYST in roles or UserRole.ADMIN in roles

    @staticmethod
    def can_delete_documents(roles: List[UserRole]) -> bool:
        """Check if role can delete documents."""
        return UserRole.ADMIN in roles

    @staticmethod
    def can_manage_users(roles: List[UserRole]) -> bool:
        """Check if role can manage users."""
        return UserRole.ADMIN in roles

    @staticmethod
    def can_view_analytics(roles: List[UserRole]) -> bool:
        """Check if role can view analytics."""
        return UserRole.ANALYST in roles or UserRole.ADMIN in roles

    @staticmethod
    def can_export_data(roles: List[UserRole]) -> bool:
        """Check if role can export data."""
        return UserRole.ANALYST in roles or UserRole.ADMIN in roles


async def check_document_permission(
    document_owner_id: str,
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Check if user has permission to access a document."""
    if current_user.role == UserRole.ADMIN:
        return current_user

    if current_user.role in [UserRole.VIEWER, UserRole.ANALYST]:
        if current_user.user_id == document_owner_id:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document"
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions"
    )


def document_action_allowed(
    action: str,
    roles: List[UserRole]
) -> bool:
    """Check if an action is allowed for the given roles."""
    action_permissions = {
        "view": Permission.can_view_documents,
        "upload": Permission.can_upload_documents,
        "delete": Permission.can_delete_documents,
        "analytics": Permission.can_view_analytics,
        "export": Permission.can_export_data,
    }

    check_func = action_permissions.get(action)
    if check_func:
        return check_func(roles)
    return False


class RoleHierarchy:
    """Define role hierarchy for inheritance."""

    HIERARCHY = {
        UserRole.ADMIN: [UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER],
        UserRole.ANALYST: [UserRole.ANALYST, UserRole.VIEWER],
        UserRole.VIEWER: [UserRole.VIEWER],
    }

    @classmethod
    def has_permission(cls, user_role: UserRole, required_role: UserRole) -> bool:
        """Check if user role has the required permission level."""
        allowed_roles = cls.HIERARCHY.get(user_role, [])
        return required_role in allowed_roles

    @classmethod
    def get_effective_permissions(cls, role: UserRole) -> List[str]:
        """Get all permissions for a role."""
        hierarchy = {
            UserRole.ADMIN: ["view", "upload", "delete", "analytics", "export", "manage_users"],
            UserRole.ANALYST: ["view", "upload", "analytics", "export"],
            UserRole.VIEWER: ["view"],
        }
        return hierarchy.get(role, [])
