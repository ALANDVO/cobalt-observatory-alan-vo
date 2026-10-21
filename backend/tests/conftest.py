"""
Pytest configuration and fixtures.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.main import create_app
from app.core.config import settings

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine per test."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()





@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
def app(test_session):
    """Create test FastAPI app with overridden dependencies."""
    from app.core.database import get_session
    from fastapi.testclient import TestClient

    async def override_get_session():
        yield test_session

    test_app = create_app()
    test_app.dependency_overrides[get_session] = override_get_session

    with TestClient(test_app) as client:
        yield client