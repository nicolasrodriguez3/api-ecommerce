from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "admin"
    OWNER = "owner"
    SELLER = "seller"
    CUSTOMER = "customer"