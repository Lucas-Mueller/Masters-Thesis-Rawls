# GEMINI.md

This file provides guidance to Gemini when working with code in this repository.

## Project Overview

This is a Master's thesis project implementing a Multi-Agent Distributive Justice Experiment framework. The system simulates Rawls' "veil of ignorance" scenario where autonomous AI agents must reach unanimous agreement on distributive justice principles without knowing their future economic position. The architecture is service-oriented, allowing for flexible and modular experiment design.

## Architecture

**Core Framework**: Built on OpenAI Agents SDK with a structured multi-agent deliberation system.

**Key Components**:
- **src/maai/core/**: Core experiment logic and data models (`deliberation_manager.py`, `models.py`)
- **src/maai/agents/**: Enhanced agent classes with specialized roles (`enhanced.py`, `summary_agent.py`)
- **src/maai/config/**: YAML-based configuration management (`manager.py`)
- **src/maai/export/**: DEPRECATED legacy data export system.
- **src/maai/services/**: Service layer for experiment orchestration. See **Service Architecture** below.
- **configs/**: YAML configuration files for different experiment scenarios
- **experiment_results/**: Output directory for all experiment data

**Agent Classes**: 
- `DeliberationAgent` (src/maai/agents/enhanced.py): Main reasoning agents that debate principles.
- `DiscussionModerator` (src/maai/agents/enhanced.py): Manages conversation flow and speaking order.
- `SummaryAgent` (src/maai/agents/summary_agent.py): Generates summaries of deliberation rounds.

**Service Architecture**:
The system uses a service-oriented architecture coordinated by the `ExperimentOrchestrator`.
- `ExperimentOrchestrator`: High-level coordinator of all services.
- `ConsensusService`: Detects consensus among agents.
- `ConversationService`: Manages the flow of conversation.
- `MemoryService`: Manages agent memories.
- `EvaluationService`: Handles principle evaluations.
- `ExperimentLogger`: Manages logging of experiment data.
- `PublicHistoryService`: Manages the public conversation history.
- `EconomicsService`: Handles economic calculations and outcomes.
- `PreferenceService`: Manages collection of agent preference rankings.
- `ValidationService`: Validates agent choices.
- `DetailedExamplesService`: Presents detailed examples of principles to agents.

**Key Design Decisions**:
- **Service-Oriented**: The architecture is highly modular, with specialized services for each major function. This allows for easy extension and modification of the experimental procedure.
- **Two-Phase Experiments**: The new experimental design consists of two phases: an individual familiarization phase and a group deliberation phase.
- **Code-Based Consensus**: Consensus detection uses simple ID matching rather than LLM assessment.
- **Configurable Personalities**: Each agent can have a custom personality defined in YAML.
- **Unified JSON Logging**: A single, comprehensive JSON file is now the primary output, containing all experiment data in an agent-centric format.

### Distributive Justice Principles

The four principles tested are defined in `src/maai/core/models.py`:

1. **Maximize the Minimum Income**: Ensures the worst-off are as well-off as possible.
2. **Maximize the Average Income**: Focuses on the greatest total income, regardless of distribution.
3. **Floor Constraint**: A hybrid principle that guarantees a minimum income and then maximizes the average.
4. **Range Constraint**: A hybrid principle that limits the inequality gap and then maximizes the average.

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
- `default`: Standard experimental setup.
- `lucas`: Custom configuration for specific research scenarios.
- `decomposed_memory_test`: Tests the new decomposed memory strategy.
- `temperature_test`: Tests different temperature settings for the models.

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
- Define experiment parameters (agents, rounds, timeouts, models).
- Specify output formats and directories.
- Configure agent personalities and behavior settings.
- Configure the new two-phase experimental flow.

**Example Configuration Structure**:
```yaml
experiment_id: my_experiment
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
# New game logic configuration
income_distributions:
  - distribution_id: 1
    name: "Distribution A"
    income_by_class:
      High: 100000
      Medium: 50000
      Low: 20000
payout_ratio: 0.0001
individual_rounds: 4
enable_detailed_examples: true
enable_secret_ballot: true
```

## Data Export System

**DEPRECATED**: The old data export system that produced multiple CSV and TXT files is deprecated.

**Unified Agent-Centric JSON Logging**:
The primary output is now a single, comprehensive JSON file in `experiment_results/`. This file is named `[experiment_id].json` and contains all data from the experiment in an agent-centric format.

The JSON structure includes:
- `experiment_metadata`: Overall experiment details, configuration, and final consensus results.
- `[agent_id]`: A top-level key for each agent, containing all their data.
  - `overall`: Agent's configuration (model, persona, etc.).
  - `assessments`: Pre- and post-experiment assessments.
  - `individual_rounds`: Data from the individual familiarization phase.
  - `deliberation_rounds`: Detailed data for each deliberation round.
  - `final_consensus`: The agent's final consensus data.

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
- `DeliberationManager` (src/maai/core/deliberation_manager.py): Facade for running experiments, coordinating services.
- `ExperimentOrchestrator` (src/maai/services/experiment_orchestrator.py): High-level coordinator of all services.
- `DeliberationAgent` (src/maai/agents/enhanced.py): Enhanced agents with structured outputs.
- `ExperimentConfig` (src/maai/core/models.py): Pydantic model for experiment configuration.
- `ExperimentLogger` (src/maai/services/experiment_logger.py): Unified agent-centric JSON logging system.

**Data Flow**:
1. Load YAML config via `load_config_from_file()` in `src/maai/config/manager.py`.
2. `ExperimentOrchestrator` initializes all services.
3. `ExperimentOrchestrator` runs the experiment through the two-phase flow.
4. `ExperimentLogger` captures all data in a structured, agent-centric format.
5. `ExperimentLogger` exports the final data to a single JSON file.

**Knowledge Base**:
- `knowledge_base/agents_sdk/`: Complete OpenAI Agents SDK documentation and examples
- `knowledge_base/best_practices/`: Practical guide to building agents (PDF and text)

## Experimental Flow

The new experimental flow is divided into two phases:

**Phase 1: Individual Familiarization**
1.  **Initial Preference Ranking**: Agents rank the four principles.
2.  **Detailed Examples**: Agents are presented with detailed examples of how each principle affects income distribution.
3.  **Second Assessment**: Agents rank the principles again after seeing the examples.
4.  **Individual Application Rounds**: Agents individually apply the principles for a set number of rounds and receive economic outcomes.
5.  **Third Assessment**: Agents rank the principles a final time based on their individual experiences.

**Phase 2: Group Experiment**
1.  **Group Deliberation**: Agents deliberate to reach a consensus on a single principle.
2.  **Secret Ballot**: If no consensus is reached, a secret ballot is held.
3.  **Group Economic Outcomes**: Economic outcomes are determined based on the group's decision.
4.  **Final Preference Ranking**: Agents provide a final ranking of the principles.
5.  **Data Export**: Results are saved to a single, unified JSON file.

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
- Use descriptive variable names and method names.
- Prefer async/await patterns throughout.
- All timestamps use `datetime` objects with UTC.
- Pydantic models for all data structures.
- Type hints on all function parameters and returns.

### Testing
- All core functionality has unit tests in `tests/`.
- Run all tests with `python tests/run_all_tests.py`.
- Test files follow the pattern `test_*.py`.
- Mock external API calls in tests.

### Configuration Management
- All experiment parameters go in `configs/` YAML files.
- Use the `load_config_from_file()` function consistently.
- Validate all configs with Pydantic models.
- Default values are defined in the `DefaultConfig` class.

### Error Handling
- All async operations are wrapped in try/catch blocks.
- The system is designed for graceful degradation when services fail.
- Detailed logging is available for debugging.

### File Structure Conventions
- Core logic in `src/maai/core/`
- Agent implementations in `src/maai/agents/`
- Service layer in `src/maai/services/`
- Configuration management in `src/maai/config/`
- Export functionality in `src/maai/export/` (legacy)
- All modules have `__init__.py` files.
