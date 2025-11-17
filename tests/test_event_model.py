"""Tests for Event Pydantic model."""

from datetime import date

import pytest
from pydantic import ValidationError

from adk.models.schemas import Event


class TestEventValidation:
    """Test Event model validation."""
    
    def test_valid_event(self, valid_event_data):
        """Test creating a valid event."""
        event = Event(**valid_event_data)
        assert event.id == "evt_001"
        assert event.title_en == "Modern Photography Exhibition"
        assert event.cost_bucket == "mid"
        assert event.outdoor is False
    
    def test_event_with_optional_fields(self, valid_event_data):
        """Test event with optional fields."""
        valid_event_data.update({
            "domain": "visual-art",
            "accessibility_notes": "Wheelchair accessible",
            "booking_url": "https://example.com/book"
        })
        event = Event(**valid_event_data)
        assert event.domain == "visual-art"
        assert event.accessibility_notes == "Wheelchair accessible"
        assert event.booking_url == "https://example.com/book"
    
    def test_event_with_unknown_values(self, valid_event_data):
        """Test event with unknown values."""
        valid_event_data.update({
            "start_date": "unknown",
            "end_date": "unknown",
            "cost_bucket": "unknown",
            "outdoor": "unknown",
            "booking_url": "unknown"
        })
        event = Event(**valid_event_data)
        assert event.start_date == "unknown"
        assert event.end_date == "unknown"
        assert event.cost_bucket == "unknown"
        assert event.outdoor == "unknown"
        assert event.booking_url == "unknown"


class TestEventIDValidation:
    """Test Event ID validation."""
    
    def test_invalid_id_format(self, valid_event_data):
        """Test that invalid ID format is rejected."""
        valid_event_data["id"] = "event_001"  # Wrong format
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "String should match pattern" in str(exc_info.value)
    
    def test_invalid_id_no_number(self, valid_event_data):
        """Test that ID without number is rejected."""
        valid_event_data["id"] = "evt_"
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "String should match pattern" in str(exc_info.value)


class TestEventStringValidation:
    """Test Event string field validation."""
    
    def test_title_too_short(self, valid_event_data):
        """Test that short title is rejected."""
        valid_event_data["title_en"] = "Art"  # < 5 chars
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "at least 5 characters" in str(exc_info.value)
    
    def test_title_too_long(self, valid_event_data):
        """Test that long title is rejected."""
        valid_event_data["title_en"] = "A" * 201  # > 200 chars
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "at most 200 characters" in str(exc_info.value)
    
    def test_description_too_short(self, valid_event_data):
        """Test that short description is rejected."""
        valid_event_data["description_en"] = "Short description."  # < 50 chars
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "at least 50 characters" in str(exc_info.value)
    
    def test_description_too_long(self, valid_event_data):
        """Test that long description is rejected."""
        valid_event_data["description_en"] = "A" * 1001  # > 1000 chars
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "at most 1000 characters" in str(exc_info.value)


class TestEventTagsValidation:
    """Test Event tags validation."""
    
    def test_tags_too_few(self, valid_event_data):
        """Test that < 2 tags is rejected."""
        valid_event_data["tags"] = ["modern"]
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "at least 2 items" in str(exc_info.value)
    
    def test_tags_too_many(self, valid_event_data):
        """Test that > 6 tags is rejected."""
        valid_event_data["tags"] = ["modern", "contemporary", "photography", 
                                     "painting", "sculpture", "installation", "digital"]
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "at most 6 items" in str(exc_info.value)
    
    def test_invalid_tag(self, valid_event_data):
        """Test that invalid tag is rejected."""
        valid_event_data["tags"] = ["modern", "invalid_tag"]
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "not in controlled vocabulary" in str(exc_info.value)
        assert "invalid_tag" in str(exc_info.value)


class TestEventCategoryValidation:
    """Test Event category validation."""
    
    @pytest.mark.parametrize("category", [
        "gallery", "museum", "street", "pop-up", "opening", "cultural-center"
    ])
    def test_valid_categories(self, valid_event_data, category):
        """Test all valid category values."""
        valid_event_data["category"] = category
        event = Event(**valid_event_data)
        assert event.category == category
    
    def test_invalid_category(self, valid_event_data):
        """Test that invalid category is rejected."""
        valid_event_data["category"] = "invalid"
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "Input should be" in str(exc_info.value)


class TestEventDomainValidation:
    """Test Event domain validation."""
    
    @pytest.mark.parametrize("domain", [
        "visual-art", "music", "theatre", "cinema", "multi"
    ])
    def test_valid_domains(self, valid_event_data, domain):
        """Test all valid domain values."""
        valid_event_data["domain"] = domain
        event = Event(**valid_event_data)
        assert event.domain == domain
    
    def test_invalid_domain(self, valid_event_data):
        """Test that invalid domain is rejected."""
        valid_event_data["domain"] = "sports"
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "Input should be" in str(exc_info.value)
    
    def test_domain_optional(self, valid_event_data):
        """Test that domain is optional."""
        event = Event(**valid_event_data)
        assert event.domain is None


class TestEventDateValidation:
    """Test Event date validation."""
    
    def test_valid_dates(self, valid_event_data):
        """Test valid date range."""
        event = Event(**valid_event_data)
        assert event.start_date == date(2025, 11, 20)
        assert event.end_date == date(2026, 1, 15)
    
    def test_end_before_start(self, valid_event_data):
        """Test that end_date before start_date is rejected."""
        valid_event_data["start_date"] = date(2026, 1, 15)
        valid_event_data["end_date"] = date(2025, 11, 20)
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "must be <=" in str(exc_info.value)
    
    def test_same_date(self, valid_event_data):
        """Test that same start and end date is valid."""
        same_date = date(2025, 11, 20)
        valid_event_data["start_date"] = same_date
        valid_event_data["end_date"] = same_date
        event = Event(**valid_event_data)
        assert event.start_date == event.end_date
    
    def test_unknown_dates(self, valid_event_data):
        """Test that unknown dates don't trigger ordering check."""
        valid_event_data["start_date"] = "unknown"
        valid_event_data["end_date"] = "unknown"
        event = Event(**valid_event_data)
        assert event.start_date == "unknown"
        assert event.end_date == "unknown"
    
    def test_mixed_unknown_date(self, valid_event_data):
        """Test that mixed known/unknown dates are valid."""
        valid_event_data["start_date"] = date(2025, 11, 20)
        valid_event_data["end_date"] = "unknown"
        event = Event(**valid_event_data)
        assert isinstance(event.start_date, date)
        assert event.end_date == "unknown"


class TestEventCostValidation:
    """Test Event cost_bucket validation."""
    
    @pytest.mark.parametrize("cost", ["free", "low", "mid", "high", "unknown"])
    def test_valid_cost_buckets(self, valid_event_data, cost):
        """Test all valid cost bucket values."""
        valid_event_data["cost_bucket"] = cost
        event = Event(**valid_event_data)
        assert event.cost_bucket == cost
    
    def test_invalid_cost_bucket(self, valid_event_data):
        """Test that invalid cost bucket is rejected."""
        valid_event_data["cost_bucket"] = "expensive"
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "Input should be" in str(exc_info.value)


class TestEventOutdoorValidation:
    """Test Event outdoor field validation."""
    
    def test_outdoor_true(self, valid_event_data):
        """Test outdoor = true."""
        valid_event_data["outdoor"] = True
        event = Event(**valid_event_data)
        assert event.outdoor is True
    
    def test_outdoor_false(self, valid_event_data):
        """Test outdoor = false."""
        valid_event_data["outdoor"] = False
        event = Event(**valid_event_data)
        assert event.outdoor is False
    
    def test_outdoor_unknown(self, valid_event_data):
        """Test outdoor = unknown."""
        valid_event_data["outdoor"] = "unknown"
        event = Event(**valid_event_data)
        assert event.outdoor == "unknown"
    
    def test_outdoor_invalid(self, valid_event_data):
        """Test that invalid outdoor value is rejected."""
        valid_event_data["outdoor"] = "maybe"
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "Input should be" in str(exc_info.value) or "unable to interpret" in str(exc_info.value)


class TestEventCoordinatesValidation:
    """Test Event coordinates validation."""
    
    def test_valid_coordinates(self, valid_event_data):
        """Test valid Barcelona coordinates."""
        event = Event(**valid_event_data)
        assert event.latitude == 41.3851
        assert event.longitude == 2.1734
    
    def test_latitude_too_low(self, valid_event_data):
        """Test latitude below Barcelona bounds."""
        valid_event_data["latitude"] = 41.29  # Below 41.30
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "greater than or equal to" in str(exc_info.value)
    
    def test_latitude_too_high(self, valid_event_data):
        """Test latitude above Barcelona bounds."""
        valid_event_data["latitude"] = 41.51  # Above 41.50
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "less than or equal to" in str(exc_info.value)
    
    def test_longitude_too_low(self, valid_event_data):
        """Test longitude below Barcelona bounds."""
        valid_event_data["longitude"] = 1.99  # Below 2.00
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "greater than or equal to" in str(exc_info.value)
    
    def test_longitude_too_high(self, valid_event_data):
        """Test longitude above Barcelona bounds."""
        valid_event_data["longitude"] = 2.31  # Above 2.30
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "less than or equal to" in str(exc_info.value)


class TestEventSourceTypeValidation:
    """Test Event source_type validation."""
    
    @pytest.mark.parametrize("source", ["curated", "external"])
    def test_valid_source_types(self, valid_event_data, source):
        """Test valid source_type values."""
        valid_event_data["source_type"] = source
        event = Event(**valid_event_data)
        assert event.source_type == source
    
    def test_invalid_source_type(self, valid_event_data):
        """Test that invalid source_type is rejected."""
        valid_event_data["source_type"] = "scraped"
        with pytest.raises(ValidationError) as exc_info:
            Event(**valid_event_data)
        assert "Input should be" in str(exc_info.value)
