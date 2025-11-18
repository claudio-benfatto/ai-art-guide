"""
Recommendation Agent
Handles user queries and generates event recommendations.
"""

from dataclasses import dataclass
from typing import List, Optional

from adk.llm.providers import LLMProvider, Message, get_llm_provider
from adk.tools.retrieve_events import RetrieveEventsInput, retrieve_events


@dataclass
class AgentResponse:
    """Agent response to user query."""
    message: str
    events_found: int
    event_ids: List[str]
    events: List = None  # List of EventResult objects
    degraded_mode: bool = False  # True if using fallbacks
    
    def __post_init__(self):
        """Initialize events list if None."""
        if self.events is None:
            self.events = []


SYSTEM_PROMPT = """You are a helpful AI art guide for Barcelona. Your role is to recommend art events, exhibitions, and cultural experiences based on user preferences.

When recommending events, you should:
1. Describe the event briefly and engagingly
2. Mention key themes or artists
3. Include practical details (dates, venue, cost)
4. Be concise but informative (2-3 sentences per event)
5. Use a friendly, enthusiastic tone

If multiple events match, focus on the top 2-3 most relevant ones."""


class RecommendationAgent:
    """
    Agent that recommends art events based on natural language queries.
    
    Flow:
        1. User query → extract intent/filters
        2. Call retrieve_events tool
        3. Format results with LLM
        4. Return natural language response
    """
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """
        Initialize agent.
        
        Args:
            llm_provider: LLM provider for response generation. Defaults to environment-based selection.
        """
        self.llm = llm_provider or get_llm_provider()
    
    def process_query(
        self,
        query: str,
        max_results: int = 5,
        filters: Optional[dict] = None
    ) -> AgentResponse:
        """
        Process user query and generate recommendation.
        
        Args:
            query: Natural language query (e.g., "Show me modern art exhibitions")
            max_results: Maximum number of events to retrieve
            filters: Optional explicit filters {tags, date_start, date_end, geo_lat, geo_lon, geo_radius_km}
        
        Returns:
            AgentResponse with formatted recommendation
        
        Example:
            >>> agent = RecommendationAgent()
            >>> response = agent.process_query("modern photography events")
            >>> print(response.message)
            "I found 3 modern photography events for you..."
        """
        # Step 1: Retrieve events using tool
        input_data = RetrieveEventsInput(
            query_text=query,
            max_results=max_results,
            tags=filters.get('tags') if filters else None,
            date_start=filters.get('date_start') if filters else None,
            date_end=filters.get('date_end') if filters else None,
            geo_lat=filters.get('geo_lat') if filters else None,
            geo_lon=filters.get('geo_lon') if filters else None,
            geo_radius_km=filters.get('geo_radius_km') if filters else None
        )
        
        retrieval_output = retrieve_events(input_data)
        
        # Step 2: Format results for LLM
        if retrieval_output.total_found == 0:
            return AgentResponse(
                message="I couldn't find any events matching your criteria. Try broadening your search or ask about different themes!",
                events_found=0,
                event_ids=[]
            )
        
        # Build context from retrieved events
        events_context = self._format_events_for_llm(retrieval_output.events[:3])  # Focus on top 3
        
        # Step 3: Generate response with LLM
        messages = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=f"User query: {query}\n\nRetrieved events:\n{events_context}\n\nProvide a friendly recommendation based on these events.")
        ]
        
        try:
            llm_response = self.llm.generate(messages, temperature=0.7, max_tokens=400)
            response_message = llm_response.content
            degraded = False
        except Exception as e:
            # Fallback to template response
            response_message = self._generate_fallback_response(query, retrieval_output.events[:3])
            degraded = True
        
        return AgentResponse(
            message=response_message,
            events_found=retrieval_output.total_found,
            event_ids=[e.event_id for e in retrieval_output.events],
            events=retrieval_output.events,  # Include full event objects
            degraded_mode=degraded
        )
    
    def _format_events_for_llm(self, events: list) -> str:
        """Format events into readable context for LLM."""
        formatted = []
        for i, event in enumerate(events, 1):
            formatted.append(
                f"{i}. **{event.title}**\n"
                f"   - Tags: {', '.join(event.tags)}\n"
                f"   - Description: {event.description[:200]}...\n"
                f"   - Dates: {event.start_date} to {event.end_date}\n"
                f"   - Category: {event.category}\n"
                f"   - Cost: {event.cost_bucket}\n"
                f"   - Relevance score: {event.raw_score:.3f}"
            )
        return "\n\n".join(formatted)
    
    def _generate_fallback_response(self, query: str, events: list) -> str:
        """Generate template-based response when LLM unavailable."""
        if not events:
            return "I found some events, but couldn't generate a detailed recommendation. Please try again!"
        
        # Simple template
        event = events[0]
        return (
            f"Based on your interest in '{query}', I recommend **{event.title}**. "
            f"This {event.category} event features {', '.join(event.tags[:2])} themes. "
            f"It runs from {event.start_date} to {event.end_date} and is {event.cost_bucket}. "
            f"{'I also found ' + str(len(events) - 1) + ' other relevant events.' if len(events) > 1 else ''}"
        )
