from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import hashlib

from app.database import get_db
from app.models import Client

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(api_key: str):
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_current_client(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
):
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key missing")

    hashed_api_key = hash_api_key(api_key)

    result = await db.execute(select(Client).filter(Client.api_key_hash == hashed_api_key))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    return user