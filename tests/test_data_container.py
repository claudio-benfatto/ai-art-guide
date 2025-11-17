"""Tests for DataContainer model and YAML loading/saving."""

import yaml
import pytest
from pydantic import ValidationError

from adk.models.schemas import DataContainer, Event, Venue


class TestDataContainerValidation:
    """Test DataContainer model validation."""
    
    def test_valid_data_container(self, valid_data_container_dict):
        """Test creating a valid data container."""
        container = DataContainer(**valid_data_container_dict)
        assert len(container.events) == 2
        assert len(container.venues) == 2
    
    def test_empty_data_container(self):
        """Test creating an empty data container."""
        container = DataContainer()
        assert container.events == []
        assert container.venues == []
    
    def test_referential_integrity_valid(self, valid_data_container_dict):
        """Test that valid venue references pass."""
        container = DataContainer(**valid_data_container_dict)
        # Should not raise
        assert container.events[0].venue_id == "v_01"
        assert container.events[1].venue_id == "v_02"
    
    def test_referential_integrity_invalid(self, valid_data_container_dict):
        """Test that invalid venue reference is caught."""
        valid_data_container_dict["events"][0]["venue_id"] = "v_99"  # Non-existent
        with pytest.raises(ValidationError) as exc_info:
            DataContainer(**valid_data_container_dict)
        assert "non-existent venue" in str(exc_info.value).lower()


class TestDataContainerUniqueness:
    """Test DataContainer uniqueness validation."""
    
    def test_duplicate_event_ids(self, valid_data_container_dict):
        """Test that duplicate event IDs are caught."""
        # Make both events have the same ID
        valid_data_container_dict["events"][1]["id"] = "evt_001"
        container = DataContainer(**valid_data_container_dict)
        
        with pytest.raises(ValueError) as exc_info:
            container.validate_uniqueness()
        assert "Duplicate event IDs" in str(exc_info.value)
        assert "evt_001" in str(exc_info.value)
    
    def test_duplicate_venue_ids(self, valid_data_container_dict):
        """Test that duplicate venue IDs are caught."""
        # Make both venues have the same ID
        # Also need to update event reference to avoid referential integrity error
        valid_data_container_dict["venues"][1]["id"] = "v_01"
        valid_data_container_dict["events"][1]["venue_id"] = "v_01"  # Update reference
        container = DataContainer(**valid_data_container_dict)
        
        with pytest.raises(ValueError) as exc_info:
            container.validate_uniqueness()
        assert "Duplicate venue IDs" in str(exc_info.value)
        assert "v_01" in str(exc_info.value)
    
    def test_unique_ids_pass(self, valid_data_container_dict):
        """Test that unique IDs pass validation."""
        container = DataContainer(**valid_data_container_dict)
        container.validate_uniqueness()  # Should not raise


class TestDataContainerQueryMethods:
    """Test DataContainer query methods."""
    
    def test_get_venue_by_id(self, valid_data_container_dict):
        """Test getting venue by ID."""
        container = DataContainer(**valid_data_container_dict)
        venue = container.get_venue_by_id("v_01")
        assert venue is not None
        assert venue.name == "MACBA - Museum of Contemporary Art"
    
    def test_get_venue_by_id_not_found(self, valid_data_container_dict):
        """Test getting non-existent venue."""
        container = DataContainer(**valid_data_container_dict)
        venue = container.get_venue_by_id("v_99")
        assert venue is None
    
    def test_get_event_by_id(self, valid_data_container_dict):
        """Test getting event by ID."""
        container = DataContainer(**valid_data_container_dict)
        event = container.get_event_by_id("evt_001")
        assert event is not None
        assert event.title_en == "Modern Photography Exhibition"
    
    def test_get_event_by_id_not_found(self, valid_data_container_dict):
        """Test getting non-existent event."""
        container = DataContainer(**valid_data_container_dict)
        event = container.get_event_by_id("evt_99")
        assert event is None
    
    def test_get_events_by_venue(self, valid_data_container_dict):
        """Test getting events by venue ID."""
        container = DataContainer(**valid_data_container_dict)
        events = container.get_events_by_venue("v_01")
        assert len(events) == 1
        assert events[0].id == "evt_001"
    
    def test_get_events_by_venue_no_events(self, valid_data_container_dict):
        """Test getting events for venue with no events."""
        # Add a venue with no events
        valid_data_container_dict["venues"].append({
            "id": "v_03",
            "name": "Empty Venue",
            "type": "gallery",
            "neighborhood": "Eixample",
            "latitude": 41.39,
            "longitude": 2.16
        })
        container = DataContainer(**valid_data_container_dict)
        events = container.get_events_by_venue("v_03")
        assert len(events) == 0
    
    def test_get_events_by_tag(self, valid_data_container_dict):
        """Test getting events by tag."""
        container = DataContainer(**valid_data_container_dict)
        events = container.get_events_by_tag("contemporary")
        assert len(events) == 2  # Both events have 'contemporary'
    
    def test_get_events_by_tag_not_found(self, valid_data_container_dict):
        """Test getting events by unused tag."""
        container = DataContainer(**valid_data_container_dict)
        events = container.get_events_by_tag("baroque")
        assert len(events) == 0


class TestDataContainerTagCoverage:
    """Test DataContainer tag coverage analysis."""
    
    def test_get_tag_coverage(self, valid_data_container_dict):
        """Test tag coverage calculation."""
        container = DataContainer(**valid_data_container_dict)
        coverage = container.get_tag_coverage()
        
        # Check that used tags have counts > 0
        assert coverage["modern"] == 1
        assert coverage["photography"] == 1
        assert coverage["contemporary"] == 2
        assert coverage["street"] == 1
        assert coverage["urban"] == 1
        
        # Check that unused tags have count 0
        assert coverage["baroque"] == 0
        assert coverage["renaissance"] == 0
    
    def test_tag_coverage_includes_all_vocabulary(self, valid_data_container_dict):
        """Test that tag coverage includes all controlled vocabulary."""
        from adk.models.schemas import CONTROLLED_VOCABULARY
        container = DataContainer(**valid_data_container_dict)
        coverage = container.get_tag_coverage()
        
        assert set(coverage.keys()) == CONTROLLED_VOCABULARY


class TestDataContainerSummary:
    """Test DataContainer summary generation."""
    
    def test_summary_output(self, valid_data_container_dict):
        """Test summary string generation."""
        container = DataContainer(**valid_data_container_dict)
        summary = container.summary()
        
        assert "Events: 2" in summary
        assert "Venues: 2" in summary
        assert "Tag Coverage:" in summary
        assert "Categories:" in summary
        assert "Cost Buckets:" in summary


class TestDataContainerYAMLLoading:
    """Test DataContainer YAML loading and saving."""
    
    def test_load_from_yaml(self, valid_data_container_dict, test_data_dir):
        """Test loading from YAML file."""
        yaml_file = test_data_dir / "test_events.yaml"
        
        # Save test data to YAML
        with open(yaml_file, 'w') as f:
            yaml.dump(valid_data_container_dict, f)
        
        # Load using DataContainer
        container = DataContainer.load_from_yaml(yaml_file)
        assert len(container.events) == 2
        assert len(container.venues) == 2
    
    def test_save_to_yaml(self, valid_data_container_dict, test_data_dir):
        """Test saving to YAML file."""
        container = DataContainer(**valid_data_container_dict)
        yaml_file = test_data_dir / "output_events.yaml"
        
        container.save_to_yaml(yaml_file)
        
        # Verify file exists and can be loaded
        assert yaml_file.exists()
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        assert "events" in data
        assert "venues" in data
        assert len(data["events"]) == 2
    
    def test_roundtrip_yaml(self, valid_data_container_dict, test_data_dir):
        """Test saving and loading produces same data."""
        container1 = DataContainer(**valid_data_container_dict)
        yaml_file = test_data_dir / "roundtrip.yaml"
        
        # Save and reload
        container1.save_to_yaml(yaml_file)
        container2 = DataContainer.load_from_yaml(yaml_file)
        
        # Compare
        assert len(container1.events) == len(container2.events)
        assert len(container1.venues) == len(container2.venues)
        assert container1.events[0].id == container2.events[0].id
        assert container1.events[0].title_en == container2.events[0].title_en
    
    def test_load_invalid_yaml(self, test_data_dir):
        """Test loading invalid YAML raises ValidationError."""
        yaml_file = test_data_dir / "invalid.yaml"
        
        # Create invalid YAML (event with bad ID)
        invalid_data = {
            "events": [{
                "id": "bad_id",  # Wrong format
                "title_en": "Test",
                "title_es": "Test",
                "description_en": "A" * 50,
                "description_es": "A" * 50,
                "tags": ["modern", "contemporary"],
                "category": "museum",
                "start_date": "2025-11-20",
                "end_date": "2026-01-15",
                "venue_id": "v_01",
                "cost_bucket": "mid",
                "outdoor": False,
                "latitude": 41.38,
                "longitude": 2.17,
                "source_type": "curated"
            }],
            "venues": [{
                "id": "v_01",
                "name": "Test Venue",
                "type": "museum",
                "neighborhood": "Test",
                "latitude": 41.38,
                "longitude": 2.17
            }]
        }
        
        with open(yaml_file, 'w') as f:
            yaml.dump(invalid_data, f)
        
        with pytest.raises(ValidationError) as exc_info:
            DataContainer.load_from_yaml(yaml_file)
        assert "String should match pattern" in str(exc_info.value)
