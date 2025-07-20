# GEMINI.md

This file provides guidance to Gemini when working with code in this repository.

## Project Overview

This is a Master's thesis project implementing a Multi-Agent Distributive Justice Experiment framework. The system simulates Rawls' "veil of ignorance" scenario where autonomous AI agents must reach unanimous agreement on distributive justice principles without knowing their future economic position. The architecture is service-oriented, allowing for flexible and modular experiment design.

## Architecture

**Core Framework**: Built on OpenAI Agents SDK with a structured multi-agent deliberation system.

**Key Components**:
- **src/maai/core/**: Core experiment logic and data models (`deliberation_manager.py`, `models.py`)
- **src/maai/agents/**: Enhanced agent classes with specialized roles (`enhanced.py`)
- **src/maai/config/**: YAML-based configuration management (`manager.py`)
- **src/maai/export/**: DEPRECATED legacy data export system.
- **src/maai/services/**: Service layer for experiment orchestration (`experiment_orchestrator.py`, `consensus_service.py`, `conversation_service.py`, `memory_service.py`, `evaluation_service.py`, `experiment_logger.py`)
- **configs/**: YAML configuration files for different experiment scenarios
- **experiment_results/**: Output directory for all experiment data

**Agent Classes**: 
- `DeliberationAgent` (src/maai/agents/enhanced.py:14): Main reasoning agents that debate principles (with configurable personalities)
- `DiscussionModerator` (src/maai/agents/enhanced.py:65): Manages conversation flow and speaking order.
- `FeedbackCollector` (src/maai/agents/enhanced.py:281): Conducts post-experiment interviews.

**Service Architecture**:
- `ExperimentOrchestrator` (src/maai/services/experiment_orchestrator.py): High-level coordination of all services.
- `ConsensusService` (src/maai/services/consensus_service.py): Multiple consensus detection strategies.
- `ConversationService` (src/maai/services/conversation_service.py): Communication pattern management.
- `MemoryService` (src/maai/services/memory_service.py): Agent memory management strategies.
- `EvaluationService` (src/maai/services/evaluation_service.py): Likert scale evaluation processing.
- `ExperimentLogger` (src/maai/services/experiment_logger.py): Unified agent-centric JSON logging system.

**Key Design Decisions**:
- **No Confidence Scores**: LLMs cannot reliably assess confidence, so confidence scoring has been removed entirely.
- **Code-Based Consensus**: Consensus detection uses simple ID matching rather than LLM assessment (src/maai/core/models.py:230).
- **Configurable Personalities**: Each agent can have a custom personality defined in YAML.
- **Neutral Descriptions**: Principle descriptions avoid references to philosophical authorities.
- **Likert Scale Evaluation**: 4-point scale for principle assessment (strongly disagree to strongly agree).
- **Unified JSON Logging**: A single, comprehensive JSON file is now the primary output, containing all experiment data in an agent-centric format.
- **Decomposed Memory Strategy**: A new memory strategy that uses focused, sequential prompts to improve memory quality.

### Distributive Justice Principles

The four principles tested are defined in `src/maai/core/models.py:208-229`:

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

**Single Experiment Runner**:
```bash
# Run with a specific configuration file
python run_experiment.py --config default

# Override the output directory
python run_experiment.py --config default --output-dir custom_experiments/my_test
```

**Batch Experiment Runner**:
```bash
# Run multiple experiments defined in run_batch.py
python run_batch.py
```

**Available Configurations**:
- `default`: Standard experimental setup
- `lucas`: Custom configuration for specific research scenarios
- `decomposed_memory_test`: Tests the new decomposed memory strategy.
- `temperature_test`: Tests different temperature settings for the models.

### Testing
```bash
# Run all tests (consolidated)
python tests/run_all_tests.py

# Run individual test directly
python tests/test_core.py
```

### Direct API Usage
```python
import asyncio
from src.maai.config.manager import load_config_from_file
from src.maai.core.deliberation_manager import run_single_experiment

# Load and run configuration
config = load_config_from_file('default')
results = await run_single_experiment(config)
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

memory_strategy: "decomposed" # or "full", "recent"

logging:
  enabled: true
  capture_raw_inputs: true
  capture_raw_outputs: true
  capture_memory_context: true
  capture_memory_steps: true
  include_processing_times: true
```

## Data Export System

**DEPRECATED**: The old data export system that produced multiple CSV and TXT files is deprecated.

**Unified Agent-Centric JSON Logging**:
The primary output is now a single, comprehensive JSON file in `experiment_results/`. This file is named `[experiment_id].json` and contains all data from the experiment in an agent-centric format.

The JSON structure includes:
- `experiment_metadata`: Overall experiment details, configuration, and final consensus results.
- `[agent_id]`: A top-level key for each agent, containing all their data.
  - `overall`: Agent's configuration (model, persona, etc.).
  - `round_0`: Initial evaluation data.
  - `round_[N]`: Detailed data for each deliberation round, including:
    - `public_history`: The conversation history provided to the agent.
    - `memory`: The agent's private memory entry for the round.
    - `strategy`: The agent's stated strategy for the round.
    - `communication`: The agent's public message to the group.
    - `choice`: The agent's principle choice for the round.
  - `final`: The agent's final consensus data.

## Environment Variables

**Required**:
- `OPENAI_API_KEY`: Primary model provider

**Optional**:
- `ANTHROPIC_API_KEY`: For Claude models
- `DEEPSEEK_API_KEY`: For DeepSeek models
- `GEMINI_API_KEY`: For Gemini models
- `XAI_API_KEY`: For Grok models
- `GROQ_API_KEY`: For Groq models

## Key Architecture Notes

**Core Classes**:
- `DeliberationManager` (src/maai/core/deliberation_manager.py:39): Facade for running experiments, coordinating services.
- `ExperimentOrchestrator` (src/maai/services/experiment_orchestrator.py): High-level coordinator of all services.
- `DeliberationAgent` (src/maai/agents/enhanced.py:14): Enhanced agents with structured outputs.
- `ExperimentConfig` (src/maai/core/models.py:133): Pydantic model for experiment configuration.
- `ExperimentLogger` (src/maai/services/experiment_logger.py): Unified agent-centric JSON logging system.

**Data Flow**:
1. Load YAML config via `load_config_from_file()` in `src/maai/config/manager.py`.
2. `ExperimentOrchestrator` initializes services (`ConsensusService`, `ConversationService`, `MemoryService`, `EvaluationService`, `ExperimentLogger`).
3. `ExperimentOrchestrator` runs the experiment through a series of phases (initial evaluation, deliberation, final evaluation).
4. `ExperimentLogger` captures all data in a structured, agent-centric format.
5. `ExperimentLogger` exports the final data to a single JSON file.

**Knowledge Base**:
- `knowledge_base/agents_sdk/`: Complete OpenAI Agents SDK documentation and examples
- `knowledge_base/best_practices/`: Practical guide to building agents (PDF and text)

## Experimental Flow

1. **Agent Initialization**: Create agents with "veil of ignorance" context.
2. **Initial Likert Evaluation**: Agents rate all 4 principles before deliberation.
3. **Multi-Round Deliberation**: Agents debate until unanimous agreement or timeout.
4. **Consensus Detection**: Validate group agreement on chosen principle.
5. **Final Likert Evaluation**: Agents re-rate all 4 principles after deliberation.
6. **Data Export**: Results saved to a single, unified JSON file.

## Implementation Notes

- Built on OpenAI Agents SDK with LitellmModel for multi-provider support.
- Supports GPT-4.1, GPT-4.1 mini/nano, Claude, DeepSeek, Gemini, Grok, and Llama models.
- All operations are async-first using asyncio.
- Pydantic models ensure data validation throughout the system.

## Advanced Service Configuration

The service architecture enables flexible research experimentation:

```python
# Example: Custom consensus and memory strategy
from src.maai.services.experiment_orchestrator import ExperimentOrchestrator
from src.maai.services.consensus_service import ThresholdBasedStrategy
from src.maai.services.memory_service import RecentMemoryStrategy

orchestrator = ExperimentOrchestrator(
    consensus_service=ConsensusService(detection_strategy=ThresholdBasedStrategy(threshold=0.8)),
    memory_service=MemoryService(memory_strategy=RecentMemoryStrategy(max_entries=3))
)

# Configure different experimental conditions
results = await orchestrator.run_experiment(config)
```

This allows researchers to A/B test different consensus mechanisms, communication patterns, and memory strategies without changing core code.

## Development Guidelines

### Code Style
- Use descriptive variable names and method names
- Prefer async/await patterns throughout
- All timestamps use `datetime` objects with UTC
- Pydantic models for all data structures
- Type hints on all function parameters and returns

### Testing
- All core functionality has unit tests in `tests/`.
- Run all tests with `python tests/run_all_tests.py`.
- Test files follow the pattern `test_*.py`.
- Mock external API calls in tests.

### Configuration Management
- All experiment parameters go in `configs/` YAML files.
- Use the `load_config_from_file()` function consistently.
- Validate all configs with Pydantic models.
- Default values defined in `DefaultConfig` class.

### Error Handling
- All async operations wrapped in try/catch.
- Graceful degradation when services fail.
- Detailed logging for debugging.

### File Structure Conventions
- Core logic in `src/maai/core/`
- Agent implementations in `src/maai/agents/`
- Service layer in `src/maai/services/`
- Configuration management in `src/maai/config/`
- Export functionality in `src/maai/export/` (legacy)
- All modules have `__init__.py` files.
