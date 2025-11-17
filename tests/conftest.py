"""Pytest fixtures for Barcelona AI Art Guide tests."""

from datetime import date, datetime
from pathlib import Path

import pytest


@pytest.fixture
def valid_event_data():
    """Minimal valid event data."""
    return {
        "id": "evt_001",
        "title_en": "Modern Photography Exhibition",
        "title_es": "Exposición de Fotografía Moderna",
        "description_en": "A comprehensive exhibition showcasing the evolution of modern photography through iconic works from renowned photographers.",
        "description_es": "Una exposición integral que muestra la evolución de la fotografía moderna a través de obras icónicas de fotógrafos reconocidos.",
        "tags": ["modern", "photography", "contemporary"],
        "category": "museum",
        "start_date": date(2025, 11, 20),
        "end_date": date(2026, 1, 15),
        "venue_id": "v_01",
        "cost_bucket": "mid",
        "outdoor": False,
        "latitude": 41.3851,
        "longitude": 2.1734,
        "source_type": "curated"
    }


@pytest.fixture
def valid_venue_data():
    """Minimal valid venue data."""
    return {
        "id": "v_01",
        "name": "MACBA - Museum of Contemporary Art",
        "type": "museum",
        "neighborhood": "El Raval",
        "latitude": 41.3851,
        "longitude": 2.1734
    }


@pytest.fixture
def valid_user_profile_data():
    """Valid user profile data."""
    return {
        "user_id": "usr_abc123",
        "preferred_tags": {"modern": 5, "photography": 4, "contemporary": 3},
        "saved_event_ids": ["evt_001", "evt_002"],
        "language": "en",
        "last_interaction_ts": datetime(2025, 11, 17, 14, 30),
        "created_at": datetime(2025, 11, 15, 10, 0)
    }


@pytest.fixture
def valid_embedding_doc_data():
    """Valid embedding document data."""
    return {
        "event_id": "evt_001",
        "text_concat": "Modern Photography Exhibition. A comprehensive exhibition...",
        "vector": [0.1] * 768,  # 768-dimensional vector
        "tags": ["modern", "photography", "contemporary"],
        "version": "1.0"
    }


@pytest.fixture
def test_data_dir(tmp_path):
    """Create temporary directory for test data files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def valid_data_container_dict():
    """Valid data container with events and venues."""
    return {
        "events": [
            {
                "id": "evt_001",
                "title_en": "Modern Photography Exhibition",
                "title_es": "Exposición de Fotografía Moderna",
                "description_en": "A comprehensive exhibition showcasing the evolution of modern photography through iconic works from renowned photographers.",
                "description_es": "Una exposición integral que muestra la evolución de la fotografía moderna a través de obras icónicas de fotógrafos reconocidos.",
                "tags": ["modern", "photography", "contemporary"],
                "category": "museum",
                "start_date": "2025-11-20",
                "end_date": "2026-01-15",
                "venue_id": "v_01",
                "cost_bucket": "mid",
                "outdoor": False,
                "latitude": 41.3851,
                "longitude": 2.1734,
                "source_type": "curated"
            },
            {
                "id": "evt_002",
                "title_en": "Street Art Walking Tour",
                "title_es": "Tour de Arte Urbano",
                "description_en": "Discover hidden murals and graffiti masterpieces in Barcelona's vibrant neighborhoods with expert local guides.",
                "description_es": "Descubre murales ocultos y obras maestras de graffiti en los vibrantes barrios de Barcelona con guías locales expertos.",
                "tags": ["street", "urban", "contemporary"],
                "category": "street",
                "start_date": "2025-11-18",
                "end_date": "2025-12-20",
                "venue_id": "v_02",
                "cost_bucket": "free",
                "outdoor": True,
                "latitude": 41.3801,
                "longitude": 2.1700,
                "source_type": "curated"
            }
        ],
        "venues": [
            {
                "id": "v_01",
                "name": "MACBA - Museum of Contemporary Art",
                "type": "museum",
                "neighborhood": "El Raval",
                "latitude": 41.3851,
                "longitude": 2.1734
            },
            {
                "id": "v_02",
                "name": "El Raval Street Art Cluster",
                "type": "street-cluster",
                "neighborhood": "El Raval",
                "latitude": 41.3801,
                "longitude": 2.1700
            }
        ]
    }
