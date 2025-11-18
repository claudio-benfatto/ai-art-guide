"""
FastAPI application for Barcelona AI Art Guide.
Provides chat endpoint for event recommendations.
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from adk.agents import AgentResponse, RecommendationAgent

app = FastAPI(
    title="Barcelona AI Art Guide",
    description="Get personalized art event recommendations in Barcelona",
    version="0.1.0"
)

# Global agent instance (lazy-loaded)
_agent: Optional[RecommendationAgent] = None


def get_agent() -> RecommendationAgent:
    """Get or create the global agent instance."""
    global _agent
    if _agent is None:
        _agent = RecommendationAgent()
    return _agent


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str = Field(..., min_length=1, description="User's natural language query")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of events to retrieve")
    filters: Optional[dict] = Field(None, description="Optional filters (tags, dates, location)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Show me modern art exhibitions",
                "max_results": 5,
                "filters": {
                    "tags": ["modern"],
                    "geo_lat": 41.3851,
                    "geo_lon": 2.1734,
                    "geo_radius_km": 5.0
                }
            }
        }


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""
    message: str = Field(..., description="Agent's natural language response")
    events_found: int = Field(..., description="Number of events found")
    event_ids: list[str] = Field(..., description="List of event IDs returned")
    degraded_mode: bool = Field(False, description="True if using fallback responses")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I found 3 modern art exhibitions for you...",
                "events_found": 3,
                "event_ids": ["macba_modern_2024", "cccb_contemporary_2024"],
                "degraded_mode": False
            }
        }


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "Barcelona AI Art Guide",
        "version": "0.1.0",
        "endpoints": {
            "/chat": "POST - Get event recommendations",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    agent = get_agent()
    return {
        "status": "healthy",
        "llm_provider": agent.llm.provider_name
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint for event recommendations.
    
    Send a natural language query and get personalized recommendations.
    
    Args:
        request: ChatRequest with user message and optional filters
    
    Returns:
        ChatResponse with agent's recommendation
    
    Example:
        ```
        curl -X POST http://localhost:8000/chat \\
          -H "Content-Type: application/json" \\
          -d '{"message": "modern photography events", "max_results": 3}'
        ```
    """
    try:
        agent = get_agent()
        
        # Process query through agent
        agent_response: AgentResponse = agent.process_query(
            query=request.message,
            max_results=request.max_results,
            filters=request.filters
        )
        
        return ChatResponse(
            message=agent_response.message,
            events_found=agent_response.events_found,
            event_ids=agent_response.event_ids,
            degraded_mode=agent_response.degraded_mode
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
