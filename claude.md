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
- `lucas`: Custom configuration
- `large_group`: 8 agents, 10 rounds (5-10 minutes)
- `multi_model`: Uses different AI models (GPT-4.1, Claude, DeepSeek)
- `default`: Standard experimental setup

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

## Configuration System

**YAML Configuration Files** in `configs/`:
- Define experiment parameters (agents, rounds, timeouts, models)
- Specify output formats and directories
- Configure agent personalities and behavior settings

**Personality System**:
- Each agent can have a custom personality defined in the `personalities` array
- If fewer personalities than agents are specified, remaining agents use the default: "You are an agent tasked to design a future society."
- Personalities can be full text descriptions or references to saved personality templates

**Example Configuration Structure**:
```yaml
experiment_id: my_experiment
experiment:
  num_agents: 3
  max_rounds: 5
  decision_rule: unanimity
  timeout_seconds: 300
  models: [gpt-4.1-mini, gpt-4.1, gpt-4.1-mini]

personalities:
  - "You are an economist focused on efficiency and optimal resource allocation."
  - "You are a philosopher concerned with justice and fairness for all members of society."
  - "You are a pragmatist who focuses on what works in practice rather than theory."

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
- `[ID]_transcript.txt`: Human-readable conversation log
- `[ID]_summary.txt`: Executive summary of results

## Environment Variables

**Required**:
- `OPENAI_API_KEY`: Primary model provider

**Optional**:
- `ANTHROPIC_API_KEY`: For Claude models
- `DEEPSEEK_API_KEY`: For DeepSeek models
- `AGENT_OPS_API_KEY`: For agent operations tracking

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
- AgentOps integration provides experiment tracing and monitoring