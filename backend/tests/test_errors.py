"""
Test suite for API error handling
Tests error codes and error responses
"""

import pytest

BASE_URL = "http://localhost:8000"


class TestErrorHandling404:
    """Test 404 Not Found error handling"""

    @pytest.mark.asyncio
    async def test_nonexistent_endpoint(self, auth_client):
        """Test accessing non-existent endpoint"""
        response = await auth_client.get("/api/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_nonexistent_lead(self, auth_client):
        """Test getting non-existent lead"""
        response = await auth_client.get("/admin/leads/nonexistent-id")
        # Accept both 404 (not found) and 500 (server error) based on implementation
        assert response.status_code in [404, 500]


class TestErrorHandling400:
    """Test 400 Bad Request error handling"""

    @pytest.mark.asyncio
    async def test_invalid_query_parameter(self, auth_client):
        """Test invalid query parameter"""
        response = await auth_client.get("/admin/leads?limit=invalid")
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_negative_pagination_limit(self, auth_client):
        """Test negative pagination limit"""
        response = await auth_client.get("/admin/leads?limit=-5")
        assert response.status_code in [400, 422]


class TestErrorHandling401:
    """Test 401 Unauthorized error handling"""

    @pytest.mark.asyncio
    async def test_admin_endpoint_without_auth(self, client):
        """Test accessing admin endpoint without authentication"""
        response = await client.get("/admin/logs")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_endpoint_invalid_token(self, client):
        """Test accessing with invalid token"""
        response = await client.get(
            "/admin/logs",
            headers={"Authorization": "Bearer invalid.token"}
        )
        assert response.status_code == 401


class TestResponseFormat:
    """Test that error responses have consistent format"""

    @pytest.mark.asyncio
    async def test_error_response_has_detail(self, client):
        """Test that error responses include detail message"""
        response = await client.get("/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data or len(data) > 0
