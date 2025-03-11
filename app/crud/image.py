import io
import uuid

from fastapi import UploadFile
from sqlalchemy import select, cast, Float
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Image
import aiofiles
from PIL import Image as PILImage
from transformers import AutoProcessor, CLIPModel
import torch
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = AutoProcessor.from_pretrained("openai/clip-vit-base-patch32")


class CRUDImage:
    @staticmethod
    async def add_image(
        db: AsyncSession,
        image: UploadFile,
        category_id: int,
    ) -> Image:
        unique_id = uuid.uuid4().hex[:6]

        upload_dir = 'uploads/images'
        os.makedirs(upload_dir, exist_ok=True)
        path = os.path.join(upload_dir, f'{unique_id}_{category_id}_{image.filename}')
        image_bytes = await image.read()
        async with aiofiles.open(path, 'wb') as out_file:
            await out_file.write(image_bytes)

        image_obj = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        features = CRUDImage.get_image_features(image_obj, model, processor)

        image_record = Image(
            path=path,
            embedding=features,
            category_id=category_id,
        )
        db.add(image_record)
        await db.commit()
        await db.refresh(image_record)
        return image_record

    @staticmethod
    def get_image_features(
        image: PILImage.Image,
        model: CLIPModel,
        processor: AutoProcessor
    ) -> np.ndarray:
        image_inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            image_features = model.get_image_features(**image_inputs)

        return image_features.tolist()[0]

    async def get_similar(
            self,
            db: AsyncSession,
            category_id: int,
            image: UploadFile,
            k: int = 5,
            similarity_threshold: float = 1.0,
    ):
        image_obj = PILImage.open(io.BytesIO(await image.read())).convert("RGB")
        query_embedding = self.get_image_features(image_obj, model, processor)

        stmt = (
            select(
                Image.path,
                cast(Image.embedding.op("<=>")(query_embedding), Float).label("similarity")
            )
            .filter(Image.category_id == category_id)
            .order_by("similarity")
            .limit(k)
        )

        results = await db.execute(stmt)
        similar_images = results.fetchall()

        return [
            {"path": path, "similarity": similarity}
            for path, similarity in similar_images
            if similarity <= similarity_threshold
        ]

    @staticmethod
    def get_query_embedding(query):
        text_inputs = processor(text=query, return_tensors="pt", padding=True)
        with torch.no_grad():
            text_features = model.get_text_features(**text_inputs)

        return text_features.tolist()[0]

    async def get_by_query(
            self,
            db: AsyncSession,
            category_id: int,
            query: str,
            k: int = 5,
            similarity_threshold: float = 1.0,
    ):
        query_embedding = self.get_query_embedding(query)

        stmt = (
            select(
                Image.path,
                cast(Image.embedding.op("<=>")(query_embedding), Float).label("similarity")
            )
            .filter(Image.category_id == category_id)
            .order_by("similarity")
            .limit(k)
        )

        results = await db.execute(stmt)
        similar_images = results.fetchall()

        return [
            {"path": path, "similarity": similarity}
            for path, similarity in similar_images
            if similarity <= similarity_threshold
        ]

    @staticmethod
    async def get_images_by_category(db: AsyncSession, category_id: int):
        result = await db.execute(select(Image).where(Image.category_id == category_id))
        return result.scalars().all()

    @staticmethod
    async def delete_image_by_id_and_category(
            db: AsyncSession, image_id: int, category_id: int
    ) -> bool:
        result = await db.execute(
            select(Image).where(
                Image.id == image_id, Image.category_id == category_id
            )
        )
        image = result.scalar_one_or_none()

        if not image:
            return False

        if os.path.exists(image.path):
            os.remove(image.path)

        await db.delete(image)
        await db.commit()

        return True
