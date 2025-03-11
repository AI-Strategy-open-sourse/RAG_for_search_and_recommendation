from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models import Client


class CRUDClient:
    @staticmethod
    async def get_by_id(db: AsyncSession, client_id: int):
        result = await db.execute(
            select(Client)
            .where(Client.id == client_id)
        )
        client = result.scalar_one_or_none()

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        return client

    @staticmethod
    async def update_fields(
        db: AsyncSession,
        client_id: int,
        fields: Dict[str, Any]
    ):
        client = await CRUDClient.get_by_id(db, client_id)

        for field, value in fields.items():
            if hasattr(client, field):
                setattr(client, field, value)

        await db.commit()
        await db.refresh(client)
        return client