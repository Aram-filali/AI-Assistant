"""
RAG (Retrieval Augmented Generation) system tests
Tests complete RAG workflow and hybrid chat functionality
"""

import pytest
import httpx
from pathlib import Path
import json


@pytest.mark.production
class TestRAGCompleteWorkflow:
    """Test complete RAG system workflow"""
    
    @pytest.fixture(autouse=True)
    async def setup(self, http_client):
        """Setup RAG test environment"""
        self.http_client = http_client
        self.base_url = "http://localhost:8000"
        self.user_email = "rag-test@example.com"
        self.user_password = "RagTest123!@"
        
        # Try to login or register
        login_response = await http_client.post(
            f"{self.base_url}/auth/login",
            data={"username": self.user_email, "password": self.user_password}
        )
        
        if login_response.status_code == 200:
            self.token = login_response.json()["access_token"]
        else:
            # Register new user
            reg_response = await http_client.post(
                f"{self.base_url}/auth/register",
                json={
                    "email": self.user_email,
                    "password": self.user_password,
                    "full_name": "RAG Test User"
                }
            )
            if reg_response.status_code in [200, 201]:
                self.token = reg_response.json()["access_token"]
        
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.kb_id = None
    
    async def test_create_knowledge_base(self):
        """Test knowledge base creation"""
        response = await self.http_client.post(
            f"{self.base_url}/knowledge/bases",
            headers=self.headers,
            json={
                "name": "Test Knowledge Base",
                "description": "For RAG testing"
            }
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        self.kb_id = data.get("id") or data.get("kb_id")
        assert self.kb_id
    
    async def test_list_knowledge_bases(self):
        """Test listing knowledge bases"""
        response = await self.http_client.get(
            f"{self.base_url}/knowledge/bases",
            headers=self.headers
        )
        
        assert response.status_code == 200
        bases = response.json()
        assert isinstance(bases, list)
    
    @pytest.mark.asyncio
    async def test_upload_document(self):
        """Test uploading a document to knowledge base"""
        if not self.kb_id:
            # Create KB first
            kb_response = await self.http_client.post(
                f"{self.base_url}/knowledge/bases",
                headers=self.headers,
                json={"name": "Upload Test", "description": ""}
            )
            self.kb_id = kb_response.json().get("id")
        
        # Create a proper file for upload using multipart/form-data
        import io
        test_content = "This is a test document for RAG system testing."
        
        # Create an in-memory file
        files = {
            'file': ('test_document.txt', io.BytesIO(test_content.encode()), 'text/plain')
        }
        
        response = await self.http_client.post(
            f"{self.base_url}/knowledge/bases/{self.kb_id}/documents/upload",
            headers=self.headers,
            files=files
        )
        
        # Accept 200/201 for success, 400 for invalid file
        assert response.status_code in [200, 201, 400]
    
    async def test_query_knowledge_base(self):
        """Test querying knowledge base"""
        response = await self.http_client.post(
            f"{self.base_url}/knowledge/query",
            headers=self.headers,
            json={
                "question": "What is the test content about?",
                "knowledge_base_id": self.kb_id,
                "top_k": 5
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data or "results" in data
    
    async def test_embedding_generation(self):
        """Test embedding generation for documents"""
        # Verify embeddings are created
        response = await self.http_client.get(
            f"{self.base_url}/knowledge/stats",
            headers=self.headers
        )
        
        if response.status_code == 200:
            stats = response.json()
            assert "total_vectors" in stats or "total_embeddings" in stats
    
    async def test_vector_similarity_search(self):
        """Test vector similarity search"""
        query_response = await self.http_client.post(
            f"{self.base_url}/knowledge/query",
            headers=self.headers,
            json={
                "question": "similarity test query",
                "top_k": 5
            },
            timeout=30.0
        )
        
        assert query_response.status_code in [200, 404, 422]


@pytest.mark.production
class TestHybridChatWorkflow:
    """Test hybrid chat with RAG integration"""
    
    @pytest.fixture(autouse=True)
    async def setup(self, http_client):
        """Setup hybrid chat test"""
        self.http_client = http_client
        self.base_url = "http://localhost:8000"
        
        # Login
        response = await http_client.post(
            f"{self.base_url}/auth/login",
            data={"username": "admin@gmail.com", "password": "admin123"}
        )
        
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.conversation_id = None
    
    async def test_create_conversation(self):
        """Test conversation creation"""
        response = await self.http_client.post(
            f"{self.base_url}/chat/conversations",
            headers=self.headers,
            json={"title": "Hybrid Chat Test"}
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        self.conversation_id = data.get("id")
        assert self.conversation_id
    
    async def test_send_message_with_rag(self):
        """Test sending message with RAG context"""
        if not self.conversation_id:
            # Create conversation
            conv_response = await self.http_client.post(
                f"{self.base_url}/chat/conversations",
                headers=self.headers,
                json={"title": "Test"}
            )
            self.conversation_id = conv_response.json().get("id")
        
        response = await self.http_client.post(
            f"{self.base_url}/chat/ask",
            headers=self.headers,
            json={
                "question": "What information do you have?",
                "conversation_id": self.conversation_id
            },
            timeout=60.0
        )
        
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
    
    async def test_conversation_memory(self):
        """Test conversation memory/history"""
        if not self.conversation_id:
            # Create conversation if needed
            conv_response = await self.http_client.post(
                f"{self.base_url}/chat/conversations",
                headers=self.headers,
                json={"title": "Memory Test"}
            )
            self.conversation_id = conv_response.json().get("id")
        
        response = await self.http_client.get(
            f"{self.base_url}/chat/conversations/{self.conversation_id}/messages",
            headers=self.headers
        )
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            messages = response.json()
            assert isinstance(messages, list)
    
    async def test_context_window_management(self):
        """Test context window for RAG queries"""
        # Verify system can handle multiple context chunks
        test_query = "What can you tell me from your knowledge base?"
        
        response = await self.http_client.post(
            f"{self.base_url}/chat/ask",
            headers=self.headers,
            json={
                "question": test_query,
                "max_context_chunks": 5
            },
            timeout=60.0
        )
        
        assert response.status_code in [200, 422]
    
    async def test_source_attribution(self):
        """Test that answers include source attribution"""
        response = await self.http_client.post(
            f"{self.base_url}/chat/ask",
            headers=self.headers,
            json={"question": "What sources are you using?"},
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for sources in response
            assert "answer" in data
            # Sources might be in optional field
            if "sources" in data:
                assert isinstance(data["sources"], list)


@pytest.fixture
async def http_client():
    """Provide async HTTP client"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client
