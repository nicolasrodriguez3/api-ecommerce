from urllib.parse import urlparse
from uuid import uuid4
import cloudinary
import cloudinary.uploader
from app.core.config import get_settings

settings = get_settings()

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
)


def upload_image(file, folder="products") -> dict:
    """
    Uploads an image to Cloudinary and returns the secure URL.
    :param file: FastAPI UploadFile object
    :param folder: Optional folder name in Cloudinary
    :return: Secure URL of the uploaded image
    """
    # print(file)
    
    filename = str(uuid4())
    print(f"Uploading {file.filename} to Cloudinary with public_id {filename} in folder {folder}")
    result = cloudinary.uploader.upload(
        file.file,
        public_id=filename,
        folder=folder,
        resource_type="image",
        overwrite=True,
    )
    print(f"Upload result: {result}")
    return {"url": result["secure_url"], "public_id": result["public_id"]}


def delete_image_from_url(url: str) -> dict:
    parsed = urlparse(url)
    public_id = parsed.path.split("/")[-1].split(".")[
        0
    ]  # asume que termina en /filename.jpg
    folder = "/".join(parsed.path.strip("/").split("/")[4:-1])
    full_id = f"{folder}/{public_id}"
    return cloudinary.uploader.destroy(
        full_id,
        resource_type="image",
        invalidate=True,
    )
