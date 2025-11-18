#!/usr/bin/env python3
"""
Test Ollama Provider
Quick test to verify Ollama integration works.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adk.llm.providers import OllamaProvider


def test_ollama():
    """Test Ollama provider."""
    print("=" * 70)
    print("Testing Ollama Provider with Llama3")
    print("=" * 70)
    
    try:
        # Create Ollama provider
        print("\n1. Initializing Ollama provider...")
        llm = OllamaProvider(model="llama3")
        print(f"   ✓ Provider: {llm.provider_name}")
        
        # Test simple generation
        print("\n2. Testing simple generation...")
        from adk.llm.providers import Message
        
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Say hello in one short sentence.")
        ]
        
        print("   Generating response...")
        response = llm.generate(messages, temperature=0.7, max_tokens=50)
        
        print(f"\n   Response: {response.content}")
        print(f"   Model: {response.model}")
        print(f"   Tokens: {response.usage}")
        
        print("\n" + "=" * 70)
        print("✓ Ollama test PASSED!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("\n🦙 Ollama + Llama3 Test\n")
    
    # Check if Ollama is running
    print("Note: Make sure Ollama is running with: ollama serve")
    print("And that llama3 model is available: ollama pull llama3\n")
    
    success = test_ollama()
    sys.exit(0 if success else 1)
