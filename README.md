# Multi-Agent Distributive Justice Experiment Framework

A Master's thesis project implementing a **two-phase economic incentive-based game** where autonomous AI agents make decisions about distributive justice principles with real economic consequences. Unlike traditional "veil of ignorance" approaches, agents receive actual monetary payouts based on their income class assignments after choosing principles.

## Overview

This framework implements a novel **economic incentive-based approach** to studying distributive justice using the OpenAI Agents SDK. The system features a two-phase structure where agents first familiarize themselves with principles through individual application rounds, then engage in group deliberation with real economic stakes.

### Game Logic Structure

**Phase 1: Individual Familiarization**
- **Initial Preference Ranking**: Agents rank all 4 principles (1-4) with certainty levels
- **Detailed Examples**: Agents review concrete income distribution examples for each principle  
- **Individual Application Rounds**: Agents apply principles in economic scenarios (configurable rounds, default 4)
- **Post-Individual Ranking**: Agents re-rank principles after gaining experience

**Phase 2: Group Experiment**
- **Group Deliberation**: Multi-round discussion to reach unanimous agreement on one principle
- **Economic Outcomes**: Apply agreed principle to determine each agent's income class and payout
- **Final Preference Ranking**: Agents provide final rankings after seeing group outcomes

### Distributive Justice Principles

The system tests four economic distribution principles:

1. **MAXIMIZING THE FLOOR INCOME** - The most just distribution maximizes the income received by the poorest member of society (Rawlsian difference principle)
2. **MAXIMIZING THE AVERAGE INCOME** - The most just distribution maximizes the average income across all members, regardless of distribution inequality  
3. **MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT** - Maximize average income while guaranteeing a specified minimum income to everyone (requires floor constraint parameter)
4. **MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT** - Maximize average income while limiting the income difference between richest and poorest (requires range constraint parameter)

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

```bash
git clone <repository-url>
cd Masters-Thesis-Rawls-
pip install -r requirements.txt
```

### Environment Setup

Set required environment variable in a .env file:
```
OPENAI_API_KEY="your-api-key"
```

Optional API keys for additional model providers:
```bash
ANTHROPIC_API_KEY="your-claude-key"
DEEPSEEK_API_KEY="your-deepseek-key"
GROQ_API_KEY="your-groq-key"
GEMINI_API_KEY="your-gemini-key"
```

### Run Your First Experiment

**Single Experiment:**
```bash
# Run with new game logic (recommended)
python run_experiment.py --config new_game_basic

# Run with specific configuration
python run_experiment.py --config lucas

# Run with custom output directory
python run_experiment.py --config new_game_basic --output-dir custom_experiments/test_run
```

**Batch Experiments:**
```bash
# Run multiple experiments in parallel
python run_batch.py

# Generate configuration variations
python config_generator.py
```

**Direct API Usage:**
```python
import asyncio
from run_experiment import run_experiment

# Run experiment programmatically
results = await run_experiment('lucas')
print(f"Results saved to: {results['output_path']}")
```

## Configuration

Experiments are configured using YAML files in the `configs/` directory. Each configuration defines:

- Number of agents and deliberation rounds
- Agent personalities and AI models
- Output formats and directories
- Timeout and decision rules
- Memory strategies and temperature settings

### Available Configurations

- `new_game_basic` - **Recommended starting point** - Basic configuration for new game logic system
- `lucas` - Custom configuration for specific research scenarios
- `decomposed_memory_test` - 3 agents with decomposed memory strategy
- `temperature_test` - Reproducible experiments with temperature=0.0
- `default` - Legacy experimental setup (pre-new game logic)
- `comprehensive_example` - Full-featured configuration example

### Example Configuration

```yaml
experiment_id: new_game_example
global_temperature: 0.0  # For reproducible results

experiment:
  max_rounds: 5
  decision_rule: unanimity
  timeout_seconds: 300

# New game logic configuration
individual_rounds: 4  # Number of individual application rounds
payout_ratio: 0.0001  # $0.0001 per $1 of income (e.g., $20,000 income = $2.00 payout)
enable_detailed_examples: true
enable_secret_ballot: true

# Income distribution scenarios
income_distributions:
  - distribution_id: 1
    name: "Distribution A"
    income_by_class:
      HIGH: 50000
      MEDIUM_HIGH: 40000
      MEDIUM: 30000
      MEDIUM_LOW: 20000
      LOW: 10000
  - distribution_id: 2
    name: "Distribution B"
    income_by_class:
      HIGH: 45000
      MEDIUM_HIGH: 35000
      MEDIUM: 25000
      MEDIUM_LOW: 18000
      LOW: 12000

memory_strategy: "decomposed"

agents:
  - name: "Economist"
    model: "gpt-4.1-mini"
    personality: "You are an economist focused on efficiency and optimal resource allocation."
  - name: "Philosopher"
    model: "gpt-4.1-mini"
    personality: "You are a philosopher concerned with justice and fairness for all members of society."

defaults:
  personality: "You are an agent participating in an economic experiment."
  model: "gpt-4.1-mini"
  temperature: 0.1

output:
  directory: experiment_results
  formats: [json]
```

## Architecture

### Core Components

- **`src/maai/core/`** - Core experiment logic and data models
- **`src/maai/agents/`** - Enhanced agent classes with specialized roles
- **`src/maai/services/`** - Service layer for experiment orchestration
- **`src/maai/config/`** - YAML-based configuration management
- **`configs/`** - YAML configuration files for different scenarios
- **`experiment_results/`** - Output directory for all experiment data

### Key Agent Classes

- **`DeliberationAgent`** - Main reasoning agents that debate principles with configurable personalities
- **`DiscussionModerator`** - Manages conversation flow and speaking order
- **`FeedbackCollector`** - Conducts post-experiment interviews

### Service Architecture

- **`ExperimentOrchestrator`** - High-level coordination of two-phase experiment flow
- **`ConsensusService`** - Multiple consensus detection strategies with constraint handling for principles 3 & 4  
- **`ConversationService`** - Communication pattern management (sequential, random, hierarchical)
- **`MemoryService`** - Agent memory management strategies (full, recent, decomposed)
- **`EconomicsService`** - Income distribution management and economic outcome calculation
- **`PreferenceService`** - Preference ranking collection and analysis (replaces Likert scale evaluation)
- **`ValidationService`** - Principle choice validation and constraint requirement checking
- **`ExperimentLogger`** - Comprehensive agent-centric experiment data collection

### Advanced Service Configuration

```python
from src.maai.services.experiment_orchestrator import ExperimentOrchestrator

orchestrator = ExperimentOrchestrator(
    consensus_strategy="threshold",  # or "id_match", "semantic"
    conversation_pattern="sequential",  # or "random", "hierarchical"
    memory_strategy="decomposed"  # or "full", "recent"
)

results = await orchestrator.run_experiment(config)
```

## Experimental Process

**Phase 1: Individual Familiarization**
1. **Agent Initialization** - Create agents with economic incentive context and income distribution scenarios
2. **Initial Preference Ranking** - Agents rank all 4 principles (1-4) with certainty levels  
3. **Detailed Examples** - Agents review concrete income distribution examples for each principle
4. **Individual Application Rounds** - Agents apply principles in multiple economic scenarios (default 4 rounds)
5. **Post-Individual Ranking** - Agents re-rank principles after gaining hands-on experience

**Phase 2: Group Experiment**
1. **Group Deliberation** - Multi-round discussion to reach unanimous agreement on one principle
2. **Consensus Detection** - Validate group agreement with constraint handling for principles 3 & 4
3. **Economic Outcomes** - Apply agreed principle to assign income classes and calculate real payouts
4. **Final Preference Ranking** - Agents provide final rankings after experiencing group outcomes
5. **Data Export** - Comprehensive agent-centric data export with all interactions and outcomes

## Data Export

Experiment results are automatically saved to `experiment_results/` (or custom directory) as comprehensive agent-centric JSON files:

- **`[ID].json`** - **Single unified file with complete experiment data** including:
  - Agent-centric organization with individual and group interaction data
  - Complete preference rankings (initial, post-individual, final) with certainty levels
  - Economic outcomes for all individual and group rounds
  - Full conversation transcripts with agent strategies and reasoning
  - Comprehensive metadata and experiment flow tracking
  - **No output truncation** - All agent outputs and reasoning stored in full

**Legacy formats** (for backward compatibility):
- **`[ID]_complete.json`** - Full structured experiment data (legacy format)  
- **`[ID]_data.csv`** - Main conversation transcript data
- **`[ID]_transcript.txt`** - Human-readable conversation log

**Batch Experiment Results** are organized into timestamped directories with consolidated analysis.

## Testing

```bash
# Run all tests (comprehensive)
python tests/run_all_tests.py

# Run with pytest
python tests/run_all_tests.py --pytest

# Run individual test files
python tests/test_core.py
python tests/test_decomposed_memory.py
python tests/test_experiment_logger.py
python tests/test_consensus_service.py
python tests/test_integration.py

# Run with pytest directly
pytest tests/ -v --tb=short
```

## Key Design Features

- **Economic Incentive-Based** - Agents receive real monetary payouts based on income assignments, not philosophical reasoning
- **Two-Phase Structure** - Phase 1 (Individual Familiarization) + Phase 2 (Group Deliberation)  
- **Preference Rankings** - 1-4 rankings with certainty levels replace Likert scale evaluation
- **Income Distributions** - Multiple distribution scenarios with 5 income classes each (HIGH, MEDIUM_HIGH, MEDIUM, MEDIUM_LOW, LOW)
- **Constraint Handling** - Automatic default values for principle 3 (floor) and 4 (range) constraints when not specified
- **Code-Based Consensus** - Consensus detection uses ID matching with constraint validation
- **Configurable Personalities** - Each agent can have custom personality defined in YAML
- **Multi-Provider Support** - Works with OpenAI, Anthropic Claude, DeepSeek, Groq, and Gemini models
- **No Output Truncation** - All agent outputs, messages, and reasoning stored in full
- **Parallel Execution** - Batch experiments run concurrently with rate limiting
- **Memory Strategies** - Multiple approaches to agent memory management (full, recent, decomposed)

## Parallel Execution System

The framework supports parallel batch execution for improved performance:

- **Speed**: ~3x faster execution with default settings (3 concurrent experiments)
- **Scalability**: Adjustable concurrency based on API rate limits
- **Resilience**: Individual experiment failures don't block others
- **Performance Metrics**: Detailed speedup and efficiency analysis

## Development

### File Structure

```
src/maai/
├── core/          # Core experiment logic and data models
├── agents/        # Agent implementations
├── services/      # Service layer
├── config/        # Configuration management
└── export/        # Data export functionality (legacy)

configs/           # YAML configuration files
tests/            # Unit and integration tests
experiment_results/ # Default output directory
custom_experiments/ # Custom experiment outputs
knowledge_base/   # Documentation and examples
docs/             # Additional documentation and visualization tools
```

### Code Style Guidelines

- Use async/await patterns throughout
- Type hints on all function parameters and returns
- Pydantic models for all data structures
- Descriptive variable and method names
- UTC timestamps with `datetime` objects
- **Never truncate output** - Store all agent messages and reasoning in full

### Knowledge Base

- **`knowledge_base/agents_sdk/`** - Complete OpenAI Agents SDK documentation and examples
- **`knowledge_base/best_practices/`** - Practical guide to building agents (PDF and text)
- **`knowledge_base/feature_plan/`** - Development roadmaps and analysis

## Analysis and Visualization

- **Jupyter Notebooks** - `Experiment.ipynb` for main analysis
- **Visualization Tools** - `docs/visualization/generate_overview.py` for system overview
- **Memory Analysis** - `docs/memory_strategies_guide.md` for memory strategy documentation

## Contributing

This is a Master's thesis research project. For questions or collaboration opportunities, please refer to the academic institution guidelines.

## License

Academic research project - see institution guidelines for usage terms.