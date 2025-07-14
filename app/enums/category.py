from enum import Enum


class CategoryOrderField(str, Enum):
    ID = "id"
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"