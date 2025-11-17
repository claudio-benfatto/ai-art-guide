"""
Barcelona AI Art Guide - Pydantic Data Models
Day 1 Implementation - Refactored to Pydantic + YAML

Provides type-safe data models with automatic validation for:
- Events (exhibitions, art experiences)
- Venues (museums, galleries, street art clusters)
- User Profiles (preferences, interaction history)
- Embedding Documents (vector representations)
"""

from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Constants (loaded from settings.yaml in production)
# ============================================================================

CONTROLLED_VOCABULARY = {
    "modern", "contemporary", "photography", "painting", "sculpture",
    "installation", "street", "abstract", "surrealism", "conceptual",
    "minimalism", "performance", "digital", "mixed-media", "urban",
    "nature", "portrait", "experimental", "political", "feminist",
    "family-friendly", "educational", "immersive", "interactive",
    "baroque", "renaissance", "video"
}


# ============================================================================
# Event Schema
# ============================================================================

class Event(BaseModel):
    """
    Represents a visual art event, exhibition, or experience in Barcelona.
    
    Attributes:
        id: Unique event identifier (format: evt_NNN)
        title_en: English title (5-200 chars)
        title_es: Spanish title (5-200 chars)
        description_en: English description (50-1000 chars)
        description_es: Spanish description (50-1000 chars)
        tags: Controlled vocabulary tags (2-6 entries)
        category: Event category (gallery, museum, street, etc.)
        domain: Optional cultural domain for multi-domain expansion
        start_date: ISO 8601 date or "unknown"
        end_date: ISO 8601 date or "unknown"
        venue_id: References Venue.id
        cost_bucket: Cost category (free, low, mid, high, unknown)
        outdoor: Indoor/outdoor or "unknown"
        latitude: Geo coordinate (Barcelona bounds)
        longitude: Geo coordinate (Barcelona bounds)
        source_type: Data origin (curated, external)
        accessibility_notes: Optional accessibility information
        booking_url: Optional booking link or "unknown"
    """
    
    id: str = Field(pattern=r"^evt_\d+$", description="Unique event identifier")
    title_en: str = Field(min_length=5, max_length=200, description="English title")
    title_es: str = Field(min_length=5, max_length=200, description="Spanish title")
    description_en: str = Field(min_length=50, max_length=1000, description="English description")
    description_es: str = Field(min_length=50, max_length=1000, description="Spanish description")
    tags: list[str] = Field(min_length=2, max_length=6, description="Controlled vocabulary tags")
    category: Literal["gallery", "museum", "street", "pop-up", "opening", "cultural-center"]
    domain: Optional[Literal["visual-art", "music", "theatre", "cinema", "multi"]] = None
    start_date: Union[date, Literal["unknown"]] = Field(description="Event start date or 'unknown'")
    end_date: Union[date, Literal["unknown"]] = Field(description="Event end date or 'unknown'")
    venue_id: str = Field(description="References Venue.id")
    cost_bucket: Literal["free", "low", "mid", "high", "unknown"]
    outdoor: Union[bool, Literal["unknown"]] = Field(description="Indoor/outdoor or 'unknown'")
    latitude: float = Field(description="Latitude")
    longitude: float = Field(description="Longitude")
    source_type: Literal["curated", "external"]
    accessibility_notes: Optional[str] = None
    booking_url: Optional[Union[str, Literal["unknown"]]] = None
    
    @field_validator('tags')
    @classmethod
    def validate_tags_vocabulary(cls, v: list[str]) -> list[str]:
        """Ensure all tags are in controlled vocabulary."""
        invalid_tags = [tag for tag in v if tag not in CONTROLLED_VOCABULARY]
        if invalid_tags:
            raise ValueError(f"Tags not in controlled vocabulary: {invalid_tags}")
        return v
    
    @model_validator(mode='after')
    def validate_date_range(self) -> 'Event':
        """Ensure start_date <= end_date when both are dates."""
        if (isinstance(self.start_date, date) and 
            isinstance(self.end_date, date) and 
            self.start_date > self.end_date):
            raise ValueError(f"start_date ({self.start_date}) must be <= end_date ({self.end_date})")
        return self
    
    @classmethod
    def load_from_yaml(cls, path: str | Path) -> list['Event']:
        """Load events from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return [cls(**event) for event in data.get('events', [])]
    
    @classmethod
    def save_to_yaml(cls, events: list['Event'], path: str | Path) -> None:
        """Save events to YAML file with pretty formatting."""
        data = {'events': [e.model_dump(mode='python') for e in events]}
        with open(path, 'w') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


# ============================================================================
# Venue Schema
# ============================================================================

class Venue(BaseModel):
    """
    Represents a physical or virtual location hosting events.
    
    Attributes:
        id: Unique venue identifier (format: v_NN)
        name: Venue name
        type: Venue type (museum, gallery, street-cluster, etc.)
        neighborhood: Barcelona neighborhood
        latitude: Geo coordinate (Barcelona bounds)
        longitude: Geo coordinate (Barcelona bounds)
        opening_hours: Optional freeform text
        accessibility_notes: Optional accessibility info
        url: Optional venue website
    """
    
    id: str = Field(pattern=r"^v_\d+$", description="Unique venue identifier")
    name: str = Field(min_length=2, max_length=200, description="Venue name")
    type: Literal["museum", "gallery", "street-cluster", "cultural-center", "outdoor-space"]
    neighborhood: str = Field(min_length=2, max_length=100, description="Barcelona neighborhood")
    latitude: float = Field(description="Latitude")
    longitude: float = Field(description="Longitude")
    opening_hours: Optional[str] = None
    accessibility_notes: Optional[str] = None
    url: Optional[str] = None
    
    @classmethod
    def load_from_yaml(cls, path: str | Path) -> list['Venue']:
        """Load venues from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return [cls(**venue) for venue in data.get('venues', [])]
    
    @classmethod
    def save_to_yaml(cls, venues: list['Venue'], path: str | Path) -> None:
        """Save venues to YAML file with pretty formatting."""
        data = {'venues': [v.model_dump(mode='python') for v in venues]}
        with open(path, 'w') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


# ============================================================================
# User Profile Schema
# ============================================================================

class UserProfile(BaseModel):
    """
    User preferences and interaction history (stored in Firestore).
    
    Attributes:
        user_id: Unique user identifier (UUID format)
        preferred_tags: Tag weights (1-5 scale)
        saved_event_ids: Bookmarked event IDs
        language: Preferred language (en, es)
        last_interaction_ts: Last interaction timestamp
        created_at: Profile creation timestamp
    """
    
    user_id: str = Field(description="Unique user identifier")
    preferred_tags: dict[str, int] = Field(default_factory=dict, description="Tag weights (1-5)")
    saved_event_ids: list[str] = Field(default_factory=list, description="Bookmarked events")
    language: Literal["en", "es"] = Field(default="en")
    last_interaction_ts: datetime
    created_at: datetime
    
    @field_validator('preferred_tags')
    @classmethod
    def validate_tag_weights(cls, v: dict[str, int]) -> dict[str, int]:
        """Ensure tag weights are valid."""
        for tag, weight in v.items():
            if tag not in CONTROLLED_VOCABULARY:
                raise ValueError(f"Tag '{tag}' not in controlled vocabulary")
            if not 1 <= weight <= 5:
                raise ValueError(f"Weight for tag '{tag}' must be between 1 and 5, got {weight}")
        return v


# ============================================================================
# Embedding Document Schema
# ============================================================================

class EmbeddingDoc(BaseModel):
    """
    Precomputed embeddings for events (for RAG retrieval).
    
    Attributes:
        event_id: References Event.id
        text_concat: Concatenated text used for embedding
        vector: Embedding vector (768-dimensional)
        tags: Copy of event tags for filtering
        version: Schema version for migration tracking
    """
    
    event_id: str = Field(description="References Event.id")
    text_concat: str = Field(description="Concatenated text for embedding")
    vector: list[float] = Field(description="Embedding vector")
    tags: list[str] = Field(description="Event tags for filtering")
    version: str = Field(default="1.0", description="Schema version")
    
    @field_validator('vector')
    @classmethod
    def validate_vector_dimension(cls, v: list[float]) -> list[float]:
        """Ensure vector has correct dimensionality (768 for text-multilingual-embedding-002)."""
        if len(v) != 768:
            raise ValueError(f"Vector must be 768-dimensional, got {len(v)}")
        return v


# ============================================================================
# Data Container (for loading both events and venues from single file)
# ============================================================================

class DataContainer(BaseModel):
    """Container for events and venues from a single YAML file."""
    
    events: list[Event] = Field(default_factory=list)
    venues: list[Venue] = Field(default_factory=list)
    
    @model_validator(mode='after')
    def validate_venue_references(self) -> 'DataContainer':
        """Ensure all event venue_id references exist."""
        venue_ids = {v.id for v in self.venues}
        invalid_refs = []
        
        for event in self.events:
            if event.venue_id not in venue_ids:
                invalid_refs.append(f"Event {event.id} references non-existent venue {event.venue_id}")
        
        if invalid_refs:
            raise ValueError(f"Invalid venue references: {', '.join(invalid_refs)}")
        
        return self
    
    @classmethod
    def load_from_yaml(cls, path: str | Path) -> 'DataContainer':
        """Load both events and venues from YAML file with validation."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def save_to_yaml(self, path: str | Path) -> None:
        """Save both events and venues to YAML file with pretty formatting."""
        data = self.model_dump(mode='python')
        with open(path, 'w') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    
    def get_venue_by_id(self, venue_id: str) -> Optional[Venue]:
        """Get venue by ID."""
        for venue in self.venues:
            if venue.id == venue_id:
                return venue
        return None
    
    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Get event by ID."""
        for event in self.events:
            if event.id == event_id:
                return event
        return None
    
    def get_events_by_venue(self, venue_id: str) -> list[Event]:
        """Get all events at a specific venue."""
        return [e for e in self.events if e.venue_id == venue_id]
    
    def get_events_by_tag(self, tag: str) -> list[Event]:
        """Get all events with a specific tag."""
        return [e for e in self.events if tag in e.tags]
    
    def validate_uniqueness(self) -> None:
        """Validate ID uniqueness across events and venues."""
        event_ids = [e.id for e in self.events]
        venue_ids = [v.id for v in self.venues]
        
        # Check for duplicate event IDs
        if len(event_ids) != len(set(event_ids)):
            duplicates = [eid for eid in event_ids if event_ids.count(eid) > 1]
            raise ValueError(f"Duplicate event IDs found: {set(duplicates)}")
        
        # Check for duplicate venue IDs
        if len(venue_ids) != len(set(venue_ids)):
            duplicates = [vid for vid in venue_ids if venue_ids.count(vid) > 1]
            raise ValueError(f"Duplicate venue IDs found: {set(duplicates)}")
    
    def get_tag_coverage(self) -> dict[str, int]:
        """Get count of events using each tag from controlled vocabulary."""
        tag_counts = {tag: 0 for tag in CONTROLLED_VOCABULARY}
        for event in self.events:
            for tag in event.tags:
                if tag in tag_counts:
                    tag_counts[tag] += 1
        return tag_counts
    
    def summary(self) -> str:
        """Get human-readable summary of data."""
        tag_coverage = self.get_tag_coverage()
        tags_used = sum(1 for count in tag_coverage.values() if count > 0)
        
        return f"""Data Summary:
  Events: {len(self.events)}
  Venues: {len(self.venues)}
  Tag Coverage: {tags_used}/{len(CONTROLLED_VOCABULARY)}
  Categories: {len(set(e.category for e in self.events))}
  Domains: {len(set(e.domain for e in self.events if e.domain))}
  Cost Buckets: {len(set(e.cost_bucket for e in self.events))}
"""
