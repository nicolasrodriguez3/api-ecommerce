import os
import shutil
import tempfile
import uuid
from fastapi import File, UploadFile
from app.core.exceptions import AppException, ConflictError, NotFoundError
from app.core.logger import setup_logger
from app.models.category import Category
from app.models.product import ProductImage
from app.repositories.product import ProductRepository
from app.schemas.category import CategoryPublicResponse
from app.schemas.product import (
    PaginatedProductResponse,
    ProductImageResponse,
    ProductImagesResponseList,
    ProductPublicResponse,
    ProductUpdate,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cloudinary import (
    delete_image_from_url,
    upload_image as upload_image_service,
)

from app.services.category import CategoryService

logger = setup_logger(__name__)


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_service = CategoryService(db)

    async def get_product_by_id(self, product_id) -> ProductPublicResponse:
        product_db = await self.product_repo.get_by_id(product_id)
        if not product_db:
            raise NotFoundError("Product", product_id)

        return ProductPublicResponse.model_validate(product_db)

    async def get_products(
        self,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        order_by: str = "id",
        order_dir: str = "asc",
        category_id: int | None = None,
        is_active: bool = True,
    ) -> PaginatedProductResponse:
        """Obtener lista de productos con filtros  opcionales, ordenamiento y paginación.

        Args:
            skip: Número de registros a saltar (para paginación)
            limit: Máximo número de productos a devolver
            search: Término de búsqueda opcional para filtrar por nombre
            min_price: Precio mínimo opcional para filtrar productos
            max_price: Precio máximo opcional para filtrar productos
            order_by: Campo por el cual ordenar los resultados (default: 'id')
            order_dir: Dirección del orden ('asc' o 'desc', default: 'asc')
            category_id: ID de categoría opcional para filtrar
            is_active: Filtrar solo productos activos (default: True)

        Returns:
            PaginatedProductResponse: Lista paginada de productos con metadata

        Raises:
            AppException: Si el campo de ordenamiento no es válido
        """

        # Validar parámetros de ordenamiento
        ALLOWED_ORDER_FIELDS = {
            "id",
            "name",
            "price",
            "stock",
            "created_at",
            "updated_at",
        }
        if order_by not in ALLOWED_ORDER_FIELDS:
            logger.error(
                f"Invalid order_by field: {order_by}. Allowed fields are: {', '.join(ALLOWED_ORDER_FIELDS)}"
            )
            raise AppException(
                f"Invalid order_by field. Allowed fields are: {', '.join(ALLOWED_ORDER_FIELDS)}",
                code="invalid_order_field",
            )

        # Validar dirección de ordenamiento
        if order_dir.lower() not in ["asc", "desc"]:
            logger.error(f"Invalid order_dir: {order_dir}. Must be 'asc' or 'desc'")
            raise AppException(
                "Invalid order direction. Must be 'asc' or 'desc'",
                code="invalid_order_direction",
            )
        # Crear filtros
        filters = {
            "search": search,
            "min_price": min_price,
            "max_price": max_price,
            "category_id": category_id,
            "is_active": is_active,
        }

        # Obtener productos con filtros
        products_db = await self.product_repo.get_products_with_filters(
            skip=skip,
            limit=limit,
            filters=filters,
            order_by=order_by,
            order_dir=order_dir.lower(),
        )

        # Obtener total de productos con los mismos filtros
        total_products = await self.product_repo.count_products_with_filters(filters)

        # Convertir a response objects
        products = [
            ProductPublicResponse.model_validate(product) for product in products_db
        ]

        # Calcular metadata de paginación
        total_pages = total_products // limit + (1 if total_products % limit > 0 else 0)
        current_page = skip // limit + 1

        logger.info(
            f"Retrieved {len(products)} products (page {current_page}/{total_pages}, "
            f"total: {total_products}) with filters: {filters}"
        )

        return PaginatedProductResponse(
            data=products,
            total_elements=total_products,
            skip=skip,
            limit=limit,
            current_page=current_page,
            total_pages=total_pages,
        )

    async def create_product(self, product_data) -> ProductPublicResponse:
        product_dict = product_data.model_dump()

        # Validar nombre único
        await self._validate_unique_name(product_dict["name"])

        category_id: int | None = product_dict.get("category_id")
        if category_id is None or category_id <= 0:
            category_id = 1
            product_dict["category_id"] = category_id

        category = await self._get_category(category_id)
        if not category:
            raise NotFoundError("Category", category_id)

        product_db = await self.product_repo.create(product_dict)
        return ProductPublicResponse.model_validate(product_db)

    async def update_product(
        self, product_id, product_data: ProductUpdate
    ) -> ProductPublicResponse:
        existing_product = await self.product_repo.get_by_id(product_id)
        if not existing_product:
            raise NotFoundError("Product", product_id)

        product_dict = product_data.model_dump(exclude_unset=True)

        # Si se está actualizando el nombre, validar unicidad
        if "name" in product_dict:
            await self._validate_unique_name(
                product_dict["name"], exclude_id=product_id
            )

        category_id: int | None = product_dict.get("category_id")
        if category_id is None or category_id <= 0:
            product_dict["category_id"] = 1
        else:
            category = await self._get_category(category_id)
            if not category:
                raise NotFoundError("Category", category_id)

        product_db = await self.product_repo.update(product_id, product_dict)
        return ProductPublicResponse.model_validate(product_db)

    async def delete_product(self, product_id):
        return await self.product_repo.delete(product_id)

    async def upload_image(
        self,
        product_id: int,
        file: UploadFile = File(...),
    ):
        """Subir una imagen para un producto."""

        # Validaciones previas
        MAX_SIZE_MB = 5
        ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}
        ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif"}

        # Validar producto
        product_db = await self.product_repo.get_by_id(product_id)
        if not product_db:
            raise NotFoundError("Product", product_id)

        # Validar nombre de archivo
        if not file.filename:
            logger.error("File upload failed: No filename provided")
            raise AppException("El archivo no tiene nombre.", code="file_name_required")

        # Validar extensión
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.error(
                f"File upload failed: Invalid file extension '{ext}'. Allowed extensions are {', '.join(ALLOWED_EXTENSIONS)}"
            )
            raise AppException(
                "Tipo de archivo no permitido. Solo imágenes jpg, jpeg, png, gif.",
                code="invalid_file_extension",
            )

        # Validar tipo MIME
        if file.content_type not in ALLOWED_MIME_TYPES:
            logger.error(
                f"File upload failed: Invalid MIME type '{file.content_type}'. Allowed types are {', '.join(ALLOWED_MIME_TYPES)}"
            )
            raise AppException(
                "El archivo no es una imagen válida.", code="invalid_file_type"
            )

        # Validar tamaño (lee el archivo en memoria para comprobar el tamaño)
        contents = await file.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > MAX_SIZE_MB:
            logger.error(
                f"File upload failed: File size {size_mb:.2f} MB exceeds maximum allowed size of {MAX_SIZE_MB} MB"
            )
            raise AppException(
                f"El archivo supera el tamaño máximo permitido de {MAX_SIZE_MB} MB.",
                code="file_size_exceeded",
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
            image_position: int = len(product_db.images) + 1
            image.position = image_position

            # Llamar al repo y guardar la imagen
            image = await self.product_repo.create_image(product_id, image)

            logger.info(
                f"Image uploaded successfully for product {product_id}: {image.url}"
            )

            return ProductImageResponse.model_validate(image)
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            raise AppException(
                f"Error uploading image: {str(e)}", code="image_upload_error"
            )
        finally:
            # Elimina el archivo temporal
            try:
                os.remove(file_name)
            except Exception:
                logger.error(f"Failed to delete temporary file: {file_name}")
                pass

    async def get_product_images(self, product_id: int) -> ProductImagesResponseList:
        """Obtener imágenes de un producto."""
        product_db = await self.get_product_by_id(product_id)
        if not product_db:
            raise NotFoundError("Product", product_id)

        return ProductImagesResponseList(images=product_db.images)

    async def delete_image(self, product_id: int, image_id: int):
        """Elimina una imagen de un producto."""
        product = await self.get_product_by_id(product_id)
        # image = self.db.query(ProductImage).filter_by(id=image_id, product_id=product.id).first()
        image = await self.product_repo.get_image_by_id(image_id)

        if not image:
            logger.error(f"Image with ID {image_id} not found for product {product_id}")
            raise AppException(
                f"Image with ID {image_id} not found for product {product_id}",
                code="image_not_found",
            )

        # Eliminar imagen de Cloudinary
        deleted: dict[str, str] = delete_image_from_url(image.url)
        if deleted.get("result") != "ok":
            logger.error(
                f"Error deleting image from Cloudinary: {deleted.get('error')}"
            )
            raise AppException(
                "Error deleting image from Cloudinary", code="cloudinary_error"
            )

        # Eliminar imagen de la base de datos
        await self.db.delete(image)
        await self.db.commit()
        logger.info(
            f"Image with ID {image_id} deleted successfully from product {product_id}"
        )
        return None

    async def update_image_position(
        self, image_id: int, new_position: int, product_id: int
    ) -> ProductImageResponse:
        """
        Versión optimizada que usa una sola transacción para intercambiar posiciones.
        """
        # Obtener la imagen por ID
        image = await self.product_repo.get_image_by_id(image_id)

        if not image:
            logger.error(f"Image with ID {image_id} not found")
            raise NotFoundError("Image", image_id)

        # Validación opcional del product_id
        if product_id is not None and image.product_id != product_id:
            logger.error(f"Image {image_id} does not belong to product {product_id}")
            raise AppException(
                f"Image {image_id} does not belong to product {product_id}",
                code="image_product_mismatch",
            )

        # Verificar si la imagen ya está en la posición solicitada
        if image.position == new_position:
            logger.warning(
                f"Image with ID {image_id} is already in position {new_position}"
            )
            raise AppException(
                "Image is already in the requested position",
                code="image_already_in_position",
            )

        # Validar que la posición sea válida
        if new_position < 1:
            logger.error(f"Invalid position {new_position} for image {image_id}")
            raise AppException(
                "Position must be greater than 0", code="invalid_position"
            )

        # Verificar si la nueva posición ya está ocupada
        existing_image = await self.product_repo.get_image_by_position(
            image.product_id, new_position
        )

        if existing_image and existing_image.id != image_id:
            # Intercambiar posiciones en una sola transacción
            old_position = image.position
            updated_image, updated_existing = (
                await self.product_repo.swap_image_positions(
                    image_id, existing_image.id, new_position, old_position
                )
            )

            logger.info(
                f"Images {image_id} and {existing_image.id} positions swapped: "
                f"{old_position} <-> {new_position}"
            )

            return ProductImageResponse.model_validate(updated_image)
        else:
            # Solo actualizar la posición de la imagen objetivo
            updated_image = await self.product_repo.update_image_position(
                image_id, new_position
            )

            logger.info(f"Image with ID {image_id} position updated to {new_position}")
            return ProductImageResponse.model_validate(updated_image)

    async def _get_category(self, category_id: int) -> CategoryPublicResponse:
        """Obtener categoría por ID."""
        return await self.category_service.get_category_by_id(category_id)

    async def _validate_unique_name(self, name: str, exclude_id: int | None = None):
        """Valida que el nombre del producto sea único."""
        existing_product = await self.product_repo.get_by_name(name)
        if existing_product and (
            exclude_id is None or existing_product.id != exclude_id
        ):
            raise ConflictError(f"Un producto con el nombre '{name}' ya existe")
