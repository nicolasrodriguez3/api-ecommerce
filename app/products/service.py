import os
import shutil
import tempfile
from typing import List
import uuid
from fastapi import File, UploadFile
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from app.categories.models import Category
from app.core.cloudinary import upload_image as upload_image_service
from app.core.exceptions import BadRequestException, NotFoundException
from app.products.models import Product, ProductImage, StockHistory
from app.products.schemas import ProductCreate, ProductImageResponse
from app.products.schemas import ProductPublicResponse


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    order_by: str = "id",
    order_dir: str = "asc",
) -> tuple[List[ProductPublicResponse], int, int]:
    query = (
        db.query(Product)
        .filter(Product.is_active.is_(True))
        .options(joinedload(Product.category))
        .options(joinedload(Product.images))
    )

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    ALLOWED_ORDER_FIELDS = {"id", "name", "price", "stock", "created_at"}
    if order_by not in ALLOWED_ORDER_FIELDS:
        raise BadRequestException(
            f"Invalid order_by field. Allowed fields are: {', '.join(ALLOWED_ORDER_FIELDS)}"
        )

    column = getattr(Product, order_by)
    query = query.order_by(desc(column) if order_dir.lower() == "desc" else asc(column))

    products: List[Product] = query.offset(skip).limit(limit).all()
    total: int = query.count()
    total_pages: int = total // limit + (1 if total % limit > 0 else 0)
    page: int = skip // limit + 1

    result = [ProductPublicResponse.model_validate(p) for p in products]
    return result, page, total_pages


def get_by_id(db: Session, product_id: int) -> ProductPublicResponse:
    product = _get_one_product(db, product_id)

    return ProductPublicResponse.model_validate(product)


def create(product_data: ProductCreate, db: Session) -> ProductPublicResponse:
    _get_category_or_400(db, product_data.category_id)

    new_product = Product(**product_data.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    product_with_category = (
        db.query(Product).options(joinedload(Product.category)).get(new_product.id)
    )

    return ProductPublicResponse.model_validate(product_with_category)


def update(
    product_id: int, product_data: ProductCreate, db: Session
) -> ProductPublicResponse:
    product = _get_one_product(db, product_id)

    # Validar categoría
    _get_category_or_400(db, product_data.category_id)

    for key, value in product_data.model_dump().items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    product_with_category = (
        db.query(Product).options(joinedload(Product.category)).get(product.id)
    )

    return ProductPublicResponse.model_validate(product_with_category)


def delete(product_id: int, db: Session) -> None:
    product = _get_one_product(db, product_id)

    product.is_active = False
    db.commit()


def restore(product_id: int, db: Session) -> ProductPublicResponse:
    product = _get_one_product(db, product_id, include_inactives=True)

    product.is_active = True
    db.commit()
    db.refresh(product)

    return ProductPublicResponse.model_validate(product)


def update_stock(db: Session, product_id: int, new_stock: int) -> ProductPublicResponse:
    if new_stock < 0:
        raise BadRequestException("Stock cannot be negative")

    product = _get_one_product(db, product_id)
    product.stock = new_stock
    db.commit()
    db.refresh(product)

    return ProductPublicResponse.model_validate(product)


def adjust_stock(
    db: Session, product_id: int, quantity: int, reason: str = "Manual"
) -> ProductPublicResponse:
    if quantity == 0:
        raise BadRequestException(
            "Adjustment quantity cannot be zero. No change made to stock."
        )

    product = _get_one_product(db, product_id)

    new_stock: int = product.stock + quantity
    if new_stock < 0:
        raise BadRequestException("Not enough stock to complete this operation")

    product.stock = new_stock

    history = StockHistory(
        product_id=product.id,
        quantity=quantity,
        reason=reason,
    )
    db.add(history)

    db.commit()
    db.refresh(product)

    return ProductPublicResponse.model_validate(product)


async def upload_image(
    db: Session,
    product_id: int,
    file: UploadFile = File(...),
) -> ProductImageResponse:
    # Validaciones previas
    MAX_SIZE_MB = 5
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif"}

    # Validar nombre de archivo
    if not file.filename:
        raise BadRequestException("El archivo no tiene nombre.")

    # Validar extensión
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BadRequestException(
            "Tipo de archivo no permitido. Solo imágenes jpg, jpeg, png, gif."
        )

    # Validar tipo MIME
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise BadRequestException("El archivo no es una imagen válida.")

    # Validar tamaño (lee el archivo en memoria para comprobar el tamaño)
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise BadRequestException(
            f"El archivo supera el tamaño máximo permitido de {MAX_SIZE_MB} MB."
        )
    # Regresa el puntero al inicio para poder guardar el archivo después
    file.file.seek(0)

    # Guardar temporalmente
    temp_dir = tempfile.gettempdir()
    file_name = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file.filename}")
    with open(file_name, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Validar producto
    product = _get_one_product(db, product_id)
    if not product:
        raise NotFoundException(f"Product with ID {product_id} not found")

    # Cargar a Cloudinary
    try:
        url: str = upload_image_service(file, folder="products")
        image = ProductImage(product_id=product_id, url=url)

        product = _get_one_product(db, product_id)
        image_position: int = len(product.images) + 1
        image.position = image_position

        db.add(image)
        db.commit()
        db.refresh(image)

        return ProductImageResponse.model_validate(image)
    except Exception as e:
        raise BadRequestException(f"Error uploading image: {str(e)}")
    finally:
        # Elimina el archivo temporal
        try:
            os.remove(file_name)
        except Exception:
            pass


def get_product_images(db: Session, product_id: int) -> List[ProductImageResponse]:
    product = _get_one_product(db, product_id)
    images: List[ProductImage] = product.images

    if not images:
        raise NotFoundException(f"No images found for product with ID {product_id}")

    return [ProductImageResponse.model_validate(image) for image in images]


def delete_image(db: Session, product_id: int, image_id: int) -> None:
    product = _get_one_product(db, product_id)
    image = db.query(ProductImage).filter_by(id=image_id, product_id=product.id).first()

    if not image:
        raise NotFoundException(
            f"Image with ID {image_id} not found for product {product_id}"
        )

    db.delete(image)
    db.commit()


def update_image_position(
    db: Session, image_id: int, new_position: int
) -> ProductImageResponse:
    image = db.query(ProductImage).filter_by(id=image_id).first()

    if not image:
        raise NotFoundException(f"Image with ID {image_id} not found")

    if image.position == new_position:
        raise BadRequestException("Image is already in the requested position")

    if new_position < 1:
        raise BadRequestException("Position must be greater than 0")

    # Check if the new position is already occupied
    existing_image = (
        db.query(ProductImage)
        .filter_by(product_id=image.product_id, position=new_position)
        .first()
    )

    if existing_image:
        existing_image.position = image.position  # Move existing image to old position

    image.position = new_position
    db.commit()
    db.refresh(image)

    return ProductImageResponse.model_validate(image)


def _get_category_or_400(db: Session, category_id: int) -> Category:
    category = db.query(Category).filter_by(id=category_id).first()
    if not category:
        raise BadRequestException(f"Category with ID {category_id} does not exist")
    return category


def _get_one_product(
    db: Session, product_id: int, include_inactives: bool = False
) -> Product:
    if include_inactives:
        product = db.query(Product).filter_by(id=product_id).first()
    else:
        product = db.query(Product).filter_by(id=product_id, is_active=True).first()

    if not product:
        raise NotFoundException(f"Product with ID {product_id} not found")
    return product
