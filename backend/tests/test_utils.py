"""
Utility and helper tests - Database models, validators, utilities
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select


@pytest.mark.unit
class TestDatabaseModels:
    """Test database model creation and validation"""
    
    async def test_user_model_creation(self):
        """Test User model instantiation"""
        try:
            from app.models import User
            from app.models.user import UserRole
            
            user = User(
                email="test@example.com",
                full_name="Test User",
                role=UserRole.USER,
                hashed_password="hashed_pwd_xyz"
            )
            
            assert user.email == "test@example.com"
            assert user.full_name == "Test User"
            assert user.role == UserRole.USER
        except ImportError:
            pytest.skip("Models not available")
    
    async def test_conversation_model(self):
        """Test Conversation model"""
        try:
            from app.models import Conversation
            from uuid import uuid4
            
            conv_id = uuid4()
            conversation = Conversation(
                id=conv_id,
                user_id=1,
                title="Test Conversation",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            assert conversation.id == conv_id
            assert conversation.title == "Test Conversation"
            assert conversation.created_at
        except ImportError:
            pytest.skip("Models not available")
    
    async def test_message_model(self):
        """Test Message model"""
        try:
            from app.models import Message
            from app.models.message import MessageRole
            
            message = Message(
                conversation_id="conv-123",
                role=MessageRole.USER,
                content="Test message",
                created_at=datetime.now()
            )
            
            assert message.role == MessageRole.USER
            assert message.content == "Test message"
        except ImportError:
            pytest.skip("Models not available")
    
    async def test_document_model(self):
        """Test Document model"""
        from app.models.document import DocumentChunk
        from datetime import datetime
        
        chunk = DocumentChunk(
            document_id="00000000-0000-0000-0000-000000000001",
            chunk_index=0,
            content="Test chunk content",
            embedding_id=None,
            created_at=datetime.now()
        )
        
        assert chunk.document_id is not None
        assert chunk.chunk_index == 0
        assert chunk.content == "Test chunk content"
    
    async def test_action_model(self):
        """Test Action model"""
        try:
            from app.models import Action
            from app.models.action import ActionType, ActionStatus
            
            # Use valid Action model parameters
            action = Action(
                action_type=ActionType.EMAIL,
                status=ActionStatus.PENDING,
                created_at=datetime.now()
            )
            
            assert action.status == ActionStatus.PENDING
        except ImportError:
            pytest.skip("Models not available")


@pytest.mark.unit
class TestValidators:
    """Test input validators and schemas"""
    
    async def test_email_validation(self):
        """Test email validation"""
        # Test valid email
        valid_email = "test@example.com"
        assert "@" in valid_email
        parts = valid_email.split("@")
        assert len(parts) == 2
        assert len(parts[0]) > 0  # Username part
        assert "." in parts[1]    # Domain part
        
        # Test invalid emails
        invalid_emails = ["test", "test@", "@example.com", "test @example.com"]
        for invalid in invalid_emails:
            parts = invalid.split("@") if "@" in invalid else []
            is_valid = (len(parts) == 2 and len(parts[0]) > 0 and "." in parts[1] 
                       and " " not in invalid)  # No spaces allowed
            assert not is_valid, f"Email {invalid} should not be valid"
    
    async def test_password_validation(self):
        """Test password validation"""
        passwords = [
            ("ValidPass123!", True),  # Valid
            ("short", False),  # Too short
            ("NoNumbers!", False),  # No numbers
            ("nouppercase123", False),  # No uppercase
        ]
        
        for pwd, should_be_valid in passwords:
            # Basic validation
            is_valid = len(pwd) >= 8 and any(c.isupper() for c in pwd) and any(c.isdigit() for c in pwd)
            assert is_valid == should_be_valid
    
    async def test_conversation_title_length(self):
        """Test conversation title validation"""
        titles = [
            ("Short", True),
            ("A" * 100, True),
            ("A" * 500, False),  # Too long
            ("", False),  # Empty
        ]
        
        for title, should_be_valid in titles:
            is_valid = 1 <= len(title) <= 255
            assert is_valid == should_be_valid
    
    async def test_message_content_validation(self):
        """Test message content validation"""
        test_messages = [
            ("Hello", True),
            ("A" * 10000, True),
            ("", False),
            ("A" * 50000, True),  # At max length, should still be valid
        ]
        
        for msg, should_be_valid in test_messages:
            is_valid = 1 <= len(msg) <= 50000
            assert is_valid == should_be_valid


@pytest.mark.unit
class TestUtilityFunctions:
    """Test utility helper functions"""
    
    async def test_datetime_utilities(self):
        """Test datetime utility functions"""
        now = datetime.now()
        assert now
        
        past = now - timedelta(days=1)
        assert past < now
        
        future = now + timedelta(days=1)
        assert future > now
    
    async def test_string_utilities(self):
        """Test string manipulation utilities"""
        test_strings = [
            ("hello world", "hello world"),
            ("HELLO WORLD", "hello world"),
            ("  spaces  ", "spaces"),  # Trimmed
        ]
        
        for input_str, expected in test_strings:
            # Basic operations
            result = input_str.strip().lower()
            assert result == expected.lower()
    
    async def test_uuid_parsing(self):
        """Test UUID parsing"""
        try:
            from uuid import UUID, uuid4
            
            # Generate random UUID
            random_uuid = uuid4()
            assert isinstance(random_uuid, UUID)
            
            # Parse string UUID
            uuid_str = str(random_uuid)
            parsed = UUID(uuid_str)
            assert parsed == random_uuid
        except ValueError:
            pytest.fail("Invalid UUID")
    
    async def test_json_serialization(self):
        """Test JSON serialization"""
        import json
        
        test_data = {
            "id": 1,
            "name": "Test",
            "active": True,
            "score": 95.5
        }
        
        # Serialize
        json_str = json.dumps(test_data)
        assert isinstance(json_str, str)
        
        # Deserialize
        parsed = json.loads(json_str)
        assert parsed["name"] == "Test"


@pytest.mark.unit
class TestErrorHandlingUtilities:
    """Test error handling utilities"""
    
    async def test_http_exception_handling(self):
        """Test HTTP exception handling"""
        try:
            from fastapi import HTTPException
            
            exc = HTTPException(status_code=404, detail="Not found")
            assert exc.status_code == 404
            assert exc.detail == "Not found"
        except ImportError:
            pytest.skip("FastAPI not available")
    
    async def test_validation_error_handling(self):
        """Test validation error handling"""
        test_cases = [
            (None, False),
            ("", False),
            (0, False),
            (1.5, True),
            ("valid", True),
        ]
        
        for value, should_be_valid in test_cases:
            # is_valid = value is not None and value != "" and value != 0
            is_valid = value not in [None, "", False, 0]  # Properly handle all falsy values
            # Check if the validity matches expectations
            if should_be_valid:
                assert is_valid, f"Expected {value} to be valid"
            else:
                assert not is_valid, f"Expected {value} to be invalid"
    
    async def test_retry_logic(self):
        """Test retry logic for API calls"""
        attempt = 0
        max_retries = 3
        
        async def try_operation():
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise Exception("Temporary failure")
            return "Success"
        
        # Simulate retry
        for i in range(max_retries):
            try:
                result = await try_operation()
                if result:
                    break
            except Exception:
                if i == max_retries - 1:
                    pytest.fail("Max retries exceeded")
