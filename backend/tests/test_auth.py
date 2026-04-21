"""
Test suite for authentication endpoints
Tests both happy path and error cases
"""

import pytest

BASE_URL = "http://localhost:8000"


class TestAuthenticationHappyPath:
    """Test valid authentication scenarios"""

    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, client):
        """Test login with valid admin credentials"""
        response = await client.post(
            "/auth/login",
            data={
                "username": "admin@gmail.com",
                "password": "admin123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, client):
        """Test getting current user with valid token"""
        # First login
        login_resp = await client.post(
            "/auth/login",
            data={"username": "admin@gmail.com", "password": "admin123"}
        )
        token = login_resp.json()["access_token"]
        
        # Then get user
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        user = response.json()
        assert user["email"] == "admin@gmail.com"
        assert user["role"] == "admin"


class TestAuthenticationErrorCases:
    """Test authentication error scenarios"""

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, client):
        """Test login with non-existent email"""
        response = await client.post(
            "/auth/login",
            data={
                "username": "nonexistent@gmail.com",
                "password": "anypassword"
            }
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        """Test login with wrong password"""
        response = await client.post(
            "/auth/login",
            data={
                "username": "admin@gmail.com",
                "password": "wrongpassword123"
            }
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_empty_credentials(self, client):
        """Test login with empty email and password"""
        response = await client.post(
            "/auth/login",
            data={
                "username": "",
                "password": ""
            }
        )
        assert response.status_code in [400, 401, 422]

    @pytest.mark.asyncio
    async def test_get_user_without_token(self, client):
        """Test accessing /auth/me without token"""
        response = await client.get("/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_invalid_token(self, client):
        """Test accessing /auth/me with invalid token"""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401


class TestAuthenticationEdgeCases:
    """Test edge cases in authentication"""

    @pytest.mark.asyncio
    async def test_login_sql_injection_attempt(self, client):
        """Test that SQL injection is prevented"""
        response = await client.post(
            "/auth/login",
            data={
                "username": "' OR '1'='1",
                "password": "' OR '1'='1"
            }
        )
        assert response.status_code != 200
        assert "sql" not in response.text.lower()

    @pytest.mark.asyncio
    async def test_bearer_prefix_required(self, client):
        """Test that 'Bearer' prefix is required"""
        # Get valid token first
        login_resp = await client.post(
            "/auth/login",
            data={"username": "admin@gmail.com", "password": "admin123"}
        )
        token = login_resp.json()["access_token"]
        
        # Try without 'Bearer' prefix
        response = await client.get(
            "/auth/me",
            headers={"Authorization": token}
        )
        assert response.status_code == 401
