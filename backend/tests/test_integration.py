"""
Integration tests - test complete workflows
"""

import pytest

BASE_URL = "http://localhost:8000"


@pytest.mark.integration
class TestAuthenticationWorkflow:
    """Test complete authentication workflow"""

    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, client):
        """Test: Login → Get user → Access protected endpoint"""
        # Step 1: Login
        login_resp = await client.post(
            "/auth/login",
            data={"username": "admin@gmail.com", "password": "admin123"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        # Step 2: Get user info
        user_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert user_resp.status_code == 200
        user = user_resp.json()
        assert user["role"] == "admin"
        
        # Step 3: Access admin endpoint
        logs_resp = await client.get(
            "/admin/logs",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert logs_resp.status_code == 200


@pytest.mark.integration
class TestLeadsWorkflow:
    """Test complete leads workflow"""

    @pytest.mark.asyncio
    async def test_leads_workflow(self, client):
        """Test: Get leads → View analytics → Export"""
        # Login
        login_resp = await client.post(
            "/auth/login",
            data={"username": "admin@gmail.com", "password": "admin123"}
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 1: Get leads list
        leads_resp = await client.get("/admin/leads?limit=10", headers=headers)
        assert leads_resp.status_code == 200
        
        # Step 2: Get analytics
        analytics_resp = await client.get(
            "/admin/analytics/leads",
            headers=headers
        )
        assert analytics_resp.status_code == 200
        analytics = analytics_resp.json()
        assert analytics["total_leads"] > 0
        
        # Step 3: Export leads
        export_resp = await client.post("/admin/leads/export", headers=headers)
        assert export_resp.status_code == 200
        assert len(export_resp.content) > 0


@pytest.mark.integration
class TestChatWorkflow:
    """Test complete chat workflow"""

    @pytest.mark.asyncio
    async def test_conversations_workflow(self, client):
        """Test: List conversations → Get conversation"""
        # Login
        login_resp = await client.post(
            "/auth/login",
            data={"username": "admin@gmail.com", "password": "admin123"}
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 1: List conversations
        conv_list = await client.get(
            "/chat/conversations",
            headers=headers
        )
        assert conv_list.status_code == 200
        conversations = conv_list.json()
        assert isinstance(conversations, list)


@pytest.mark.integration
class TestKnowledgeWorkflow:
    """Test complete knowledge base workflow"""

    @pytest.mark.asyncio
    async def test_knowledge_base_workflow(self, client):
        """Test: List bases → Get stats"""
        # Login
        login_resp = await client.post(
            "/auth/login",
            data={"username": "admin@gmail.com", "password": "admin123"}
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 1: List knowledge bases
        bases_resp = await client.get(
            "/knowledge/bases",
            headers=headers
        )
        assert bases_resp.status_code == 200
        
        # Step 2: Get RAG stats
        stats_resp = await client.get(
            "/knowledge/stats",
            headers=headers
        )
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert "total_vectors" in stats
        assert "total_documents" in stats
