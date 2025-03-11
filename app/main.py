from app.database import init_db
from app.queue_manager import stop_queue, start_queue
from app.routes import chunk_routes, category_routes, image_routes

from fastapi import FastAPI

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await init_db()
    start_queue()


@app.on_event("shutdown")
async def shutdown_event():
    await stop_queue()
    print("[APP] Приложение завершается, очередь остановлена.")


app.include_router(category_routes.router, prefix="/categories", tags=["Categories"])
app.include_router(chunk_routes.router, prefix="/chunks", tags=["Chunks"])
app.include_router(image_routes.router, prefix="/images", tags=["Images"])


