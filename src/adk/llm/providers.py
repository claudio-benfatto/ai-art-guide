"""
LLM Provider Interfaces and Implementations
Supports multiple LLM providers with fallback to mock for testing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import os


@dataclass
class Message:
    """Chat message."""
    role: str  # 'system', 'user', 'assistant'
    content: str


@dataclass
class LLMResponse:
    """LLM generation response."""
    content: str
    model: str
    usage: Optional[dict] = None  # {prompt_tokens, completion_tokens, total_tokens}


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, messages: List[Message], temperature: float = 0.7, max_tokens: int = 500) -> LLMResponse:
        """Generate response from messages."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier."""
        pass


class MockLLMProvider(LLMProvider):
    """
    Mock LLM for testing and fallback.
    Returns template-based responses without external API calls.
    """
    
    def __init__(self):
        self.call_count = 0
    
    def generate(self, messages: List[Message], temperature: float = 0.7, max_tokens: int = 500) -> LLMResponse:
        """Generate mock response."""
        self.call_count += 1
        
        # Extract last user message
        user_messages = [m for m in messages if m.role == 'user']
        last_user_message = user_messages[-1].content if user_messages else ""
        
        # Simple keyword-based mock responses
        content = self._generate_mock_content(last_user_message)
        
        return LLMResponse(
            content=content,
            model="mock-llm-v1",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        )
    
    def _generate_mock_content(self, query: str) -> str:
        """Generate mock response based on query keywords."""
        query_lower = query.lower()
        
        if "modern" in query_lower or "contemporary" in query_lower:
            return ("Based on your interest in modern art, I recommend checking out the Modern Photography "
                    "Retrospective. It explores the evolution of modern photography through iconic 20th century "
                    "works. The exhibition features experimental techniques and bold compositional choices.")
        
        if "photography" in query_lower:
            return ("For photography enthusiasts, I suggest the Modern Photography Retrospective at MACBA. "
                    "This exhibition showcases pioneering photographers who revolutionized visual storytelling.")
        
        if "family" in query_lower:
            return ("For a family-friendly experience, I recommend visiting exhibitions that offer interactive "
                    "elements and educational programs suitable for all ages.")
        
        # Default response
        return ("I found several interesting art events in Barcelona. Would you like recommendations based on "
                "specific themes, dates, or locations?")
    
    @property
    def provider_name(self) -> str:
        return "mock"


class OpenAIProvider(LLMProvider):
    """
    OpenAI LLM provider (GPT-3.5/GPT-4).
    Requires OPENAI_API_KEY environment variable.
    """
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def generate(self, messages: List[Message], temperature: float = 0.7, max_tokens: int = 500) -> LLMResponse:
        """Generate response using OpenAI API."""
        # Convert to OpenAI message format
        openai_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        )
    
    @property
    def provider_name(self) -> str:
        return "openai"


def get_llm_provider(provider: Optional[str] = None, model: Optional[str] = None) -> LLMProvider:
    """
    Factory function to get LLM provider.
    
    Args:
        provider: Provider name ('openai', 'mock'). Defaults to env var LLM_PROVIDER or 'mock'
        model: Model name (provider-specific). Defaults to env var LLM_MODEL or provider default
    
    Returns:
        LLMProvider instance
    
    Examples:
        >>> # Use mock for testing
        >>> llm = get_llm_provider('mock')
        >>> 
        >>> # Use OpenAI
        >>> llm = get_llm_provider('openai', 'gpt-4')
        >>> 
        >>> # Auto-detect from environment
        >>> llm = get_llm_provider()  # Uses LLM_PROVIDER env var or defaults to mock
    """
    provider = provider or os.getenv("LLM_PROVIDER", "mock")
    
    if provider == "mock":
        return MockLLMProvider()
    
    elif provider == "openai":
        model = model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        return OpenAIProvider(model=model)
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: 'openai', 'mock'")
