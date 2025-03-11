from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Chunk, Client
from app.openai_controller import OpenAIController
from fastapi import HTTPException


class CRUDChunk:
    @staticmethod
    async def create(db: AsyncSession, category_id: int, text: str, transcript: str = None):
        embedding = await OpenAIController().get_embedding(text=text)
        db_chunk = Chunk(text=text, embedding=embedding, category_id=category_id, transcript=transcript)
        db.add(db_chunk)
        await db.commit()
        await db.refresh(db_chunk)
        return db_chunk

    @staticmethod
    async def get_all_by_category(db: AsyncSession, category_id: int) -> list[Chunk]:
        query = select(Chunk).where(Chunk.category_id == category_id)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def delete(db: AsyncSession, chunk_id: int, category_id: int):
        result = await db.execute(
            delete(Chunk)
            .where(Chunk.id == chunk_id, Chunk.category_id == category_id)
            .returning(Chunk.id)
        )

        deleted_row = result.fetchone()

        if not deleted_row:
            raise HTTPException(status_code=404, detail="Chunk not found or not accessible")

        await db.commit()
        return {"message": f"Chunk {chunk_id} deleted successfully"}

    @staticmethod
    async def get_similar(category_id: int, db: AsyncSession, query: str, k: int, similarity_threshold: float = 1):
        embedding = await OpenAIController().get_embedding(text=query)

        cosine_distance_column = Chunk.embedding.cosine_distance(embedding)

        result = await db.execute(
            select(Chunk, cosine_distance_column)
            .filter(cosine_distance_column < similarity_threshold)
            .filter(Chunk.category_id == category_id)
            .order_by(cosine_distance_column)
            .limit(k),
            {"embedding": embedding}
        )

        chunks_with_distances = [
            {
                **{key: getattr(chunk, key) for key in chunk.__table__.columns.keys() if key != "embedding"},
                "distance": distance
            }
            for chunk, distance in result.all()
        ]

        return chunks_with_distances
