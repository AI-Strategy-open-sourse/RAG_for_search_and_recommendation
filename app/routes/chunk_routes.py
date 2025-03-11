import os
import uuid
from typing import List

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, File

from app.crud.category import CRUDCategory
from app.crud.chunk import CRUDChunk
from app.database import get_db
from app.dependencies.get_current_client import get_current_client
from app.models import Client, MediaType
from app.openai_controller import OpenAIController
from app.queue_manager import media_queue
from app.schemas import ChunkResponse, ChunkCreateRequest, FindSimilarRequest, ChunkDeleteRequest

router = APIRouter()


@router.post("/chunks/", response_model=ChunkResponse)
async def add_chunk(
        request: ChunkCreateRequest,
        current_client: Client = Depends(get_current_client),
        db: AsyncSession = Depends(get_db),
):
    category = await CRUDCategory.get_by_id(db=db, category_id=request.category_id, client_id=current_client.id)

    if category.media_type != MediaType.TEXT:
        raise HTTPException(status_code=400, detail="Invalid media type")

    return await CRUDChunk.create(
        db=db,
        text=request.text,
        category_id=category.id,
    )


@router.delete("/chunks/{chunk_id}")
async def remove_chunk(
        request: ChunkDeleteRequest,
        current_client: Client = Depends(get_current_client),
        db: AsyncSession = Depends(get_db),
):
    category = await CRUDCategory.get_by_id(db=db, category_id=request.category_id, client_id=current_client.id)

    return await CRUDChunk.delete(
        db=db,
        chunk_id=request.chunk_id,
        category_id=category.id,
    )


@router.get("/", response_model=List[ChunkResponse])
async def get_all_chunks(
    category_id: int,
    current_client=Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    await CRUDCategory.get_by_id(db=db, category_id=category_id, client_id=current_client.id)

    categories = await CRUDChunk.get_all_by_category(db, category_id=category_id)
    return categories


@router.post("/chunks/similar/")
async def find_similar_chunks(
        request: FindSimilarRequest,
        current_client: Client = Depends(get_current_client),
        db: AsyncSession = Depends(get_db),
):
    category = await CRUDCategory.get_by_id(db=db, category_id=request.category_id, client_id=current_client.id)

    similar_chunks = await CRUDChunk.get_similar(
        db=db,
        category_id=category.id,
        query=request.query,
        similarity_threshold=request.threshold,
        k=request.k,
    )

    if request.with_llm_response:
        for chunk in similar_chunks:
            llm_response = await OpenAIController().explain_match(
                system_prompt=category.prompt,
                query=request.query,
                chunk_text=chunk['text'],
                model=category.model,
            )
            chunk['llm_response'] = llm_response

    return similar_chunks


@router.post("/upload_videos")
async def upload_videos(
        category_id: int,
        files: List[UploadFile] = File(...),
        current_client: Client = Depends(get_current_client),
        db: AsyncSession = Depends(get_db),
):
    category = await CRUDCategory.get_by_id(db=db, category_id=category_id, client_id=current_client.id)

    if category.media_type not in [
        MediaType.VIDEO,
        MediaType.AUDIO,
    ]:
        raise HTTPException(status_code=400, detail="Invalid media type")

    upload_dir = "uploads/videos"
    os.makedirs(upload_dir, exist_ok=True)

    task_ids = []
    for file in files:
        task_id = str(uuid.uuid4())
        file_path = os.path.join(upload_dir, f"{task_id}_{file.filename}")

        with open(file_path, "wb") as f:
            f.write(await file.read())

        media_queue.append({"id": task_id, "file_path": file_path, "category_id": category.id})
        task_ids.append(task_id)

    return {
        "message": "Файлы загружены и поставлены в очередь",
        "task_ids": task_ids
    }
