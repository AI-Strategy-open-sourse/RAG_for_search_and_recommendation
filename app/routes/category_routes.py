from typing import List

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.category import CRUDCategory
from app.database import get_db
from app.dependencies.get_current_client import get_current_client
from app.schemas import CategoryCreateRequest, CategoryResponse, CategoryUpdateRequest

router = APIRouter()


@router.post("/", response_model=CategoryResponse)
async def create_category(
    request: CategoryCreateRequest,
    current_client=Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    category = await CRUDCategory.create(
        db=db,
        client_id=current_client.id,
        name=request.name,
        prompt=request.prompt,
        model=request.model,
        media_type=request.media_type,
    )
    return category


@router.get("/", response_model=List[CategoryResponse])
async def get_all_categories(
    current_client=Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    categories = await CRUDCategory.get_all_by_client(db, current_client.id)
    return categories


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    request: CategoryUpdateRequest,
    current_client=Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    updated_category = await CRUDCategory.update(
        db=db,
        category_id=category_id,
        client_id=current_client.id,
        name=request.name,
        prompt=request.prompt,
        model=request.model,
    )
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found or does not belong to the client")
    return updated_category


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    current_client=Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    await CRUDCategory.delete(db=db, category_id=category_id, client_id=current_client.id)
    return {"detail": "Category successfully deleted"}