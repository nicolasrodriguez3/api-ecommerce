from enum import Enum


class ProductOrderField(str, Enum):
    ID = "id"
    NAME = "name"
    PRICE = "price"
    STOCK = "stock"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
