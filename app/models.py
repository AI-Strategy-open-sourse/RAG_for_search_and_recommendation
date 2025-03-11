from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Text
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy import UniqueConstraint
import enum

Base = declarative_base()


class ModelEnum(str, enum.Enum):
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    O1 = "o1"
    O1_MINI = "o1-mini"


class MediaType(str, enum.Enum):
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    tariff = Column(String)
    api_key_hash = Column(String(64), nullable=False, unique=True)
    categories = relationship("Category", back_populates="client")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)

    model = Column(Enum(ModelEnum), nullable=False, default=ModelEnum.GPT_4O)

    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client", back_populates="categories")

    chunks = relationship("Chunk", back_populates="category")
    images = relationship("Image", back_populates="category")

    __table_args__ = (
        UniqueConstraint('client_id', 'name', name='_client_category_uc'),
    )


class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, index=True)

    text = Column(Text, nullable=True)
    transcript = Column(String, nullable=True)

    embedding = Column(Vector(1536))
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="chunks")


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, nullable=False, unique=True)
    embedding = Column(Vector(512), nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Category", back_populates="images")