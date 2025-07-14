from enum import Enum


class OrderDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"