import os

from beanie import Document, init_beanie
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

load_dotenv()
MONGO_CONN_STR = os.getenv('MONGO_CONN_STR')


class User(Document):
    name: str
    email: str
    age: int


class UserProjection(BaseModel):
    name: str
    email: str


async def get_client():
    client = AsyncIOMotorClient(MONGO_CONN_STR)
    await init_beanie(database=client.db_name, document_models=[User])
    return client


async def seed_data():
    await User.find().delete()
    await User(name='John', email='john@example.com', age=25).insert()
    await User(name='Jane', email='jane@example.com', age=30).insert()
    await User(name='Alice', email='alice@example.com', age=35).insert()
    await User(name='Bob', email='bob@example.com', age=40).insert()
    await User(name='Bobby', email='bobby@example.com', age=28).insert()
    await User(name='Charlie', email='charlie@example.com', age=32).insert()
    await User(name='David', email='david@example.com', age=41).insert()
    await User(name='Eve', email='eve@example.com', age=54).insert()
    await User(name='Frank', email='frank@example.com', age=29).insert()
    await User(name='Grace', email='grace@example.com', age=37).insert()
