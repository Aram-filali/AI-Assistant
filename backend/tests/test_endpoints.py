"""
Test suite for API endpoints
Tests main functionality of each endpoint
"""

import pytest

BASE_URL = "http://localhost:8000"


class TestLeadsEndpoints:
    """Test /admin/leads endpoints"""

    @pytest.mark.asyncio
    async def test_get_leads_returns_list(self, auth_client):
        """Test that GET /admin/leads returns a list"""
        response = await auth_client.get("/admin/leads")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_get_leads_pagination(self, auth_client):
        """Test pagination parameters"""
        response = await auth_client.get("/admin/leads?skip=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 5

    @pytest.mark.asyncio
    async def test_get_leads_with_search(self, auth_client):
        """Test search parameter"""
        response = await auth_client.get("/admin/leads?search=test")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_leads_with_status_filter(self, auth_client):
        """Test status filter"""
        response = await auth_client.get("/admin/leads?status=NEW")
        assert response.status_code == 200


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""

    @pytest.mark.asyncio
    async def test_get_analytics_leads(self, auth_client):
        """Test GET /admin/analytics/leads"""
        response = await auth_client.get("/admin/analytics/leads")
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "conversion_rate" in data

    @pytest.mark.asyncio
    async def test_analytics_returns_numbers(self, auth_client):
        """Test that analytics returns numeric values"""
        response = await auth_client.get("/admin/analytics/leads")
        data = response.json()
        assert isinstance(data["total_leads"], int)
        assert isinstance(data["leads_with_email"], int)


class TestActivityLogsEndpoints:
    """Test activity logs endpoints"""

    @pytest.mark.asyncio
    async def test_get_activity_logs(self, auth_client):
        """Test GET /admin/logs"""
        response = await auth_client.get("/admin/logs")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_activity_logs_pagination(self, auth_client):
        """Test activity logs pagination"""
        response = await auth_client.get("/admin/logs?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10


class TestChatEndpoints:
    """Test chat endpoints"""

    @pytest.mark.asyncio
    async def test_list_conversations(self, auth_client):
        """Test GET /chat/conversations"""
        response = await auth_client.get("/chat/conversations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_conversation(self, auth_client):
        """Test POST /chat/conversations"""
        response = await auth_client.post(
            "/chat/conversations",
            json={"title": "Test Conversation"}
        )
        assert response.status_code in [200, 201]


class TestKnowledgeEndpoints:
    """Test knowledge base endpoints"""

    @pytest.mark.asyncio
    async def test_list_knowledge_bases(self, auth_client):
        """Test GET /knowledge/bases"""
        response = await auth_client.get("/knowledge/bases")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_rag_stats(self, auth_client):
        """Test GET /knowledge/stats"""
        response = await auth_client.get("/knowledge/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_vectors" in data
        assert "total_documents" in data


class TestExportEndpoints:
    """Test export endpoints"""

    @pytest.mark.asyncio
    async def test_export_leads_csv(self, auth_client):
        """Test POST /admin/leads/export"""
        response = await auth_client.post("/admin/leads/export")
        assert response.status_code == 200
        assert len(response.content) > 0
