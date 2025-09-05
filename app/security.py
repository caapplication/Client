from fastapi import Depends, HTTPException, status
from .dependencies import get_current_user
from enum import Enum

class Role(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    AGENCY_ADMIN = "AGENCY_ADMIN"
    CA_ACCOUNTANT = "CA_ACCOUNTANT"
    CA_TEAM = "CA_TEAM"
    CLIENT_ADMIN = "CLIENT_ADMIN"
    CLIENT_USER = "CLIENT_USER"

def has_role(required_roles: list[Role]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in [role.value for role in required_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action.",
            )
    return role_checker
