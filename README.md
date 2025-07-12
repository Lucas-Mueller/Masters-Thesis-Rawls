# Multi-Agent Distributive Justice Experiment Framework

A Master's thesis project implementing a computational simulation of Rawls' "veil of ignorance" scenario, where autonomous AI agents deliberate and reach unanimous agreement on distributive justice principles without knowing their future economic position.

## Overview

This framework simulates multi-agent deliberation on distributive justice using the OpenAI Agents SDK. Agents debate four different economic principles under conditions of uncertainty about their future roles in society, mimicking Rawls' original position thought experiment.

### Distributive Justice Principles

The system tests four economic distribution principles:

1. **Maximize the Minimum Income** - Ensures the worst-off are as well-off as possible (Rawlsian)
2. **Maximize the Average Income** - Focuses on greatest total income regardless of distribution (Utilitarian)
3. **Floor Constraint** - Hybrid approach with guaranteed minimum income plus average maximization
4. **Range Constraint** - Hybrid that limits inequality gap while maximizing average income

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
GROQ_API_KEY="your api key"
GEMINI_API_KEY="your gemini api key"

```
If you want to use monitoring when not using OpenAI models you can use AgentOps by setting 
this API key 
AGENT_OPS_API_KEY="your-agentops-key"

### Run Your First Experiment



```bash
source .venv/bin/activate

python run_config.py
```
## Configuration

Experiments are configured using YAML files in the `configs/` directory. Each configuration defines, if no values are given default values are used:

- Number of agents and deliberation rounds
- Agent personalities and AI models
- Output formats and directories
- Timeout and decision rules


### Example Configuration

```yaml
experiment_id: my_experiment
experiment:
  max_rounds: 5
  decision_rule: unanimity
  timeout_seconds: 300

agents:
  - name: "Agent_1"
    model: "gpt-4o-mini"
    personality: "You are an economist focused on efficiency and optimal resource allocation."
  - name: "Agent_2"
    model: "gpt-4o"
    personality: "You are a philosopher concerned with justice and fairness for all members of society."

output:
  directory: experiment_results
  formats: [json, csv, txt]
  include_feedback: true
```

## Architecture

### Core Components

- **`src/maai/core/`** - Core experiment logic and data models
- **`src/maai/agents/`** - Enhanced agent classes with specialized roles
- **`src/maai/services/`** - Service layer for experiment orchestration
- **`src/maai/config/`** - YAML-based configuration management
- **`src/maai/export/`** - Multi-format data export system
- **`configs/`** - YAML configuration files for different scenarios
- **`experiment_results/`** - Output directory for all experiment data

### Key Agent Classes

- **`DeliberationAgent`** - Main reasoning agents that debate principles with configurable personalities
- **`DiscussionModerator`** - Manages conversation flow and speaking order
- **`FeedbackCollector`** - Conducts post-experiment interviews

### Service Architecture

- **`ExperimentOrchestrator`** - High-level coordination of all services
- **`ConsensusService`** - Multiple consensus detection strategies
- **`ConversationService`** - Communication pattern management
- **`MemoryService`** - Agent memory management strategies
- **`EvaluationService`** - Likert scale evaluation processing



### Available Configurations

- **`quick_test`** - 3 agents, 2 rounds (1-2 minutes)
- **`lucas`** - Custom configuration for specific research scenarios
- **`smart`** - Different AI models with custom personalities
- **`default`** - Standard experimental setup
- **`test_custom`** - Template for custom configurations

## Running Experiments

### Command Line Interface

```bash
# Universal configuration runner
python run_config.py
# Edit CONFIG_NAME variable on line 27 to switch configurations

# Quick test run
python run_quick_demo.py

# Demo systems
python demos/demo_phase1.py  # Core multi-agent deliberation
python demos/demo_phase2.py  # Enhanced features

# Advanced service usage examples
python example_service_usage.py
```

### Programmatic API

```python
import asyncio
from src.maai.config.manager import load_config_from_file
from src.maai.core.deliberation_manager import run_single_experiment

# Load and run configuration
config = load_config_from_file('quick_test')
results = await run_single_experiment(config)
```

### Advanced Service Configuration

```python
from src.maai.services.experiment_orchestrator import ExperimentOrchestrator

orchestrator = ExperimentOrchestrator(
    consensus_strategy="threshold",  # or "id_match", "semantic"
    conversation_pattern="sequential",  # or "random", "hierarchical"
    memory_strategy="recent"  # or "full", "selective"
)

results = await orchestrator.run_experiment(config)
```

## Experimental Process

1. **Agent Initialization** - Create agents with "veil of ignorance" context
2. **Initial Evaluation** - Agents rate all 4 principles on Likert scale before deliberation
3. **Multi-Round Deliberation** - Agents debate until unanimous agreement or timeout
4. **Consensus Detection** - Validate group agreement on chosen principle
5. **Final Evaluation** - Agents re-rate all 4 principles after deliberation
6. **Data Export** - Results saved in multiple formats for analysis

## Data Export

Experiment results are automatically saved to `experiment_results/` in multiple formats:

- **`[ID]_complete.json`** - Full structured experiment data
- **`[ID]_data.csv`** - Main conversation transcript data
- **`[ID]_initial_evaluation.csv`** - Pre-deliberation principle ratings
- **`[ID]_evaluation.csv`** - Post-consensus principle evaluations
- **`[ID]_comparison.csv`** - Before/after rating comparison analysis
- **`[ID]_transcript.txt`** - Human-readable conversation log

## Testing

```bash
# Run all tests
python run_tests.py

# Run individual test files
python tests/test_core.py
```

## Key Design Features

- **No Confidence Scores** - LLMs cannot reliably assess confidence, so confidence scoring is avoided
- **Code-Based Consensus** - Consensus detection uses ID matching rather than LLM assessment
- **Configurable Personalities** - Each agent can have custom personality defined in YAML
- **Neutral Descriptions** - Principle descriptions avoid references to philosophical authorities
- **Multi-Provider Support** - Works with OpenAI, Anthropic Claude, and DeepSeek models
- **AgentOps Integration** - Optional experiment tracing and monitoring



## Development

### File Structure

```
src/maai/
├── core/          # Core experiment logic and data models
├── agents/        # Agent implementations
├── services/      # Service layer
├── config/        # Configuration management
└── export/        # Data export functionality

configs/           # YAML configuration files
tests/            # Unit and integration tests
experiment_results/ # Output directory
knowledge_base/   # Documentation and examples
```

### Code Style Guidelines

- Use async/await patterns throughout
- Type hints on all function parameters and returns
- Pydantic models for all data structures
- Descriptive variable and method names
- UTC timestamps with `datetime` objects

## Contributing

This is a Master's thesis research project. For questions or collaboration opportunities, please refer to the academic institution guidelines.

## License

Academic research project - see institution guidelines for usage terms.I 