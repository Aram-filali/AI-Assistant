"""Test database models"""

import asyncio
from sqlalchemy import select

from app.core.database import get_db_context
from app.models import User, Conversation, Message, Document, Action
from app.models.user import UserRole
from app.models.message import MessageRole
from app.models.document import DocumentType, DocumentStatus
from app.models.action import ActionType, ActionStatus


async def test_create_user():
    """Test user creation"""
    async with get_db_context() as db:
        user = User(
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            hashed_password="hashed_password_here"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"✅ User created: {user.email} (ID: {user.id})")
        return user


async def test_create_conversation(user_id):
    """Test conversation creation"""
    async with get_db_context() as db:
        conversation = Conversation(
            user_id=user_id,
            title="Test Conversation",
            metadata={"language": "fr", "tags": ["test"]}
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        print(f"✅ Conversation created: {conversation.title} (ID: {conversation.id})")
        return conversation


async def test_create_message(conversation_id):
    """Test message creation"""
    async with get_db_context() as db:
        # User message
        user_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="Comment ça marche ?",
            metadata={}
        )
        db.add(user_msg)
        
        # Assistant message
        assistant_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content="Voici comment ça fonctionne...",
            metadata={"sources": ["doc1"], "confidence": 0.9}
        )
        db.add(assistant_msg)
        
        await db.commit()
        print(f"✅ Messages created: 2 messages")


async def test_create_document():
    """Test document creation"""
    async with get_db_context() as db:
        document = Document(
            title="Guide d'utilisation",
            content="Contenu du document...",
            source_url="https://example.com/guide",
            doc_type=DocumentType.WEB,
            status=DocumentStatus.INDEXED,
            metadata={"author": "John Doe"}
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        print(f"✅ Document created: {document.title} (ID: {document.id})")
        return document


async def test_create_action(conversation_id):
    """Test action creation"""
    async with get_db_context() as db:
        action = Action(
            conversation_id=conversation_id,
            action_type=ActionType.EMAIL,
            status=ActionStatus.DONE,
            payload={"to": "client@example.com", "subject": "Devis"},
            result={"sent": True, "message_id": "123"}
        )
        db.add(action)
        await db.commit()
        
        print(f"✅ Action created: {action.action_type}")


async def test_query_data():
    """Test querying data"""
    async with get_db_context() as db:
        # Get all users
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f"\n📊 Total users: {len(users)}")
        
        # Get all conversations
        result = await db.execute(select(Conversation))
        conversations = result.scalars().all()
        print(f"📊 Total conversations: {len(conversations)}")
        
        # Get all messages
        result = await db.execute(select(Message))
        messages = result.scalars().all()
        print(f"📊 Total messages: {len(messages)}")
        
        # Get all documents
        result = await db.execute(select(Document))
        documents = result.scalars().all()
        print(f"📊 Total documents: {len(documents)}")


async def main():
    print("🧪 Testing Database Models...\n")
    
    # Create test data
    user = await test_create_user()
    conversation = await test_create_conversation(user.id)
    await test_create_message(conversation.id)
    await test_create_document()
    await test_create_action(conversation.id)
    
    # Query data
    await test_query_data()
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
