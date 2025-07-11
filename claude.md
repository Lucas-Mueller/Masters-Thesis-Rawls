# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Master's thesis project implementing a Multi-Agent Distributive Justice Experiment framework. The system simulates Rawls' "veil of ignorance" scenario where autonomous AI agents must reach unanimous agreement on distributive justice principles without knowing their future economic position.

## Architecture

**Core Framework**: Built on OpenAI Agents SDK with structured multi-agent deliberation system

**Key Components**:
- **src/maai/core/**: Core experiment logic and data models (`deliberation_manager.py`, `models.py`)
- **src/maai/agents/**: Enhanced agent classes with specialized roles (`enhanced.py`)
- **src/maai/config/**: YAML-based configuration management (`manager.py`)
- **src/maai/export/**: Multi-format data export system (`data_export.py`)
- **configs/**: YAML configuration files for different experiment scenarios
- **experiment_results/**: Output directory for all experiment data

**Agent Classes**: 
- `DeliberationAgent`: Main reasoning agents that debate principles (with configurable personalities)
- `DiscussionModerator`: Manages conversation flow and speaking order
- `FeedbackCollector`: Conducts post-experiment interviews

**Service Architecture** (Advanced):
- `ExperimentOrchestrator`: High-level coordination of all services
- `ConsensusService`: Multiple consensus detection strategies (ID matching, threshold-based, semantic similarity)
- `ConversationService`: Communication pattern management (random, sequential, hierarchical)
- `MemoryService`: Agent memory management strategies (full, recent, selective)

**Key Design Decisions**:
- **No Confidence Scores**: LLMs cannot reliably assess confidence, so confidence scoring has been removed entirely
- **Code-Based Consensus**: Consensus detection uses simple ID matching rather than LLM assessment
- **Configurable Personalities**: Each agent can have a custom personality defined in YAML
- **Neutral Descriptions**: Principle descriptions avoid references to philosophical authorities

### Distributive Justice Principles
1. **Maximize the Minimum Income**: Ensures worst-off are as well-off as possible
2. **Maximize the Average Income**: Focuses on greatest total income regardless of distribution  
3. **Floor Constraint**: Hybrid with guaranteed minimum income plus maximizing average
4. **Range Constraint**: Hybrid that limits inequality gap plus maximizing average

## Development Commands

### Setup and Installation
```bash
pip install -r requirements.txt
```

### Running Experiments

**Quick Test (3 agents, 2 rounds)**:
```bash
python run_quick_demo.py
```

**Universal Configuration Runner**:
```bash
python run_config.py
# Edit CONFIG_NAME variable on line 20 to switch configurations
```

**Available Configurations**:
- `quick_test`: 3 agents, 2 rounds (1-2 minutes)
- `lucas`: Custom configuration for specific research scenarios
- `default`: Standard experimental setup
- `test_custom`: Template for custom configurations

### Testing
```bash
# Run all tests (consolidated)
python run_tests.py

# Run individual test directly
python tests/test_core.py
```

### Direct API Usage
```python
import asyncio
from src.maai.config.manager import load_config_from_file
from src.maai.core.deliberation_manager import run_single_experiment

# Load and run configuration
config = load_config_from_file('quick_test')
results = await run_single_experiment(config)
```

### Demo System
```bash
# Phase 1: Core multi-agent deliberation
python demos/demo_phase1.py

# Phase 2: Enhanced features (feedback, export, configuration)
python demos/demo_phase2.py

# Advanced service usage examples
python example_service_usage.py
```

## Configuration System

**YAML Configuration Files** in `configs/`:
- Define experiment parameters (agents, rounds, timeouts, models)
- Specify output formats and directories
- Configure agent personalities and behavior settings

**Personality System**:
- Each agent can have a custom personality defined in the `agents` array
- If fewer agents are specified, remaining agents use the `defaults` configuration
- Personalities can be full text descriptions or references to saved personality templates
- Default personality: "You are an agent tasked to design a future society."

**Example Configuration Structure**:
```yaml
experiment_id: my_experiment
experiment:
  max_rounds: 5
  decision_rule: unanimity
  timeout_seconds: 300

agents:
  - name: "Agent_1"
    model: "gpt-4.1-mini"
    personality: "You are an economist focused on efficiency and optimal resource allocation."
  - name: "Agent_2"
    model: "gpt-4.1"
    personality: "You are a philosopher concerned with justice and fairness for all members of society."
  - name: "Agent_3"
    model: "gpt-4.1-mini"
    personality: "You are a pragmatist who focuses on what works in practice rather than theory."

defaults:
  personality: "You are an agent tasked to design a future society."
  model: "gpt-4.1-mini"

output:
  directory: experiment_results
  formats: [json, csv, txt]
  include_feedback: true
```

## Data Export System

**Experiment Results** are saved to `experiment_results/` with multiple formats:
- `[ID]_complete.json`: Full structured experiment data
- `[ID]_summary.csv`: Key metrics and outcomes
- `[ID]_transcript.csv`: Complete conversation data
- `[ID]_feedback.csv`: Post-experiment agent feedback
- `[ID]_choice_evolution.csv`: How agent choices changed over time
- `[ID]_agent_memories.csv`: Agent memory states throughout experiment
- `[ID]_speaking_orders.csv`: Communication patterns and turn order
- `[ID]_transcript.txt`: Human-readable conversation log
- `[ID]_summary.txt`: Executive summary of results

## Environment Variables

**Required**:
- `OPENAI_API_KEY`: Primary model provider

**Optional**:
- `ANTHROPIC_API_KEY`: For Claude models
- `DEEPSEEK_API_KEY`: For DeepSeek models
- `AGENT_OPS_API_KEY`: For AgentOps monitoring (session named with experiment ID)

## Key Architecture Notes

**Core Classes**:
- `DeliberationManager` (src/maai/core/deliberation_manager.py:42): Main orchestrator for multi-round experiments
- `DeliberationAgent` (src/maai/agents/enhanced.py:14): Enhanced agents with structured outputs
- `ExperimentConfig` (src/maai/core/models.py): Pydantic model for experiment configuration
- `PrincipleChoice` (src/maai/core/models.py:11): Structured agent decision representation

**Data Flow**:
1. Load YAML config via `load_config_from_file()` in `src/maai/config/manager.py`
2. Create agents with personality configurations
3. Run deliberation rounds through `DeliberationManager`
4. Export results via `export_experiment_data()` in `src/maai/export/data_export.py`

**Knowledge Base**:
- `knowledge_base/agents_sdk/`: Complete OpenAI Agents SDK documentation and examples
- `knowledge_base/best_practices/`: Practical guide to building agents (PDF and text)
- `knowledge_base/agentops/`: AgentOps integration documentation and examples

## Experimental Flow

1. **Agent Initialization**: Create agents with "veil of ignorance" context
2. **Multi-Round Deliberation**: Agents debate until unanimous agreement or timeout
3. **Consensus Detection**: Validate group agreement on chosen principle
4. **Feedback Collection**: Post-experiment interviews with agents
5. **Data Export**: Results saved in multiple formats for analysis

## Implementation Notes

- Built on OpenAI Agents SDK with LitellmModel for multi-provider support
- Supports GPT-4.1, GPT-4.1 mini/nano, Claude, and DeepSeek models
- All operations are async-first using asyncio
- Pydantic models ensure data validation throughout the system
- AgentOps integration provides experiment tracing and monitoring (conditional based on model providers)

## Advanced Service Configuration

The service architecture enables flexible research experimentation:

```python
# Example: Custom consensus strategy
from src.maai.services.experiment_orchestrator import ExperimentOrchestrator

orchestrator = ExperimentOrchestrator(
    consensus_strategy="threshold",  # or "id_match", "semantic"
    conversation_pattern="sequential",  # or "random", "hierarchical"
    memory_strategy="recent"  # or "full", "selective"
)

# Configure different experimental conditions
results = await orchestrator.run_experiment(config)
```

This allows researchers to A/B test different consensus mechanisms, communication patterns, and memory strategies without changing core code.

At the end of this message, I will ask you to do something. Please follow the "Explore, Plan, Code, Test" workflow when you start.

Explore
First, use parallel subagents to find and read all files that may be useful for implementing the ticket, either as examples or as edit targets. The subagents should return relevant file paths, and any other info that may be useful.

Plan
Next, think hard and write up a detailed implementation plan. Don't forget to include tests, lookbook components, and documentation. Use your judgement as to what is necessary, given the standards of this repo.

If there are things you are not sure about, use parallel subagents to do some web research. They should only return useful information, no noise.

If there are things you still do not understand or questions you have for the user, pause here to ask them before continuing.

Code
When you have a thorough implementation plan, you are ready to start writing code. Follow the style of the existing codebase (e.g. we prefer clearly named variables and methods to extensive comments). Make sure to run our autoformatting script when you're done, and fix linter warnings that seem reasonable to you.

Test
Use parallel subagents to run tests, and make sure they all pass.

If your changes touch the UX in a major way, use the browser to make sure that everything works correctly. Make a list of what to test for, and use a subagent for this step.

If your testing shows problems, go back to the planning stage and think ultrahard.

Write up your work
When you are happy with your work, write up a short report that could be used as the PR description. Include what you set out to do, the choices you made with their brief justification, and any commands you ran in the process that may be useful for future developers to know about.