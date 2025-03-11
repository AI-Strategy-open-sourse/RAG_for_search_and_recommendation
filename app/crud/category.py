from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Category, ModelEnum, MediaType


class CRUDCategory:
    @staticmethod
    async def create(
            db: AsyncSession,
            client_id: int,
            name: str,
            prompt: str,
            media_type: MediaType,
            model: ModelEnum = ModelEnum.GPT_4O,
    ) -> Category:
        new_cat = Category(
            client_id=client_id,
            name=name,
            media_type=media_type,
            prompt=prompt,
            model=model,
        )
        db.add(new_cat)
        await db.commit()
        await db.refresh(new_cat)
        return new_cat

    @staticmethod
    async def get_by_id(db: AsyncSession, category_id: int, client_id: int) -> Category:
        query = select(Category).where(Category.id == category_id, Category.client_id == client_id)
        result = await db.execute(query)
        category = result.scalars().first()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found or does not belong to the client")

        return category

    @staticmethod
    async def get_all_by_client(db: AsyncSession, client_id: int) -> list[Category]:
        query = select(Category).where(Category.client_id == client_id)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(
            db: AsyncSession,
            category_id: int,
            client_id: int,
            name: str | None = None,
            prompt: str | None = None,
            model: ModelEnum | None = None
    ) -> Category | None:
        category = await CRUDCategory.get_by_id(db, category_id, client_id)
        if not category:
            return None

        if name is not None:
            category.name = name
        if prompt is not None:
            category.prompt = prompt
        if model is not None:
            category.model = model

        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete(db: AsyncSession, category_id: int, client_id: int) -> bool:
        category = await CRUDCategory.get_by_id(db, category_id, client_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found or does not belong to the client")

        await db.delete(category)
        await db.commit()
        return True
