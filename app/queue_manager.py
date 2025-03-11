from collections import deque
import asyncio
from app.video_controller import process_video

media_queue = deque()
tasks = []


async def process_media_queue():
    while True:
        if media_queue:
            task = media_queue.popleft()
            await process_video(task_id=task["id"], video_file_path=task["file_path"], category_id=task["category_id"])

        await asyncio.sleep(1)


def start_queue():
    tasks.append(asyncio.create_task(process_media_queue()))
    print("[QUEUE] Очередь запущена")


async def stop_queue():
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    print("[QUEUE] Очередь остановлена")
    tasks.clear()