"""
Tests for retrieve_events ADK Tool
Tests the tool wrapper and integration with retriever.
"""

from pathlib import Path

import pytest

from adk.tools.retrieve_events import (
    RetrieveEventsInput,
    retrieve_events,
)


EMBEDDINGS_PATH = Path(__file__).parent.parent / "data" / "embeddings_v1.json"


class TestRetrieveEventsTool:
    """Test the retrieve_events ADK tool."""
    
    @pytest.mark.skipif(not EMBEDDINGS_PATH.exists(), reason="Embeddings file not found")
    def test_basic_query(self):
        """Test basic query without filters."""
        input_data = RetrieveEventsInput(
            query_text="modern art",
            max_results=5
        )
        
        output = retrieve_events(input_data)
        
        assert output.total_found > 0
        assert len(output.events) <= 5
        assert output.query == "modern art"
        assert len(output.filters_applied) == 0
        
        # Check event structure
        for event in output.events:
            assert event.event_id
            assert event.title
            assert event.description
            assert len(event.tags) > 0
            assert event.category
            assert event.raw_score >= 0
    
    @pytest.mark.skipif(not EMBEDDINGS_PATH.exists(), reason="Embeddings file not found")
    def test_tag_filter(self):
        """Test query with tag filter."""
        input_data = RetrieveEventsInput(
            query_text="art exhibition",
            max_results=10,
            tags=["photography"]
        )
        
        output = retrieve_events(input_data)
        
        # All results should have photography tag
        for event in output.events:
            assert "photography" in event.tags
        
        # Filter should be recorded
        assert 'tags' in output.filters_applied
        assert output.filters_applied['tags'] == ["photography"]
    
    @pytest.mark.skipif(not EMBEDDINGS_PATH.exists(), reason="Embeddings file not found")
    def test_date_filter(self):
        """Test query with date range filter."""
        input_data = RetrieveEventsInput(
            query_text="art events",
            max_results=10,
            date_start="2025-11-20",
            date_end="2025-12-31"
        )
        
        output = retrieve_events(input_data)
        
        # Filter should be recorded
        assert 'date_range' in output.filters_applied
        assert output.filters_applied['date_range']['start'] == "2025-11-20"
        assert output.filters_applied['date_range']['end'] == "2025-12-31"
        
        # All events should be within date range
        for event in output.events:
            # Event should overlap with [2025-11-20, 2025-12-31]
            assert event.start_date <= "2025-12-31"
            assert event.end_date >= "2025-11-20"
    
    @pytest.mark.skipif(not EMBEDDINGS_PATH.exists(), reason="Embeddings file not found")
    def test_geo_filter(self):
        """Test query with geographic filter."""
        input_data = RetrieveEventsInput(
            query_text="galleries",
            max_results=10,
            geo_lat=41.3851,  # Plaça Catalunya
            geo_lon=2.1734,
            geo_radius_km=3.0
        )
        
        output = retrieve_events(input_data)
        
        # Filter should be recorded
        assert 'geo' in output.filters_applied
        assert output.filters_applied['geo']['lat'] == 41.3851
        assert output.filters_applied['geo']['lon'] == 2.1734
        assert output.filters_applied['geo']['radius_km'] == 3.0
        
        # All events should have distance_km populated
        for event in output.events:
            assert event.distance_km is not None
            assert event.distance_km <= 3.0
    
    @pytest.mark.skipif(not EMBEDDINGS_PATH.exists(), reason="Embeddings file not found")
    def test_combined_filters(self):
        """Test query with multiple filters."""
        input_data = RetrieveEventsInput(
            query_text="modern photography",
            max_results=5,
            tags=["photography", "modern"],
            date_start="2025-11-01",
            date_end="2026-02-01",
            geo_lat=41.3851,
            geo_lon=2.1734,
            geo_radius_km=5.0
        )
        
        output = retrieve_events(input_data)
        
        # All filters should be recorded
        assert 'tags' in output.filters_applied
        assert 'date_range' in output.filters_applied
        assert 'geo' in output.filters_applied
        
        # Validate results
        for event in output.events:
            # Tag filter (any match)
            assert any(tag in event.tags for tag in ["photography", "modern"])
            
            # Date filter (overlap)
            assert event.start_date <= "2026-02-01"
            assert event.end_date >= "2025-11-01"
            
            # Geo filter
            assert event.distance_km is not None
            assert event.distance_km <= 5.0
    
    @pytest.mark.skipif(not EMBEDDINGS_PATH.exists(), reason="Embeddings file not found")
    def test_max_results_limit(self):
        """Test that max_results is respected."""
        input_data = RetrieveEventsInput(
            query_text="art",
            max_results=3
        )
        
        output = retrieve_events(input_data)
        assert len(output.events) <= 3
    
    @pytest.mark.skipif(not EMBEDDINGS_PATH.exists(), reason="Embeddings file not found")
    def test_empty_results(self):
        """Test handling of filters that match nothing."""
        input_data = RetrieveEventsInput(
            query_text="art",
            max_results=10,
            tags=["nonexistent_tag_xyz"]
        )
        
        output = retrieve_events(input_data)
        assert output.total_found == 0
        assert len(output.events) == 0
    
    @pytest.mark.skipif(not EMBEDDINGS_PATH.exists(), reason="Embeddings file not found")
    def test_results_sorted_by_score(self):
        """Test that results are sorted by raw_score descending."""
        input_data = RetrieveEventsInput(
            query_text="contemporary art",
            max_results=5
        )
        
        output = retrieve_events(input_data)
        
        if len(output.events) > 1:
            scores = [event.raw_score for event in output.events]
            assert scores == sorted(scores, reverse=True), "Events should be sorted by score descending"


class TestToolSuccessMetric:
    """Test Day 4 success metric."""
    
    @pytest.mark.skipif(not EMBEDDINGS_PATH.exists(), reason="Embeddings file not found")
    def test_modern_query_success_metric(self):
        """
        Day 4 Success Metric: Query 'modern' returns modern-tag events in top-3.
        """
        input_data = RetrieveEventsInput(
            query_text="modern",
            max_results=3
        )
        
        output = retrieve_events(input_data)
        
        assert output.total_found > 0, "Should find at least one event"
        assert len(output.events) > 0, "Should return at least one event"
        
        # Check if any of the top-3 results have 'modern' tag
        top_3_tags = [tag for event in output.events[:3] for tag in event.tags]
        assert "modern" in top_3_tags, "Expected 'modern' tag in top-3 results"
        
        print(f"\n✅ Day 4 Success Metric PASSED")
        print(f"   Query: 'modern'")
        print(f"   Total found: {output.total_found}")
        print(f"   Top-3 events:")
        for i, event in enumerate(output.events[:3], 1):
            print(f"   {i}. {event.title}")
            print(f"      Tags: {', '.join(event.tags)}")
            print(f"      Score: {event.raw_score:.3f}")
