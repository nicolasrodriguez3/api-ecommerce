from enum import Enum


class RoleEnum(str, Enum):
    """Enumeration for user roles in the application."""
    ADMIN = "admin"
    OWNER = "owner"
    SELLER = "seller"
    CUSTOMER = "customer"