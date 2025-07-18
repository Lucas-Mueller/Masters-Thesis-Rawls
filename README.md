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
GROQ_API_KEY="your-groq-key"
GEMINI_API_KEY="your-gemini-key"
```

### Run Your First Experiment

**Single Experiment:**
```bash
# Run with default configuration
python run_experiment.py

# Run with specific configuration
python run_experiment.py --config lucas

# Run with custom output directory
python run_experiment.py --config default --output-dir custom_experiments/test_run
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

- `lucas` - Custom configuration for specific research scenarios (default)
- `decomposed_memory_test` - 3 agents with decomposed memory strategy
- `temperature_test` - Reproducible experiments with temperature=0.0
- `default` - Standard experimental setup
- `comprehensive_example` - Full-featured configuration example

### Example Configuration

```yaml
experiment_id: my_experiment
global_temperature: 0.0  # For reproducible results

experiment:
  max_rounds: 5
  decision_rule: unanimity
  timeout_seconds: 300

# Memory strategy configuration
memory_strategy: "decomposed"  # or "full", "recent"

agents:
  - name: "Agent_1"
    model: "gpt-4.1-mini"
    personality: "You are an economist focused on efficiency and optimal resource allocation."
    temperature: 0.0
  - name: "Agent_2"
    model: "gpt-4.1"
    personality: "You are a philosopher concerned with justice and fairness for all members of society."

defaults:
  personality: "You are an agent tasked to design a future society."
  model: "gpt-4.1-mini"
  temperature: 0.1

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
- **`configs/`** - YAML configuration files for different scenarios
- **`experiment_results/`** - Output directory for all experiment data

### Key Agent Classes

- **`DeliberationAgent`** - Main reasoning agents that debate principles with configurable personalities
- **`DiscussionModerator`** - Manages conversation flow and speaking order
- **`FeedbackCollector`** - Conducts post-experiment interviews

### Service Architecture

- **`ExperimentOrchestrator`** - High-level coordination of all services
- **`ConsensusService`** - Multiple consensus detection strategies (id_match, threshold, semantic)
- **`ConversationService`** - Communication pattern management (sequential, random, hierarchical)
- **`MemoryService`** - Agent memory management strategies (full, recent, decomposed)
- **`EvaluationService`** - Likert scale evaluation processing
- **`ExperimentLogger`** - Comprehensive single-file experiment data collection

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

1. **Agent Initialization** - Create agents with "veil of ignorance" context
2. **Initial Likert Evaluation** - Agents rate all 4 principles before deliberation
3. **Multi-Round Deliberation** - Agents debate until unanimous agreement or timeout
4. **Consensus Detection** - Validate group agreement on chosen principle
5. **Final Likert Evaluation** - Agents re-rate all 4 principles after deliberation
6. **Data Export** - Results saved in multiple formats for analysis

## Data Export

Experiment results are automatically saved to `experiment_results/` (or custom directory) in multiple formats:

- **`[ID].json`** - Full structured experiment data (single file format) - **Complete data with no truncation**
- **`[ID]_complete.json`** - Full structured experiment data (legacy format)
- **`[ID]_data.csv`** - Main conversation transcript data
- **`[ID]_initial_evaluation.csv`** - Pre-deliberation principle ratings
- **`[ID]_initial_evaluation.json`** - Initial ratings with statistics
- **`[ID]_evaluation.csv`** - Post-consensus principle evaluations
- **`[ID]_evaluation.json`** - Final ratings with statistics
- **`[ID]_comparison.csv`** - Before/after rating comparison analysis
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

- **No Confidence Scores** - LLMs cannot reliably assess confidence, so confidence scoring is avoided
- **Code-Based Consensus** - Consensus detection uses ID matching rather than LLM assessment
- **Configurable Personalities** - Each agent can have custom personality defined in YAML
- **Neutral Descriptions** - Principle descriptions avoid references to philosophical authorities
- **Multi-Provider Support** - Works with OpenAI, Anthropic Claude, DeepSeek, Groq, and Gemini models
- **No Output Truncation** - All agent outputs, messages, and reasoning stored in full
- **Parallel Execution** - Batch experiments run concurrently with rate limiting
- **Memory Strategies** - Multiple approaches to agent memory management

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