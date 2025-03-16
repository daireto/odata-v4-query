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
    addresses: list[str] = []


class UserProjection(BaseModel):
    name: str
    email: str


async def get_client():
    client = AsyncIOMotorClient(MONGO_CONN_STR)
    await init_beanie(database=client.db_name, document_models=[User])
    return client


async def seed_data():
    await User.find().delete()
    await User(
        name='John',
        email='john@example.com',
        age=25,
        addresses=['123 Main St', '456 Main St'],
    ).insert()
    await User(
        name='Jane',
        email='jane@example.com',
        age=30,
        addresses=['456 Main St', '789 Main St'],
    ).insert()
    await User(
        name='Alice',
        email='alice@example.com',
        age=35,
        addresses=['789 Main St', '101 Main St', '102 Main St'],
    ).insert()
    await User(
        name='Bob',
        email='bob1@example.com',
        age=28,
        addresses=['101 Main St'],
    ).insert()
    await User(
        name='Bob',
        email='bob2@example.com',
        age=40,
        addresses=['102 Main St'],
    ).insert()
    await User(
        name='Charlie',
        email='charlie@example.com',
        age=32,
        addresses=['103 Main St', '104 Main St'],
    ).insert()
    await User(
        name='David',
        email='david@example.com',
        age=41,
        addresses=['104 Main St'],
    ).insert()
    await User(
        name='Eve',
        email='eve@example.com',
        age=54,
        addresses=['105 Main St'],
    ).insert()
    await User(
        name='Frank',
        email='frank@example.com',
        age=29,
        addresses=['106 Main St', '107 Main St', '108 Main St'],
    ).insert()
    await User(
        name='Grace',
        email='grace@example.com',
        age=37,
        addresses=['107 Main St', '108 Main St'],
    ).insert()
