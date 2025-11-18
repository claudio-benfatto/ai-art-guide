#!/usr/bin/env python3
"""
Interactive Demo - Barcelona AI Art Guide
Query the agent interactively from the command line.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adk.agents import RecommendationAgent
from adk.llm.providers import MockLLMProvider


def print_header():
    """Print welcome header."""
    print("\n" + "=" * 70)
    print("🎨  Barcelona AI Art Guide - Interactive Demo")
    print("=" * 70)
    print("\nAsk me about art events in Barcelona!")
    print("Examples:")
    print("  - Show me modern art exhibitions")
    print("  - I'm interested in photography")
    print("  - What's happening near MACBA?")
    print("\nType 'quit' or 'exit' to stop.\n")


def main():
    """Run interactive demo."""
    print_header()
    
    # Initialize agent with mock LLM
    agent = RecommendationAgent(llm_provider=MockLLMProvider())
    print(f"Agent ready (using {agent.llm.provider_name})\n")
    
    while True:
        try:
            # Get user input
            query = input("You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for using Barcelona AI Art Guide!")
                break
            
            # Process query
            print("\n🤔 Searching...\n")
            response = agent.process_query(query, max_results=3)
            
            # Display response
            print(f"Agent: {response.message}\n")
            print(f"📊 Found {response.events_found} events")
            
            # Display event details
            if response.events:
                print("\n📍 Event Details:")
                for i, event in enumerate(response.events[:3], 1):
                    print(f"\n{i}. {event.title}")
                    print(f"   📅 {event.start_date} to {event.end_date}")
                    print(f"   📍 {event.venue_name}")
                    if event.distance_km is not None:
                        print(f"   🚶 Distance: {event.distance_km:.1f} km")
                    print(f"   💰 {event.cost_bucket.title()}")
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for using Barcelona AI Art Guide!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    main()
