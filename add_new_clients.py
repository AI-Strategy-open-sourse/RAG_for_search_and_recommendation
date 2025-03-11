import asyncio
import hashlib
import secrets
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from app.models import ModelEnum, Base, Client, Category, MediaType

DATABASE_URL = "postgresql+asyncpg://postgres:password@0.0.0.0:5432/postgres"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


def hash_api_key(api_key: str):
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key():
    return secrets.token_hex(32)


FIXED_CLIENTS = [
    {"tariff": "basic", "api_key": "client1secretkey"},
    {"tariff": "premium", "api_key": "client2secretkey"},
    {"tariff": "pro", "api_key": "client3secretkey"},
]

# Маппинг media_type к именам и моделям категорий
MEDIA_TYPE_CATEGORIES = {
    MediaType.TEXT: {
        "name": "Text Category",
        "prompt": "This is a prompt for the Text category",
        "model": ModelEnum.GPT_4O,
    },
    MediaType.AUDIO: {
        "name": "Audio Category",
        "prompt": "This is a prompt for the Audio category",
        "model": ModelEnum.GPT_4O_MINI,
    },
    MediaType.VIDEO: {
        "name": "Video Category",
        "prompt": "This is a prompt for the Video category",
        "model": ModelEnum.O1,
    },
    MediaType.IMAGE: {
        "name": "Image Category",
        "prompt": "This is a prompt for the Image category",
        "model": ModelEnum.O1_MINI,
    },
}


async def initialize_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        clients = []
        for client_data in FIXED_CLIENTS:
            api_key = client_data["api_key"]
            hashed_api_key = hash_api_key(api_key)

            client = Client(
                tariff=client_data["tariff"],
                api_key_hash=hashed_api_key,
            )
            session.add(client)
            await session.flush()

            for media_type, cat_data in MEDIA_TYPE_CATEGORIES.items():
                category = Category(
                    name=cat_data["name"],
                    prompt=cat_data["prompt"],
                    model=cat_data["model"],
                    media_type=media_type,
                    client_id=client.id,
                )
                session.add(category)

            clients.append({"api_key": api_key, "client_id": client.id})

        await session.commit()

        print("Clients and categories added successfully. API keys and Client IDs:")
        for client in clients:
            print(f"Client ID: {client['client_id']}, API Key: {client['api_key']}")

        result = await session.execute(select(Category, Client).join(Client))
        categories = result.fetchall()

        print("\nСписок всех категорий с их ID и связанными клиентами:")
        for category, client in categories:
            print(f"Category ID: {category.id}, Name: {category.name}, Media Type: {category.media_type}, Client ID: {client.id}, Tariff: {client.tariff}")

if __name__ == "__main__":
    asyncio.run(initialize_database())