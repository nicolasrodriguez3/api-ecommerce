from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.core import database_connection
from app.models.product_model import ProductModel
from app.schemas.product_schema import ProductCreate




class ProductService:
    def __init__(self):
        self.db = database_connection.session

    def create_product(self, product: ProductCreate):
        new_product = ProductModel(
            name = product.name,
            description = product.description,
            price = product.price,
            stock = product.stock,
        )
        self.db.add(new_product)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Failed to create product")
        
        self.db.refresh(new_product)
        return new_product
    
    
    def get_products(self, limit, offset):
        products = self.db.query(ProductModel).limit(limit).offset(offset).all()
        return products