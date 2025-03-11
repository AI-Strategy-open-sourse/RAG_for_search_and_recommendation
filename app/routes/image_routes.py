from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse
from app.crud.category import CRUDCategory
from app.crud.image import CRUDImage
from app.database import get_db
from app.dependencies.get_current_client import get_current_client
from app.models import Client, MediaType

router = APIRouter()


@router.post("/upload-images/")
async def upload_images(
    category_id: int,
    current_client: Client = Depends(get_current_client),
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    category = await CRUDCategory.get_by_id(db=db, category_id=category_id, client_id=current_client.id)

    if category.media_type != MediaType.IMAGE:
        raise HTTPException(status_code=400, detail="Invalid media type")

    for each_file in files:
        await CRUDImage.add_image(
            db=db,
            category_id=category_id,
            image=each_file,
        )

    return JSONResponse(content={"message": "Successful request"}, status_code=200)


@router.post("/similar/")
async def find_similar_images(
    file: UploadFile,
    category_id: int,
    k: int = 5,
    similarity_threshold: float = 1.0,
    current_client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    category = await CRUDCategory.get_by_id(db=db, category_id=category_id, client_id=current_client.id)

    if category.media_type != MediaType.IMAGE:
        raise HTTPException(status_code=400, detail="Invalid media type")

    return await CRUDImage().get_similar(
        db=db,
        category_id=category_id,
        image=file,
        k=k,
        similarity_threshold=similarity_threshold
    )


@router.post("/by_query/")
async def find_similar_images_by_query(
    query: str,
    category_id: int,
    k: int = 5,
    similarity_threshold: float = 1.0,
    current_client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    category = await CRUDCategory.get_by_id(db=db, category_id=category_id, client_id=current_client.id)

    if category.media_type != MediaType.IMAGE:
        raise HTTPException(status_code=400, detail="Invalid media type")

    return await CRUDImage().get_by_query(
        db=db,
        category_id=category_id,
        query=query,
        k=k,
        similarity_threshold=similarity_threshold
    )


@router.get("/category/{category_id}")
async def get_images_by_category(category_id: int, db: AsyncSession = Depends(get_db)):
    images = await CRUDImage.get_images_by_category(db, category_id)

    if not images:
        raise HTTPException(status_code=404, detail="No images found for this category")

    return [{"id": image.id, "path": image.path} for image in images]


@router.delete("/{image_id}/category/{category_id}")
async def delete_image(image_id: int, category_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await CRUDImage.delete_image_by_id_and_category(db, image_id, category_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found or does not belong to the specified category")

    return {"message": "Image successfully deleted"}
