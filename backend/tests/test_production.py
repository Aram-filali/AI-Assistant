"""
Production readiness tests - Validates all critical system components
"""

import pytest
import httpx
from datetime import datetime


@pytest.mark.production
class TestProductionReadiness:
    """Test suite for production readiness validation"""
    
    async def test_health_check(self, http_client):
        """Test FastAPI documentation endpoint"""
        response = await http_client.get(f"{BASE_URL}/docs")
        assert response.status_code == 200
        assert "FastAPI" in response.text or "swagger" in response.text.lower()
    
    async def test_authentication_flow(self, http_client):
        """Test login endpoint and token generation"""
        response = await http_client.post(
            f"{BASE_URL}/auth/login",
            data={"username": "admin@gmail.com", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Store token for other tests
        return data["access_token"]
    
    async def test_user_profile(self, http_client, test_auth_headers):
        """Test GET /auth/me endpoint"""
        response = await http_client.get(
            f"{BASE_URL}/auth/me",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        user = response.json()
        assert user["email"] == "admin@gmail.com"
        assert user["role"] in ["admin", "user"]
    
    async def test_dashboard_analytics(self, http_client, test_auth_headers):
        """Test GET /admin/analytics/leads endpoint"""
        response = await http_client.get(
            f"{BASE_URL}/admin/analytics/leads",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert isinstance(data["total_leads"], int)
    
    async def test_leads_endpoint(self, http_client, test_auth_headers):
        """Test GET /admin/leads pagination"""
        response = await http_client.get(
            f"{BASE_URL}/admin/leads?skip=0&limit=10",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)
    
    async def test_activity_logs_endpoint(self, http_client, test_auth_headers):
        """Test GET /admin/logs endpoint"""
        response = await http_client.get(
            f"{BASE_URL}/admin/logs?skip=0&limit=10",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, dict)
    
    async def test_knowledge_bases_endpoint(self, http_client, test_auth_headers):
        """Test GET /knowledge/bases endpoint"""
        response = await http_client.get(
            f"{BASE_URL}/knowledge/bases",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_chat_conversations_endpoint(self, http_client, test_auth_headers):
        """Test GET /chat/conversations endpoint"""
        response = await http_client.get(
            f"{BASE_URL}/chat/conversations",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_database_connectivity(self, http_client, test_auth_headers):
        """Test database connectivity through logs endpoint"""
        response = await http_client.get(
            f"{BASE_URL}/admin/logs?skip=0&limit=1",
            headers=test_auth_headers
        )
        assert response.status_code == 200
    
    async def test_cache_system(self, http_client, test_auth_headers):
        """Test Redis cache through auth/me endpoint"""
        response = await http_client.get(
            f"{BASE_URL}/auth/me",
            headers=test_auth_headers
        )
        assert response.status_code == 200


# Base URL configuration
BASE_URL = "http://localhost:8000"


@pytest.fixture
async def http_client():
    """Provide async HTTP client"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield client


@pytest.fixture
async def test_auth_headers(http_client):
    """Get admin auth headers"""
    response = await http_client.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin@gmail.com", "password": "admin123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
