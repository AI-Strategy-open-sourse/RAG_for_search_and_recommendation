from typing import Optional

from pydantic import BaseModel

from app.models import ModelEnum, MediaType


class ChunkResponse(BaseModel):
    id: int
    text: str


class ChunkCreateRequest(BaseModel):
    text: str
    category_id: int


class ChunkDeleteRequest(BaseModel):
    chunk_id: int
    category_id: int


class FindSimilarRequest(BaseModel):
    query: str
    category_id: int
    k: int = 5
    threshold: float = 0.3
    with_llm_response: bool = True


class UpdateClientRequest(BaseModel):
    prompt: Optional[str] = None


class CategoryCreateRequest(BaseModel):
    name: str
    prompt: str
    model: Optional[ModelEnum] = ModelEnum.GPT_4O
    media_type: Optional[MediaType] = MediaType.TEXT


class CategoryResponse(BaseModel):
    id: int
    name: str
    prompt: str
    media_type: MediaType
    model: ModelEnum

    class Config:
        orm_mode = True


class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    model: Optional[ModelEnum] = None

