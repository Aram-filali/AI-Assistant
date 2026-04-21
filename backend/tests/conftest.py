"""
pytest configuration and fixtures
"""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Configure pytest for async tests
pytest_plugins = ('pytest_asyncio',)

BASE_URL = "http://localhost:8000"

# Test Database Configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test_user:test_pass@localhost:5433/test_db"
)


@pytest.fixture
def test_data():
    """Provide test data"""
    return {
        "admin_email": "admin@gmail.com",
        "admin_password": "admin123",
        "test_lead": {
            "email": "test@example.com",
            "name": "Test Lead",
            "phone": "+1234567890",
            "company_name": "Test Company"
        },
        "test_conversation": {
            "title": "Test Conversation"
        }
    }


# ==================== DATABASE FIXTURES ====================

@pytest_asyncio.fixture
async def test_db_engine():
    """Create test database engine and initialize tables"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Import models to register them with Base
    from app.models import Base
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        # Create schema if it doesn't exist
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS app'))
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup - drop all tables and schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        try:
            await conn.execute(text('DROP SCHEMA IF EXISTS app CASCADE'))
        except:
            pass  # Schema might already be gone
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_db_engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def user_factory(test_db):
    """Factory for creating test users"""
    from app.models.user import User, UserRole
    from app.api.auth import get_password_hash
    
    async def _create_user(
        email: str = "test@example.com",
        password: str = "password123",
        full_name: str = "Test User",
        role: UserRole = UserRole.USER,
        is_active: str = "true"
    ):
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role=role,
            is_active=is_active
        )
        test_db.add(user)
        await test_db.flush()
        await test_db.refresh(user)
        return user
    
    return _create_user


@pytest_asyncio.fixture
async def kb_factory(test_db):
    """Factory for creating test knowledge bases"""
    from app.models.knowledge import KnowledgeBase
    
    async def _create_kb(
        user_id,
        name: str = "Test KB",
        description: str = "Test Knowledge Base"
    ):
        kb = KnowledgeBase(
            name=name,
            description=description,
            user_id=user_id
        )
        test_db.add(kb)
        await test_db.flush()
        await test_db.refresh(kb)
        return kb
    
    return _create_kb


@pytest_asyncio.fixture
async def conversation_factory(test_db):
    """Factory for creating test conversations"""
    from app.models.conversation import Conversation
    
    async def _create_conversation(
        user_id,
        title: str = "Test Conversation",
        knowledge_base_id=None
    ):
        conversation = Conversation(
            user_id=user_id,
            title=title,
            knowledge_base_id=knowledge_base_id,
            meta_data={}
        )
        test_db.add(conversation)
        await test_db.flush()
        await test_db.refresh(conversation)
        return conversation
    
    return _create_conversation


@pytest_asyncio.fixture
async def message_factory(test_db):
    """Factory for creating test messages"""
    from app.models.message import Message, MessageRole
    
    async def _create_message(
        conversation_id,
        content: str = "Test message",
        role: str = "user"
    ):
        message = Message(
            conversation_id=conversation_id,
            content=content,
            role=MessageRole.USER if role == "user" else MessageRole.ASSISTANT,
            meta_data={}
        )
        test_db.add(message)
        await test_db.flush()
        await test_db.refresh(message)
        return message
    
    return _create_message


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing"""
    async with AsyncClient(base_url=BASE_URL, timeout=10.0) as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client, test_data):
    """Create authenticated async HTTP client"""
    # Login first to get token
    response = await client.post(
        "/auth/login",
        data={
            "username": test_data["admin_email"],
            "password": test_data["admin_password"]
        }
    )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        # Create new client with auth headers
        async with AsyncClient(
            base_url=BASE_URL,
            timeout=10.0,
            headers={"Authorization": f"Bearer {token}"}
        ) as ac:
            yield ac
    else:
        # If login fails, just yield regular client
        yield client


@pytest_asyncio.fixture
async def test_auth_headers(client, test_data):
    """Get test authentication headers"""
    response = await client.post(
        "/auth/login",
        data={
            "username": test_data["admin_email"],
            "password": test_data["admin_password"]
        }
    )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    return {}


# Markers for organizing tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "auth: marks tests as authentication tests"
    )
    config.addinivalue_line(
        "markers", "admin: marks tests as requiring admin access"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
