from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.core import database_connection
from app.models.product_model import ProductModel
from app.schemas.product_schema import ProductCreate, ProductUpdate




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
    
    def get_product_by_id(self, product_id: int):
        product = self.db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    
    def update_product(self, product_id: int, product: ProductUpdate):
        db_product = self.get_product_by_id(product_id)
        for key, value in product.model_dump().items():
            setattr(db_product, key, value)
        
        try:
            self.db.add(db_product)
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to update product: {str(e)}")
        
        self.db.refresh(db_product)
        return db_product
                    