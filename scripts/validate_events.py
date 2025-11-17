#!/usr/bin/env python3
"""
Barcelona AI Art Guide - Pydantic-based Validator
Day 1 Implementation - Refactored to use Pydantic + YAML

Validates events and venues using Pydantic models with comprehensive error reporting.
Supports both JSON and YAML input files.
"""

import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adk.models.schemas import DataContainer, CONTROLLED_VOCABULARY


def format_validation_error(error: ValidationError) -> list[str]:
    """Format Pydantic validation errors into human-readable messages."""
    formatted_errors = []
    
    for err in error.errors():
        loc = " → ".join(str(l) for l in err['loc'])
        msg = err['msg']
        value = err.get('input', '')
        
        # Truncate long values
        if isinstance(value, str) and len(value) > 50:
            value = value[:47] + "..."
        
        formatted_errors.append(f"❌ {loc}: {msg} (value: {value})")
    
    return formatted_errors


def print_summary(data: DataContainer) -> None:
    """Print validation summary with statistics."""
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    print(f"\n✅ Successfully validated:")
    print(f"   • {len(data.events)} events")
    print(f"   • {len(data.venues)} venues")
    
    # Tag coverage
    tag_coverage = data.get_tag_coverage()
    tags_used = sum(1 for count in tag_coverage.values() if count > 0)
    print(f"   • Tag coverage: {tags_used}/{len(CONTROLLED_VOCABULARY)}")
    
    # Category distribution
    categories = {}
    for event in data.events:
        categories[event.category] = categories.get(event.category, 0) + 1
    print(f"   • Categories: {', '.join(f'{k}({v})' for k, v in sorted(categories.items()))}")
    
    # Cost distribution
    costs = {}
    for event in data.events:
        costs[event.cost_bucket] = costs.get(event.cost_bucket, 0) + 1
    print(f"   • Cost buckets: {', '.join(f'{k}({v})' for k, v in sorted(costs.items()))}")
    
    # Domain distribution
    domains = {}
    for event in data.events:
        if event.domain:
            domains[event.domain] = domains.get(event.domain, 0) + 1
    if domains:
        print(f"   • Domains: {', '.join(f'{k}({v})' for k, v in sorted(domains.items()))}")
    
    # Venue types
    venue_types = {}
    for venue in data.venues:
        venue_types[venue.type] = venue_types.get(venue.type, 0) + 1
    print(f"   • Venue types: {', '.join(f'{k}({v})' for k, v in sorted(venue_types.items()))}")
    
    # Neighborhoods
    neighborhoods = set(v.neighborhood for v in data.venues)
    print(f"   • Neighborhoods: {len(neighborhoods)} ({', '.join(sorted(neighborhoods))})")
    
    # Warnings for unused tags
    unused_tags = [tag for tag, count in tag_coverage.items() if count == 0]
    if unused_tags:
        print(f"\n⚠️  Unused tags ({len(unused_tags)}): {', '.join(sorted(unused_tags))}")
    
    print("\n" + "="*60)


def main():
    """Main validation entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_events.py <file.yaml|file.json>")
        print("\nExample:")
        print("  python validate_events.py data/events.yaml")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    
    print(f"📋 Validating: {file_path}")
    print(f"   Format: {file_path.suffix.upper()[1:]}")
    
    try:
        # Load and validate using Pydantic
        data = DataContainer.load_from_yaml(file_path)
        
        # Additional validations
        data.validate_uniqueness()
        
        # Print summary
        print_summary(data)
        
        print("\n✅ Validation passed! All data is valid.")
        return 0
        
    except ValidationError as e:
        print("\n" + "="*60)
        print("VALIDATION ERRORS")
        print("="*60)
        
        errors = format_validation_error(e)
        for error in errors:
            print(error)
        
        print(f"\n❌ Found {len(errors)} validation error(s)")
        print("="*60)
        return 1
        
    except ValueError as e:
        print("\n" + "="*60)
        print("VALIDATION ERROR")
        print("="*60)
        print(f"❌ {e}")
        print("="*60)
        return 1
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
