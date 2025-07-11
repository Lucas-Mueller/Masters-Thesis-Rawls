# AgentOps OpenAI Agents SDK Integration

## Overview
AgentOps provides seamless integration with OpenAI Agents SDK for monitoring and tracking agent workflows.

## Key Integration Points

### 1. Installation
- Install AgentOps SDK: `pip install agentops`
- Install OpenAI Agents SDK: `pip install openai-agents`

### 2. Initialization
- Call `agentops.init()` before using any models
- Can set API key via environment variables or direct initialization

### 3. Core Concepts
- Supports "Agents" with:
  - Instructions
  - Tools
  - Guardrails
  - Handoffs

### 4. Tracing Mechanism
- Automatically tracks agent runs
- Provides "built-in tracking of agent runs"
- Allows viewing, debugging, and optimizing workflows

### 5. Agent Loop Workflow
The SDK runs a loop that:
- Calls LLM with agent settings
- Processes responses
- Handles tool calls
- Manages potential agent handoffs
- Terminates when final output is produced

## Example Integration
```python
import agentops
from agents import Agent, Runner

agentops.init()

agent = Agent(
    name="Assistant", 
    instructions="You are a helpful assistant"
)

result = Runner.run_sync(agent, "Write a haiku about recursion")
```

## Integration Benefits
- Seamless monitoring of multi-agent workflows
- Minimal additional configuration required
- Built-in tracking and analytics
- Debugging and optimization capabilities