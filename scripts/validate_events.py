#!/usr/bin/env python3
"""
Barcelona AI Art Guide - Schema Validator
Day 1 Implementation

Validates events and venues against schema constraints with zero external dependencies.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ValidationError:
    """Structured validation error."""
    def __init__(self, path: str, message: str, value: Any = None):
        self.path = path
        self.message = message
        self.value = value
    
    def __str__(self) -> str:
        val_str = f" (value: {self.value})" if self.value is not None else ""
        return f"❌ {self.path}: {self.message}{val_str}"


class SchemaValidator:
    """Validates data against Barcelona AI Art Guide schemas."""
    
    # Constants from schema
    COST_BUCKETS = {"free", "low", "mid", "high"}
    CATEGORIES = {"gallery", "museum", "street", "pop-up", "opening", "cultural-center"}
    VENUE_TYPES = {"museum", "gallery", "street-cluster", "cultural-center", "outdoor-space"}
    LANGUAGES = {"en", "es"}
    
    # Barcelona geo bounds
    LAT_MIN, LAT_MAX = 41.30, 41.50
    LON_MIN, LON_MAX = 2.00, 2.30
    
    CONTROLLED_VOCAB = {
        "modern", "contemporary", "photography", "painting", "sculpture",
        "installation", "street", "abstract", "surrealism", "conceptual",
        "minimalism", "performance", "digital", "mixed-media", "urban",
        "nature", "portrait", "experimental", "political", "feminist",
        "family-friendly", "educational", "immersive", "interactive",
        "baroque", "renaissance", "video"
    }
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []
    
    def add_error(self, path: str, message: str, value: Any = None):
        """Add validation error."""
        self.errors.append(ValidationError(path, message, value))
    
    def add_warning(self, message: str):
        """Add validation warning."""
        self.warnings.append(f"⚠️  {message}")
    
    def validate_required_field(self, obj: Dict, field: str, path: str) -> bool:
        """Check required field exists and is not empty."""
        if field not in obj:
            self.add_error(f"{path}.{field}", "Required field missing")
            return False
        
        value = obj[field]
        if value is None or (isinstance(value, str) and value.strip() == ""):
            self.add_error(f"{path}.{field}", "Required field is empty")
            return False
        
        return True
    
    def validate_string_length(self, value: str, min_len: int, max_len: int, path: str) -> bool:
        """Validate string length."""
        if not isinstance(value, str):
            self.add_error(path, f"Expected string, got {type(value).__name__}")
            return False
        
        length = len(value.strip())
        if length < min_len or length > max_len:
            self.add_error(path, f"Length must be {min_len}-{max_len} chars, got {length}")
            return False
        return True
    
    def validate_date(self, date_str: str, path: str) -> bool:
        """Validate ISO 8601 date format."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            self.add_error(path, f"Invalid date format, expected YYYY-MM-DD", date_str)
            return False
    
    def validate_coordinates(self, lat: float, lon: float, path: str) -> bool:
        """Validate coordinates within Barcelona bounds."""
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            self.add_error(path, "Coordinates must be numeric")
            return False
        
        if not (self.LAT_MIN <= lat <= self.LAT_MAX):
            self.add_error(f"{path}.latitude", f"Outside Barcelona bounds ({self.LAT_MIN}-{self.LAT_MAX})", lat)
            return False
        
        if not (self.LON_MIN <= lon <= self.LON_MAX):
            self.add_error(f"{path}.longitude", f"Outside Barcelona bounds ({self.LON_MIN}-{self.LON_MAX})", lon)
            return False
        
        return True
    
    def validate_event(self, event: Dict, index: int, all_venue_ids: set) -> bool:
        """Validate single event."""
        path = f"events[{index}]"
        valid = True
        
        # Required fields
        required = [
            "id", "title_en", "title_es", "description_en", "description_es",
            "tags", "category", "start_date", "end_date", "venue_id",
            "cost_bucket", "outdoor", "popularity_score", "latitude", "longitude", "source_type"
        ]
        
        for field in required:
            if not self.validate_required_field(event, field, path):
                valid = False
        
        if not valid:
            return False  # Skip further validation if required fields missing
        
        # ID format
        if not event["id"].startswith("evt_"):
            self.add_error(f"{path}.id", "ID must start with 'evt_'", event["id"])
            valid = False
        
        # Title lengths
        self.validate_string_length(event["title_en"], 5, 200, f"{path}.title_en")
        self.validate_string_length(event["title_es"], 5, 200, f"{path}.title_es")
        
        # Description lengths
        self.validate_string_length(event["description_en"], 50, 1000, f"{path}.description_en")
        self.validate_string_length(event["description_es"], 50, 1000, f"{path}.description_es")
        
        # Tags
        tags = event["tags"]
        if not isinstance(tags, list) or not (2 <= len(tags) <= 6):
            self.add_error(f"{path}.tags", "Must be array with 2-6 entries", len(tags) if isinstance(tags, list) else type(tags))
            valid = False
        else:
            for i, tag in enumerate(tags):
                if tag not in self.CONTROLLED_VOCAB:
                    self.add_error(f"{path}.tags[{i}]", f"Tag not in controlled vocabulary", tag)
                    valid = False
        
        # Category
        if event["category"] not in self.CATEGORIES:
            self.add_error(f"{path}.category", f"Must be one of {self.CATEGORIES}", event["category"])
            valid = False
        
        # Dates
        if self.validate_date(event["start_date"], f"{path}.start_date") and \
           self.validate_date(event["end_date"], f"{path}.end_date"):
            start = datetime.strptime(event["start_date"], "%Y-%m-%d")
            end = datetime.strptime(event["end_date"], "%Y-%m-%d")
            if start > end:
                self.add_error(f"{path}.dates", "start_date must be <= end_date")
                valid = False
        
        # Venue reference
        if event["venue_id"] not in all_venue_ids:
            self.add_error(f"{path}.venue_id", "References non-existent venue", event["venue_id"])
            valid = False
        
        # Cost bucket
        if event["cost_bucket"] not in self.COST_BUCKETS:
            self.add_error(f"{path}.cost_bucket", f"Must be one of {self.COST_BUCKETS}", event["cost_bucket"])
            valid = False
        
        # Outdoor boolean
        if not isinstance(event["outdoor"], bool):
            self.add_error(f"{path}.outdoor", "Must be boolean", event["outdoor"])
            valid = False
        
        # Popularity score
        pop = event["popularity_score"]
        if not isinstance(pop, (int, float)) or not (0 <= pop <= 1):
            self.add_error(f"{path}.popularity_score", "Must be float 0-1", pop)
            valid = False
        
        # Coordinates
        self.validate_coordinates(event["latitude"], event["longitude"], path)
        
        # Source type
        if event["source_type"] not in {"curated", "external"}:
            self.add_error(f"{path}.source_type", "Must be 'curated' or 'external'", event["source_type"])
            valid = False
        
        return valid
    
    def validate_venue(self, venue: Dict, index: int) -> bool:
        """Validate single venue."""
        path = f"venues[{index}]"
        valid = True
        
        # Required fields
        required = ["id", "name", "type", "neighborhood", "latitude", "longitude"]
        
        for field in required:
            if not self.validate_required_field(venue, field, path):
                valid = False
        
        if not valid:
            return False
        
        # ID format
        if not venue["id"].startswith("v_"):
            self.add_error(f"{path}.id", "ID must start with 'v_'", venue["id"])
            valid = False
        
        # Type
        if venue["type"] not in self.VENUE_TYPES:
            self.add_error(f"{path}.type", f"Must be one of {self.VENUE_TYPES}", venue["type"])
            valid = False
        
        # Coordinates
        self.validate_coordinates(venue["latitude"], venue["longitude"], path)
        
        return valid
    
    def validate_data(self, data: Dict) -> bool:
        """Validate entire dataset."""
        if "events" not in data or "venues" not in data:
            self.add_error("root", "Missing 'events' or 'venues' key")
            return False
        
        events = data["events"]
        venues = data["venues"]
        
        if not isinstance(events, list) or not isinstance(venues, list):
            self.add_error("root", "events and venues must be arrays")
            return False
        
        # Validate venues first (events reference them)
        venue_ids = set()
        for i, venue in enumerate(venues):
            self.validate_venue(venue, i)
            if "id" in venue:
                if venue["id"] in venue_ids:
                    self.add_error(f"venues[{i}].id", "Duplicate venue ID", venue["id"])
                venue_ids.add(venue["id"])
        
        # Validate events
        event_ids = set()
        for i, event in enumerate(events):
            self.validate_event(event, i, venue_ids)
            if "id" in event:
                if event["id"] in event_ids:
                    self.add_error(f"events[{i}].id", "Duplicate event ID", event["id"])
                event_ids.add(event["id"])
        
        # Summary stats
        if not self.errors:
            self.add_warning(f"Validated {len(events)} events and {len(venues)} venues successfully")
            
            # Tag distribution
            all_tags = [tag for event in events for tag in event.get("tags", [])]
            unique_tags = set(all_tags)
            self.add_warning(f"Tag coverage: {len(unique_tags)}/{len(self.CONTROLLED_VOCAB)} vocabulary tags used")
        
        return len(self.errors) == 0


def main():
    """Main validation entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_events.py <data_file.json>")
        sys.exit(1)
    
    data_file = Path(sys.argv[1])
    
    if not data_file.exists():
        print(f"❌ File not found: {data_file}")
        sys.exit(1)
    
    print(f"📋 Validating: {data_file}")
    print()
    
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)
    
    validator = SchemaValidator()
    is_valid = validator.validate_data(data)
    
    # Print errors
    if validator.errors:
        print("VALIDATION ERRORS:")
        print("-" * 60)
        for error in validator.errors:
            print(error)
        print()
    
    # Print warnings
    if validator.warnings:
        print("VALIDATION SUMMARY:")
        print("-" * 60)
        for warning in validator.warnings:
            print(warning)
        print()
    
    # Exit status
    if is_valid:
        print("✅ Validation passed!")
        sys.exit(0)
    else:
        print(f"❌ Validation failed with {len(validator.errors)} error(s)")
        sys.exit(1)


if __name__ == "__main__":
    main()
