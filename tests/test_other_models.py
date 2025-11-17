"""Tests for Venue, UserProfile, and EmbeddingDoc Pydantic models."""

import pytest
from pydantic import ValidationError

from adk.models.schemas import Venue, UserProfile, EmbeddingDoc


class TestVenueValidation:
    """Test Venue model validation."""
    
    def test_valid_venue(self, valid_venue_data):
        """Test creating a valid venue."""
        venue = Venue(**valid_venue_data)
        assert venue.id == "v_01"
        assert venue.name == "MACBA - Museum of Contemporary Art"
        assert venue.type == "museum"
    
    def test_venue_with_optional_fields(self, valid_venue_data):
        """Test venue with optional fields."""
        valid_venue_data.update({
            "opening_hours": "Tue-Sun 10:00-19:00",
            "accessibility_notes": "Wheelchair accessible",
            "url": "https://www.macba.cat"
        })
        venue = Venue(**valid_venue_data)
        assert venue.opening_hours == "Tue-Sun 10:00-19:00"
        assert venue.accessibility_notes == "Wheelchair accessible"
        assert venue.url == "https://www.macba.cat"
    
    def test_invalid_venue_id(self, valid_venue_data):
        """Test that invalid venue ID is rejected."""
        valid_venue_data["id"] = "venue_01"
        with pytest.raises(ValidationError) as exc_info:
            Venue(**valid_venue_data)
        assert "String should match pattern" in str(exc_info.value)
    
    @pytest.mark.parametrize("venue_type", [
        "museum", "gallery", "street-cluster", "cultural-center", "outdoor-space"
    ])
    def test_valid_venue_types(self, valid_venue_data, venue_type):
        """Test all valid venue types."""
        valid_venue_data["type"] = venue_type
        venue = Venue(**valid_venue_data)
        assert venue.type == venue_type
    
    def test_invalid_venue_type(self, valid_venue_data):
        """Test that invalid venue type is rejected."""
        valid_venue_data["type"] = "cafe"
        with pytest.raises(ValidationError) as exc_info:
            Venue(**valid_venue_data)
        assert "Input should be" in str(exc_info.value)
    
    def test_venue_name_too_short(self, valid_venue_data):
        """Test that short venue name is rejected."""
        valid_venue_data["name"] = "A"
        with pytest.raises(ValidationError) as exc_info:
            Venue(**valid_venue_data)
        assert "at least 2 characters" in str(exc_info.value)
    
    def test_venue_coordinates_validation(self, valid_venue_data):
        """Test venue coordinates within Barcelona bounds."""
        valid_venue_data["latitude"] = 50.0  # Outside Barcelona
        with pytest.raises(ValidationError) as exc_info:
            Venue(**valid_venue_data)
        assert "less than or equal to" in str(exc_info.value)


class TestUserProfileValidation:
    """Test UserProfile model validation."""
    
    def test_valid_user_profile(self, valid_user_profile_data):
        """Test creating a valid user profile."""
        profile = UserProfile(**valid_user_profile_data)
        assert profile.user_id == "usr_abc123"
        assert profile.preferred_tags == {"modern": 5, "photography": 4, "contemporary": 3}
        assert profile.language == "en"
    
    def test_user_profile_defaults(self):
        """Test user profile with defaults."""
        from datetime import datetime
        profile = UserProfile(
            user_id="usr_123",
            last_interaction_ts=datetime.now(),
            created_at=datetime.now()
        )
        assert profile.preferred_tags == {}
        assert profile.saved_event_ids == []
        assert profile.language == "en"
    
    def test_invalid_tag_in_preferences(self, valid_user_profile_data):
        """Test that invalid tag in preferences is rejected."""
        valid_user_profile_data["preferred_tags"] = {"invalid_tag": 5}
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(**valid_user_profile_data)
        assert "not in controlled vocabulary" in str(exc_info.value)
    
    def test_invalid_tag_weight_low(self, valid_user_profile_data):
        """Test that tag weight < 1 is rejected."""
        valid_user_profile_data["preferred_tags"] = {"modern": 0}
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(**valid_user_profile_data)
        assert "between 1 and 5" in str(exc_info.value)
    
    def test_invalid_tag_weight_high(self, valid_user_profile_data):
        """Test that tag weight > 5 is rejected."""
        valid_user_profile_data["preferred_tags"] = {"modern": 6}
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(**valid_user_profile_data)
        assert "between 1 and 5" in str(exc_info.value)
    
    @pytest.mark.parametrize("language", ["en", "es"])
    def test_valid_languages(self, valid_user_profile_data, language):
        """Test valid language values."""
        valid_user_profile_data["language"] = language
        profile = UserProfile(**valid_user_profile_data)
        assert profile.language == language
    
    def test_invalid_language(self, valid_user_profile_data):
        """Test that invalid language is rejected."""
        valid_user_profile_data["language"] = "fr"
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(**valid_user_profile_data)
        assert "Input should be" in str(exc_info.value)


class TestEmbeddingDocValidation:
    """Test EmbeddingDoc model validation."""
    
    def test_valid_embedding_doc(self, valid_embedding_doc_data):
        """Test creating a valid embedding document."""
        doc = EmbeddingDoc(**valid_embedding_doc_data)
        assert doc.event_id == "evt_001"
        assert len(doc.vector) == 768
        assert doc.version == "1.0"
    
    def test_embedding_default_version(self, valid_embedding_doc_data):
        """Test that version has default value."""
        del valid_embedding_doc_data["version"]
        doc = EmbeddingDoc(**valid_embedding_doc_data)
        assert doc.version == "1.0"
    
    def test_invalid_vector_dimension_too_short(self, valid_embedding_doc_data):
        """Test that vector with wrong dimension is rejected."""
        valid_embedding_doc_data["vector"] = [0.1] * 100  # Wrong dimension
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingDoc(**valid_embedding_doc_data)
        assert "768-dimensional" in str(exc_info.value)
    
    def test_invalid_vector_dimension_too_long(self, valid_embedding_doc_data):
        """Test that vector with too many dimensions is rejected."""
        valid_embedding_doc_data["vector"] = [0.1] * 1000
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingDoc(**valid_embedding_doc_data)
        assert "768-dimensional" in str(exc_info.value)
    
    def test_empty_vector(self, valid_embedding_doc_data):
        """Test that empty vector is rejected."""
        valid_embedding_doc_data["vector"] = []
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingDoc(**valid_embedding_doc_data)
        assert "768-dimensional" in str(exc_info.value)
