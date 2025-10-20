from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from ... import config
from sqlalchemy.ext.asyncio import async_sessionmaker

SQLALCHEMY_DATABASE_URL = (
    f"mysql+asyncmy://{config.DB_USER}:{config.DB_PASSWORD}@"
    f"{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
)

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False
)

Base = declarative_base()