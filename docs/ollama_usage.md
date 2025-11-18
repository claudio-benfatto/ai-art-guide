# Using Ollama with Llama3

The Barcelona AI Art Guide now supports running Llama3 locally via Ollama!

## Setup

### 1. Install Ollama

```bash
# macOS
brew install ollama

# Or download from https://ollama.ai
```

### 2. Pull Llama3 Model

```bash
ollama pull llama3
```

### 3. Start Ollama Server

```bash
# In a separate terminal, start the Ollama server
ollama serve
```

This will start Ollama on `http://localhost:11434`

## Usage

### Environment Variables

```bash
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3
```

### In Code

```python
from adk.llm.providers import OllamaProvider

# Create provider
llm = OllamaProvider(model="llama3")

# Generate response
from adk.llm.providers import Message

messages = [
    Message(role="system", content="You are a helpful Barcelona art guide."),
    Message(role="user", content="Tell me about modern art in Barcelona")
]

response = llm.generate(messages, temperature=0.7, max_tokens=500)
print(response.content)
```

### With the Agent

```python
from adk.agents import RecommendationAgent
from adk.llm.providers import OllamaProvider

# Use Ollama with the recommendation agent
agent = RecommendationAgent(llm_provider=OllamaProvider(model="llama3"))

response = agent.process_query("modern photography events")
print(response.message)
```

### Via Environment Variables

```bash
# Set environment
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3

# Run agent (will auto-detect Ollama)
poetry run python scripts/demo_interactive.py
```

## Test Ollama

```bash
# Make sure Ollama is running first
ollama serve  # in separate terminal

# Test the integration
poetry run python scripts/test_ollama.py
```

## Supported Models

You can use any model available in Ollama:

```bash
# List available models
ollama list

# Pull other models
ollama pull mistral
ollama pull codellama
ollama pull llama3:70b  # Larger Llama3 variant
```

Then use them:

```python
llm = OllamaProvider(model="mistral")
# or
llm = OllamaProvider(model="llama3:70b")
```

## Performance Tips

- **First run is slow**: Ollama loads the model into memory on first request
- **Subsequent runs are fast**: Model stays in memory
- **RAM requirements**: 
  - Llama3 (8B): ~8GB RAM
  - Llama3:70B: ~40GB RAM
- **GPU acceleration**: Ollama automatically uses Metal on macOS for faster inference

## Comparison with Mock and OpenAI

| Provider | Pros | Cons |
|----------|------|------|
| **Mock** | No setup, instant, free | Template responses, not intelligent |
| **Ollama** | Free, private, no API limits | Requires local setup, slower first run |
| **OpenAI** | Best quality, fast | Costs money, requires API key, sends data externally |

## Troubleshooting

### Connection Refused

```
RuntimeError: Ollama API error: Connection refused
```

**Solution**: Start Ollama server first:
```bash
ollama serve
```

### Model Not Found

```
Error: model 'llama3' not found
```

**Solution**: Pull the model:
```bash
ollama pull llama3
```

### Slow First Response

This is normal! Ollama loads the model into memory on first request (can take 10-30 seconds). Subsequent requests are much faster.

## Example: Full Flow with Ollama

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Run the agent
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3
poetry run python scripts/demo_interactive.py
```

Then query: "Show me modern art exhibitions in Barcelona"

The agent will use Llama3 locally to generate natural language responses!
