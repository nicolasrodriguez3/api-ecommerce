from enum import Enum


class RoleEnum(str, Enum):
    admin = "admin"
    seller = "seller"
    customer = "customer"