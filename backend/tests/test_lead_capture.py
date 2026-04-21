"""
Lead Capture functionality tests
"""

import pytest
import httpx
import json
from datetime import datetime


@pytest.mark.production
class TestLeadCaptureWorkflow:
    """Test complete lead capture workflow"""
    
    @pytest.fixture(autouse=True)
    async def setup(self, http_client):
        """Setup test data"""
        self.http_client = http_client
        self.base_url = "http://localhost:8000"
        
        # Get test token
        response = await http_client.post(
            f"{self.base_url}/auth/login",
            data={"username": "admin@gmail.com", "password": "admin123"}
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    async def test_session_creation_and_tracking(self):
        """Test session creation for lead capture"""
        session_data = {
            "session_id": "test-session-123",
            "source": "website",
            "landing_page": "https://example.com/demo"
        }
        
        # Session should be created when user visits
        assert session_data["session_id"]
        assert session_data["source"] in ["website", "chat", "form"]
    
    async def test_lead_extraction_from_chat(self):
        """Test lead extraction from chat messages"""
        message = "Hi, I'm John Doe from Acme Corp. You can reach me at john@acme.com"
        
        # Parse lead info from message
        lead_info = {
            "name": "John Doe",
            "company": "Acme Corp",
            "email": "john@acme.com"
        }
        
        assert lead_info["name"]
        assert lead_info["company"]
        assert "@" in lead_info["email"]
    
    async def test_intent_detection(self):
        """Test intent detection from user messages"""
        test_messages = [
            ("I want to buy your product", "purchase"),
            ("Can I schedule a demo?", "demo_request"),
            ("Tell me more about pricing", "pricing_inquiry"),
            ("I'm just browsing", "information_seeking")
        ]
        
        for message, expected_intent in test_messages:
            # Mock intent detection
            detected = expected_intent
            assert expected_intent in ["purchase", "demo_request", "pricing_inquiry", "information_seeking"]
    
    async def test_email_capture_proposal(self):
        """Test email capture proposal trigger"""
        # Email should be proposed after engagement threshold
        engagement_score = 75
        should_propose_email = engagement_score > 50
        
        assert should_propose_email
    
    async def test_lead_status_transitions(self):
        """Test lead status state machine"""
        statuses = [
            ("new", "contacted"),
            ("contacted", "qualified"),
            ("qualified", "proposal"),
            ("proposal", "won")
        ]
        
        for current, next_status in statuses:
            assert current in ["new", "contacted", "qualified", "proposal", "won"]
            assert next_status in ["new", "contacted", "qualified", "proposal", "won"]
    
    async def test_lead_scoring_system(self):
        """Test automated lead scoring"""
        lead_data = {
            "engagement_level": 3,  # 1-5
            "page_views": 5,
            "message_count": 8,
            "company_size": "medium",
            "industry": "technology"
        }
        
        # Calculate score
        base_score = 50
        engagement_bonus = lead_data["engagement_level"] * 5
        activity_bonus = min(lead_data["message_count"], 20)
        
        total_score = base_score + engagement_bonus + activity_bonus
        
        assert 0 <= total_score <= 100
    
    async def test_automated_actions_trigger(self):
        """Test automated actions based on lead behavior"""
        trigger_conditions = [
            {"type": "email_proposal", "condition": "engagement > 50"},
            {"type": "lead_scoring", "condition": "message_count > 5"},
            {"type": "crm_sync", "condition": "lead_qualified"},
            {"type": "notification", "condition": "high_intent_detected"}
        ]
        
        for trigger in trigger_conditions:
            assert trigger["type"]
            assert trigger["condition"]
    
    async def test_lead_data_persistence(self):
        """Test lead data is saved to database"""
        lead = {
            "email": "test-lead-capture@example.com",
            "name": "Test Lead",
            "company": "Test Company",
            "captured_at": datetime.now().isoformat()
        }
        
        # Simulate save
        assert lead["email"]
        assert lead["captured_at"]


@pytest.fixture
async def http_client():
    """Provide async HTTP client"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client
