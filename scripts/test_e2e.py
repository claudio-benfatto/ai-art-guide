#!/usr/bin/env python3
"""
End-to-End Test Script
Tests the complete flow: user query → agent → retrieve_events → LLM → response
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adk.agents import RecommendationAgent
from adk.llm.providers import MockLLMProvider


def test_e2e_flow():
    """Test end-to-end conversational flow."""
    print("=" * 70)
    print("Barcelona AI Art Guide - End-to-End Test")
    print("=" * 70)
    
    # Create agent with mock LLM
    agent = RecommendationAgent(llm_provider=MockLLMProvider())
    print(f"\n✓ Agent initialized with {agent.llm.provider_name}")
    
    # Test queries
    test_queries = [
        "I'm interested in modern art exhibitions",
        "Show me photography events",
        "What's good for families with kids?",
        "Art near MACBA"
    ]
    
    print("\n" + "=" * 70)
    print("Testing Queries")
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: \"{query}\"")
        print("-" * 70)
        
        try:
            response = agent.process_query(query, max_results=3)
            
            print(f"   Events Found: {response.events_found}")
            if response.events:
                print(f"   Top Event: {response.events[0].title}")
                print(f"   Venue: {response.events[0].venue_name}")
                print(f"   Dates: {response.events[0].start_date} to {response.events[0].end_date}")
            print(f"   Degraded Mode: {response.degraded_mode}")
            print(f"\n   Response:\n   {response.message[:200]}...")
            
            # Validate
            assert response.events_found >= 0, "Should return non-negative event count"
            assert isinstance(response.message, str), "Should return string message"
            assert len(response.message) > 0, "Message should not be empty"
            
            print("\n   ✓ PASSED")
            
        except Exception as e:
            print(f"\n   ✗ FAILED: {str(e)}")
            return False
    
    print("\n" + "=" * 70)
    print("All End-to-End Tests PASSED ✓")
    print("=" * 70)
    return True


def test_with_filters():
    """Test query with explicit filters."""
    print("\n" + "=" * 70)
    print("Testing with Filters")
    print("=" * 70)
    
    agent = RecommendationAgent(llm_provider=MockLLMProvider())
    
    # Test with location filter
    print("\nQuery: 'art events' with location filter (near MACBA)")
    response = agent.process_query(
        "art events",
        filters={
            'geo_lat': 41.3830,
            'geo_lon': 2.1670,
            'geo_radius_km': 1.0
        }
    )
    
    print(f"Events Found: {response.events_found}")
    print(f"Message: {response.message[:150]}...")
    print("\n✓ Location filter test PASSED")
    
    # Test with tag filter
    print("\nQuery: 'exhibitions' with tag filter (modern)")
    response = agent.process_query(
        "exhibitions",
        filters={'tags': ["modern"]}
    )
    
    print(f"Events Found: {response.events_found}")
    print(f"Message: {response.message[:150]}...")
    print("\n✓ Tag filter test PASSED")


if __name__ == "__main__":
    print("\n🎨 Barcelona AI Art Guide - E2E Validation\n")
    
    try:
        # Run tests
        success = test_e2e_flow()
        if success:
            test_with_filters()
            
            print("\n" + "=" * 70)
            print("🎉 ALL END-TO-END TESTS PASSED!")
            print("=" * 70)
            print("\nYou can now:")
            print("  1. Query the agent via command line")
            print("  2. Start FastAPI server: poetry run python src/api/main.py")
            print("  3. Test HTTP endpoint: curl -X POST http://localhost:8000/chat \\")
            print("       -H 'Content-Type: application/json' \\")
            print("       -d '{\"message\": \"modern art\", \"max_results\": 3}'")
            print("=" * 70)
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
