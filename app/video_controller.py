import whisper
import asyncio

from app.crud.chunk import CRUDChunk
from app.database import get_db
from app.openai_controller import OpenAIController

MODEL = whisper.load_model("small")  # Или "medium" для более точной транскрибации


async def process_video(task_id: str, video_file_path: str, category_id: int):
    print(f"[PROCESS_VIDEO] Начинаем обработку {video_file_path} (task_id={task_id}, category_id={category_id})")

    try:
        transcription = await asyncio.to_thread(
            MODEL.transcribe, video_file_path, language="ru", fp16=False
        )
        transcript = transcription.get("text", "")

        summary = await OpenAIController().summarize_transcription(transcription_text=transcript)

        print(f"[PROCESS_VIDEO] Транскрибация завершена (task_id={task_id})")
        print(f"Transcript: {transcript}")
        print(f"Summary: {summary}")

        async for db in get_db():
            await CRUDChunk.create(
                db=db,
                category_id=category_id,
                text=summary,
                transcript=transcript,
            )
            break

    except Exception as e:
        print(f"[PROCESS_VIDEO] Ошибка обработки файла {video_file_path}: {e}")

    print(f"[PROCESS_VIDEO] Обработка завершена (task_id={task_id})")