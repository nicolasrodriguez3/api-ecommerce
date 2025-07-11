from logging import Logger
import os
import shutil
import tempfile
from typing import List
import uuid
from fastapi import File, UploadFile
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from app.categories.models import Category
from app.core.cloudinary import (
    delete_image_from_url,
    upload_image as upload_image_service,
)
from app.core.exceptions import BadRequestException, NotFoundException
from app.core.logger import setup_logger
from app.core import db_connection
from app.products.models import Product, ProductImage, StockHistory
from app.products.schemas import ProductCreate, ProductImageResponse, ProductUpdate
from app.products.schemas import ProductPublicResponse

logger: Logger = setup_logger(__name__)


db: Session = db_connection.session


def get_products(
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    order_by: str = "id",
    order_dir: str = "asc",
) -> tuple[List[ProductPublicResponse], int, int]:
    """
    Get a paginated list of products with optional filters and sorting.
    :param db: Database session
    :param skip: Number of products to skip (for pagination)
    :param limit: Maximum number of products to return
    :param search: Optional search term to filter products by name
    :param min_price: Optional minimum price to filter products
    :param max_price: Optional maximum price to filter products
    :param order_by: Field to order the results by (default is 'id')
    :param order_dir: Direction of the order ('asc' or 'desc', default is 'asc')
    :return: Tuple containing a list of ProductPublicResponse, current page number, and total pages
    """

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
        logger.error(
            f"Invalid order_by field: {order_by}. Allowed fields are: {', '.join(ALLOWED_ORDER_FIELDS)}"
        )
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


def get_by_id(product_id: int) -> ProductPublicResponse:
    """
    Get a product by its ID.
    :param db: Database session
    :param product_id: ID of the product to retrieve
    :return: ProductPublicResponse containing product details
    """
    product = _get_one_product(product_id)

    return ProductPublicResponse.model_validate(product)


def create(product_data: ProductCreate) -> ProductPublicResponse:
    _get_category_or_400(product_data.category_id)

    new_product = Product(**product_data.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    product_with_category = (
        db.query(Product).options(joinedload(Product.category)).get(new_product.id)
    )

    logger.info(f"Product created successfully with ID: {new_product.id}")
    return ProductPublicResponse.model_validate(product_with_category)


def update(
    product_id: int, product_data: ProductUpdate
) -> ProductPublicResponse:
    # Validar que el producto existe
    product = _get_one_product(product_id)
    # Guarda el estado original antes de modificar
    original_data = product.to_dict().copy()

    # Validar categoría
    if product_data.category_id is not None:
        _get_category_or_400(product_data.category_id)

    print(
        f"Updating product {product_id} with data: {product_data.model_dump(exclude_none=True)}"
    )
    # Actualizar los campos del producto
    for key, value in product_data.model_dump(exclude_none=True).items():
        setattr(product, key, value)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product {product_id}: {str(e)}")
        raise BadRequestException(f"Error updating product: {str(e)}")

    db.refresh(product)

    product_with_category = _get_one_product(product_id)
    print(f"Product with category: {product_with_category.to_dict()}")
    if not product_with_category:
        logger.error(f"Product with ID {product_id} not found after update")
        raise NotFoundException(f"Product with ID {product_id} not found")

    logger.info(
        f"Product ID {product_id} updated successfully from {original_data} to {product_data.model_dump(exclude_none=True)}"
    )
    return ProductPublicResponse.model_validate(product_with_category)


def delete(product_id: int) -> None:
    """
    Delete a product by its ID.
    :param product_id: ID of the product to delete
    :param db: Database session
    :return: None
    """

    product = _get_one_product(product_id)

    product.is_active = False
    db.commit()
    logger.info(f"Product {product_id} deleted successfully")
    return None


def restore(product_id: int) -> ProductPublicResponse:
    """
    Restore a previously deleted product by its ID.
    :param product_id: ID of the product to restore
    :param db: Database session
    :return: ProductPublicResponse containing restored product details
    """
    product = _get_one_product(product_id, include_inactives=True)

    product.is_active = True
    db.commit()
    db.refresh(product)

    logger.info(f"Product {product_id} restored successfully")
    return ProductPublicResponse.model_validate(product)


def update_stock(product_id: int, new_stock: int) -> ProductPublicResponse:
    """
    Update the stock of a product.
    :param db: Database session
    :param product_id: ID of the product to update
    :param new_stock: New stock value to set
    :return: ProductPublicResponse containing updated product details
    """
    if new_stock < 0:
        logger.error(
            f"Attempted to set negative stock for product {product_id}: {new_stock}"
        )
        raise BadRequestException("Stock cannot be negative")

    product = _get_one_product(product_id)
    product.stock = new_stock
    db.commit()
    db.refresh(product)

    logger.info(f"Stock updated for product {product_id}: new stock {product.stock}")
    return ProductPublicResponse.model_validate(product)


def adjust_stock(
    product_id: int, quantity: int, reason: str = "Manual"
) -> ProductPublicResponse:
    """
    Adjust the stock of a product by a specified quantity.
    :param db: Database session
    :param product_id: ID of the product to adjust
    :param quantity: Quantity to adjust (can be positive or negative)
    :param reason: Reason for the stock adjustment
    :return: ProductPublicResponse containing updated product details
    """
    if quantity == 0:
        logger.warning(
            f"Attempted to adjust stock for product {product_id} with zero quantity"
        )
        raise BadRequestException(
            "Adjustment quantity cannot be zero. No change made to stock."
        )

    product = _get_one_product(product_id)

    new_stock: int = product.stock + quantity
    if new_stock < 0:
        logger.error(
            f"Insufficient stock for product {product_id}: current stock {product.stock}, attempted adjustment {quantity}"
        )
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

    logger.info(
        f"Stock adjusted for product {product_id}: new stock {product.stock}, quantity adjusted {quantity}, reason: {reason}"
    )

    return ProductPublicResponse.model_validate(product)


async def upload_image(
    product_id: int,
    file: UploadFile = File(...),
) -> ProductImageResponse:
    # Validaciones previas
    MAX_SIZE_MB = 5
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif"}

    # Validar producto
    product = _get_one_product(product_id)

    # Validar nombre de archivo
    if not file.filename:
        logger.error("File upload failed: No filename provided")
        raise BadRequestException("El archivo no tiene nombre.")

    # Validar extensión
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        logger.error(
            f"File upload failed: Invalid file extension '{ext}'. Allowed extensions are {', '.join(ALLOWED_EXTENSIONS)}"
        )
        raise BadRequestException(
            "Tipo de archivo no permitido. Solo imágenes jpg, jpeg, png, gif."
        )

    # Validar tipo MIME
    if file.content_type not in ALLOWED_MIME_TYPES:
        logger.error(
            f"File upload failed: Invalid MIME type '{file.content_type}'. Allowed types are {', '.join(ALLOWED_MIME_TYPES)}"
        )
        raise BadRequestException("El archivo no es una imagen válida.")

    # Validar tamaño (lee el archivo en memoria para comprobar el tamaño)
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        logger.error(
            f"File upload failed: File size {size_mb:.2f} MB exceeds maximum allowed size of {MAX_SIZE_MB} MB"
        )
        raise BadRequestException(
            f"El archivo supera el tamaño máximo permitido de {MAX_SIZE_MB} MB."
        )

    # Guardar temporalmente
    temp_dir = tempfile.gettempdir()
    file_name = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file.filename}")
    with open(file_name, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Regresa el puntero al inicio para poder guardar el archivo
    file.file.seek(0)

    # Cargar a Cloudinary
    try:
        response: dict = upload_image_service(file, folder="products")
        image = ProductImage(product_id=product_id, **response)
        image_position: int = len(product.images) + 1
        image.position = image_position

        db.add(image)
        db.commit()
        db.refresh(image)

        logger.info(
            f"Image uploaded successfully for product {product_id}: {image.url}"
        )

        return ProductImageResponse.model_validate(image)
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise BadRequestException(f"Error uploading image: {str(e)}")
    finally:
        # Elimina el archivo temporal
        try:
            os.remove(file_name)
        except Exception:
            logger.error(f"Failed to delete temporary file: {file_name}")
            pass


def get_product_images(product_id: int) -> List[ProductImageResponse]:
    product = _get_one_product(product_id)
    images: List[ProductImage] = product.images

    return [ProductImageResponse.model_validate(image) for image in images]


def delete_image(product_id: int, image_id: int) -> None:
    product = _get_one_product(product_id)
    image = db.query(ProductImage).filter_by(id=image_id, product_id=product.id).first()

    if not image:
        logger.error(f"Image with ID {image_id} not found for product {product_id}")
        raise NotFoundException(
            f"Image with ID {image_id} not found for product {product_id}"
        )

    # Eliminar imagen de Cloudinary
    deleted: dict[str, str] = delete_image_from_url(image.url)
    if deleted.get("result") != "ok":
        logger.error(f"Error deleting image from Cloudinary: {deleted.get('error')}")
        raise BadRequestException("Error deleting image from Cloudinary")

    # Eliminar imagen de la base de datos
    db.delete(image)
    db.commit()
    logger.info(
        f"Image with ID {image_id} deleted successfully from product {product_id}"
    )
    return None


def update_image_position(
    image_id: int, new_position: int
) -> ProductImageResponse:
    image = db.query(ProductImage).filter_by(id=image_id).first()

    if not image:
        logger.error(f"Image with ID {image_id} not found")
        raise NotFoundException(f"Image with ID {image_id} not found")

    if image.position == new_position:
        logger.warning(
            f"Image with ID {image_id} is already in position {new_position}"
        )
        raise BadRequestException("Image is already in the requested position")

    if new_position < 1:
        logger.error(f"Invalid position {new_position} for image {image_id}")
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

    logger.info(f"Image with ID {image_id} position updated to {new_position}")
    return ProductImageResponse.model_validate(image)


def _get_category_or_400(category_id: int) -> Category:
    category = db.query(Category).filter_by(id=category_id).first()
    if not category:
        raise BadRequestException(f"Category with ID {category_id} does not exist")
    return category


def _get_one_product(
    product_id: int, include_inactives: bool = False
) -> Product:
    if include_inactives:
        product = db.query(Product).filter_by(id=product_id).first()
    else:
        product = db.query(Product).filter_by(id=product_id, is_active=True).first()

    if not product:
        logger.error(f"Product with ID {product_id} not found")
        raise NotFoundException(f"Product with ID {product_id} not found")
    return product
