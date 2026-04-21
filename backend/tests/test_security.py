"""
Test suite for security and permissions
Tests access control, data isolation, and security issues
"""

import pytest

BASE_URL = "http://localhost:8000"


class TestAccessControl:
    """Test access control and permissions"""

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_admin_logs(self, client):
        """Test that unauthenticated users cannot access admin logs"""
        response = await client.get("/admin/logs")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_leads(self, client):
        """Test that unauthenticated users cannot access leads"""
        response = await client.get("/admin/leads")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticated_can_access_logs(self, auth_client):
        """Test that authenticated admin can access logs"""
        response = await auth_client.get("/admin/logs")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_authenticated_can_access_leads(self, auth_client):
        """Test that authenticated admin can access leads"""
        response = await auth_client.get("/admin/leads")
        assert response.status_code == 200


class TestInputValidation:
    """Test that inputs are properly validated"""

    @pytest.mark.asyncio
    async def test_sql_injection_in_search(self, auth_client):
        """Test that SQL injection is prevented in search"""
        response = await auth_client.get(
            "/admin/leads?search=' OR '1'='1"
        )
        assert response.status_code in [200, 400, 422]
        assert "sql" not in response.text.lower()

    @pytest.mark.asyncio
    async def test_xss_prevention(self, auth_client):
        """Test that XSS payloads are handled"""
        response = await auth_client.get(
            "/admin/leads?search=<script>alert('xss')</script>"
        )
        assert response.status_code in [200, 400]


class TestSensitiveDataExposure:
    """Test that sensitive data is not exposed"""

    @pytest.mark.asyncio
    async def test_password_not_in_user_response(self, auth_client):
        """Test that password is never returned"""
        response = await auth_client.get("/auth/me")
        assert response.status_code == 200
        user_data = response.json()
        assert "password" not in user_data
        assert "hash" not in str(user_data).lower()

    @pytest.mark.asyncio
    async def test_error_messages_dont_reveal_internals(self, client):
        """Test that error messages don't reveal system internals"""
        response = await client.post(
            "/auth/login",
            data={"username": "admin@gmail.com", "password": "wrong"}
        )
        error_text = response.text.lower()
        assert "table" not in error_text
        assert "database" not in error_text
