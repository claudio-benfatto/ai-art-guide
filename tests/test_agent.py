"""
Tests for RecommendationAgent.
"""

import pytest

from adk.agents import AgentResponse, RecommendationAgent
from adk.llm.providers import MockLLMProvider


class TestRecommendationAgent:
    """Tests for the recommendation agent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with mock LLM."""
        return RecommendationAgent(llm_provider=MockLLMProvider())
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.llm is not None
        assert isinstance(agent.llm, MockLLMProvider)
    
    def test_agent_default_llm(self):
        """Test agent uses default LLM provider from environment."""
        agent = RecommendationAgent()
        assert agent.llm is not None
    
    def test_process_query_returns_response(self, agent):
        """Test processing query returns AgentResponse."""
        response = agent.process_query("modern art")
        
        assert isinstance(response, AgentResponse)
        assert isinstance(response.message, str)
        assert isinstance(response.events_found, int)
        assert isinstance(response.event_ids, list)
        assert len(response.message) > 0
    
    def test_process_query_finds_events(self, agent):
        """Test query finds relevant events."""
        response = agent.process_query("photography")
        
        assert response.events_found > 0
        assert len(response.event_ids) > 0
        assert "photography" in response.message.lower() or "photo" in response.message.lower()
    
    def test_process_query_with_filters(self, agent):
        """Test query with explicit filters."""
        response = agent.process_query(
            "art events",
            filters={
                'tags': ["modern"],
                'geo_lat': 41.3851,
                'geo_lon': 2.1734,
                'geo_radius_km': 5.0
            }
        )
        
        assert response.events_found >= 0  # May or may not find results
        assert isinstance(response.message, str)
    
    def test_process_query_no_results(self, agent):
        """Test handling of no results."""
        response = agent.process_query(
            "very specific query that matches nothing xyz123",
            filters={'tags': ["nonexistent_tag"]}
        )
        
        assert response.events_found == 0
        assert len(response.event_ids) == 0
        assert "couldn't find" in response.message.lower()
    
    def test_process_query_max_results(self, agent):
        """Test max_results parameter."""
        response = agent.process_query("art", max_results=2)
        
        assert len(response.event_ids) <= 2
    
    def test_format_events_for_llm(self, agent):
        """Test event formatting for LLM context."""
        from adk.tools.retrieve_events import EventResult
        
        events = [
            EventResult(
                event_id="test_1",
                title="Test Event",
                description="A test description",
                tags=["modern", "photography"],
                start_date="2024-01-01",
                end_date="2024-01-31",
                category="exhibition",
                cost_bucket="free",
                venue_id="venue_1",
                venue_name="Test Venue",
                latitude=41.3851,
                longitude=2.1734,
                raw_score=0.95,
                distance_km=None
            )
        ]
        
        formatted = agent._format_events_for_llm(events)
        
        assert "Test Event" in formatted
        assert "modern" in formatted
        assert "photography" in formatted
        assert "0.950" in formatted
    
    def test_fallback_response(self, agent):
        """Test fallback response generation."""
        from adk.tools.retrieve_events import EventResult
        
        events = [
            EventResult(
                event_id="test_1",
                title="Test Exhibition",
                description="A test",
                tags=["modern"],
                start_date="2024-01-01",
                end_date="2024-01-31",
                category="exhibition",
                cost_bucket="free",
                venue_id="venue_1",
                venue_name="Test Venue",
                latitude=41.3851,
                longitude=2.1734,
                raw_score=0.95,
                distance_km=None
            )
        ]
        
        response = agent._generate_fallback_response("modern art", events)
        
        assert "Test Exhibition" in response
        assert "modern" in response
        assert len(response) > 0


class TestAgentEndToEnd:
    """End-to-end tests with real queries."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with mock LLM."""
        return RecommendationAgent(llm_provider=MockLLMProvider())
    
    def test_e2e_modern_art_query(self, agent):
        """Test complete flow for 'modern art' query."""
        response = agent.process_query("I'm interested in modern art exhibitions")
        
        assert response.events_found > 0
        assert len(response.event_ids) > 0
        assert "modern" in response.message.lower() or "exhibition" in response.message.lower()
        assert not response.degraded_mode  # Should succeed with mock LLM
    
    def test_e2e_photography_query(self, agent):
        """Test complete flow for photography query."""
        response = agent.process_query("Show me photography events")
        
        assert response.events_found > 0
        assert any("photo" in eid.lower() for eid in response.event_ids) or response.events_found > 0
    
    def test_e2e_family_query(self, agent):
        """Test complete flow for family-friendly query."""
        response = agent.process_query("What's good for families with kids?")
        
        assert response.events_found >= 0  # May or may not find family events
        assert isinstance(response.message, str)
    
    def test_e2e_location_based_query(self, agent):
        """Test query with location filter."""
        response = agent.process_query(
            "art near MACBA",
            filters={
                'geo_lat': 41.3830,
                'geo_lon': 2.1670,
                'geo_radius_km': 1.0
            }
        )
        
        assert isinstance(response, AgentResponse)
        # Should find events near MACBA coordinates
        if response.events_found > 0:
            assert len(response.event_ids) > 0
