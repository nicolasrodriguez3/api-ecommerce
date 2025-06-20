import os
import shutil
import tempfile
import uuid
from fastapi import File, UploadFile
from app.core.exceptions import AppException, NotFoundError
from app.core.logger import setup_logger
from app.models.category import Category
from app.models.product import ProductImage
from app.repositories.product import ProductRepository
from app.schemas.product import (
    PaginatedProductResponse,
    ProductImageResponse,
    ProductImagesResponseList,
    ProductPublicResponse,
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
        self, skip: int = 0, limit: int = 100
    ) -> PaginatedProductResponse:
        """Obtener lista de productos con paginación.
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a devolver
        Returns:
            PaginatedProductsResponse: Lista de productos paginada
        """
        products_db = await self.product_repo.get_multi(skip=skip, limit=limit)

        products = [
            ProductPublicResponse.model_validate(product) for product in products_db
        ]

        total_products = await self.product_repo.count()

        return PaginatedProductResponse(
            data=products, total_elements=total_products, skip=skip, limit=limit
        )

    async def create_product(self, product_data) -> ProductPublicResponse:
        product_dict = product_data.model_dump()

        category_id: int | None = product_dict.get("category_id")
        if category_id is None or category_id <= 0:
            product_dict["category_id"] = 1
        else:
            category = await self._get_category(category_id)
            if not category:
                raise NotFoundError("Category", category_id)

        product_db = await self.product_repo.create(product_dict)
        return ProductPublicResponse.model_validate(product_db)

    async def update_product(self, product_id, product_data) -> ProductPublicResponse:
        product_dict: dict = product_data.model_dump()

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

    async def _get_category(self, category_id: int):
        """Obtener categoría por ID."""
        return await self.category_service.get_by_id(category_id)

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
            logger.error(f"Error deleting image from Cloudinary: {deleted.get('error')}")
            raise AppException("Error deleting image from Cloudinary", code="cloudinary_error")

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
                code="image_product_mismatch"
            )
        
        # Verificar si la imagen ya está en la posición solicitada
        if image.position == new_position:
            logger.warning(
                f"Image with ID {image_id} is already in position {new_position}"
            )
            raise AppException(
                "Image is already in the requested position",
                code="image_already_in_position"
            )
        
        # Validar que la posición sea válida
        if new_position < 1:
            logger.error(f"Invalid position {new_position} for image {image_id}")
            raise AppException(
                "Position must be greater than 0",
                code="invalid_position"
            )
        
        # Verificar si la nueva posición ya está ocupada
        existing_image = await self.product_repo.get_image_by_position(
            image.product_id, new_position
        )
        
        if existing_image and existing_image.id != image_id:
            # Intercambiar posiciones en una sola transacción
            old_position = image.position
            updated_image, updated_existing = await self.product_repo.swap_image_positions(
                image_id, existing_image.id, new_position, old_position
            )
            
            logger.info(
                f"Images {image_id} and {existing_image.id} positions swapped: "
                f"{old_position} <-> {new_position}"
            )
            
            return ProductImageResponse.model_validate(updated_image)
        else:
            # Solo actualizar la posición de la imagen objetivo
            updated_image = await self.product_repo.update_image_position(image_id, new_position)
            
            logger.info(f"Image with ID {image_id} position updated to {new_position}")
            return ProductImageResponse.model_validate(updated_image)