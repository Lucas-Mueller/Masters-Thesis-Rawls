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
- **src/maai/services/**: Service layer for experiment orchestration
- **configs/**: YAML configuration files for different experiment scenarios
- **experiment_results/**: Output directory for all experiment data

**Agent Classes**: 
- `DeliberationAgent` (src/maai/agents/enhanced.py:14): Main reasoning agents that debate principles (with configurable personalities)
- `DiscussionModerator` (src/maai/agents/enhanced.py:65): Manages conversation flow and speaking order
- `FeedbackCollector`: Conducts post-experiment interviews

**Service Architecture**:
- `ExperimentOrchestrator` (src/maai/services/experiment_orchestrator.py): High-level coordination of all services
- `ConsensusService` (src/maai/services/consensus_service.py): Multiple consensus detection strategies
- `ConversationService` (src/maai/services/conversation_service.py): Communication pattern management
- `MemoryService` (src/maai/services/memory_service.py): Agent memory management strategies
- `EvaluationService` (src/maai/services/evaluation_service.py): Likert scale evaluation processing
- `ExperimentLogger` (src/maai/services/experiment_logger.py): Comprehensive single-file experiment data collection

**Key Design Decisions**:
- **No Confidence Scores**: LLMs cannot reliably assess confidence, so confidence scoring has been removed entirely
- **Code-Based Consensus**: Consensus detection uses simple ID matching rather than LLM assessment (src/maai/core/models.py:230)
- **Configurable Personalities**: Each agent can have a custom personality defined in YAML
- **Neutral Descriptions**: Principle descriptions avoid references to philosophical authorities
- **Likert Scale Evaluation**: 4-point scale for principle assessment (strongly disagree to strongly agree)

### Distributive Justice Principles

The four principles tested are defined in `src/maai/core/models.py:187-208`:

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
# Note: run_quick_demo.py file not found in current codebase
# Use run_config.py with quick_test configuration instead
python run_config.py  # Edit DEFAULT_CONFIG_NAME to "quick_test" first
```

**Universal Configuration Runner**:
```bash
python run_config.py
# Edit DEFAULT_CONFIG_NAME variable on line 30 to switch configurations (currently set to "lucas")
```

**Parallel Experiment Execution**:
```bash
# Run experiments in parallel for faster execution
python run_experiments_parallel.py --num-experiments 10 --max-concurrent 3

# Jupyter notebook with parallel execution
# experiment_runner.ipynb (includes parallel execution with semaphore-based rate limiting)
```

**Available Configurations**:
- `lucas`: Custom configuration for specific research scenarios (default)
- `decomposed_memory_test`: 3 agents with decomposed memory strategy (test new memory system)
- `temperature_test`: Reproducible experiments with temperature=0.0 for deterministic results
- `default`: Standard experimental setup
- `test_custom`: Template for custom configurations
- `comprehensive_example`: Full-featured configuration example
- `hyp_random_XXX`: Generated configurations for hypothesis testing (001-010)
- `test_clean_XXX`: Clean test configurations (001-005)
- `test_fix_XXX`: Test configurations for bug fixes (001-003)

### Testing
```bash
# Run all tests (consolidated)
python run_tests.py

# Run individual test files
python tests/test_core.py
python tests/test_decomposed_memory.py
python tests/test_experiment_logger.py
python tests/test_temperature_configuration.py
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

### Additional Development Tools

**Random Configuration Generation**:
```bash
python generate_random_configs.py
```

**Hypothesis Testing**:
```bash
# Use Jupyter notebooks for hypothesis testing
jupyter notebook hypothesis_testing_experiment_refined.ipynb
jupyter notebook hypothesis_analysis.ipynb
jupyter notebook experiment_runner.ipynb
```

**Test Fixes**:
```bash
python test_fixes.py
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

**Temperature Configuration**:
- `global_temperature`: Sets temperature for all agents (overrides individual and default settings)
- Individual agents can specify their own `temperature` value
- Default temperature can be set in the `defaults` section
- Temperature precedence: `global_temperature` > agent-specific `temperature` > default `temperature`

**Memory Strategy System**:
- Configure how agents generate and manage private memories using `memory_strategy` field
- Available strategies:
  - `"full"`: Include all previous memory entries (default)
  - `"recent"`: Include only the most recent N memory entries
  - `"decomposed"`: Use focused, sequential prompts for improved memory quality
- Decomposed strategy breaks memory generation into three focused steps:
  1. **Factual Recap**: "What actually happened?" (objective events only)
  2. **Agent Analysis**: "Focus on ONE agent's behavior" (specific observations)
  3. **Strategic Action**: "What's ONE concrete thing you could do next?" (actionable strategy)
- Decomposed strategy reduces cognitive overload and produces more specific, actionable memories

**Example Configuration Structure**:
```yaml
experiment_id: my_experiment
global_temperature: 0.0  # Global temperature for reproducible results

experiment:
  max_rounds: 5
  decision_rule: unanimity
  timeout_seconds: 300

# Memory strategy configuration
memory_strategy: "decomposed"

agents:
  - name: "Agent_1"
    model: "gpt-4.1-mini"
    personality: "You are an economist focused on efficiency and optimal resource allocation."
    temperature: 0.0  # Agent-specific temperature override
  - name: "Agent_2"
    model: "gpt-4.1"
    personality: "You are a philosopher concerned with justice and fairness for all members of society."
  - name: "Agent_3"
    model: "gpt-4.1-mini"
    personality: "You are a pragmatist who focuses on what works in practice rather than theory."

defaults:
  personality: "You are an agent tasked to design a future society."
  model: "gpt-4.1-mini"
  temperature: 0.1  # Default temperature (overridden by global_temperature)

output:
  directory: experiment_results
  formats: [json, csv, txt]
  include_feedback: true
```

## Parallel Execution System

**Performance Benefits**:
- **Speed**: ~3x faster execution with default settings (3 concurrent experiments)
- **Scalability**: Adjustable concurrency based on API rate limits
- **Efficiency**: Better resource utilization and API capacity usage
- **Resilience**: Individual experiment failures don't block others

**Key Features**:
- **Semaphore-based Rate Limiting**: Prevents overwhelming API services
- **Real-time Progress Reporting**: See results as experiments complete
- **Robust Error Handling**: Graceful handling of individual experiment failures
- **Performance Metrics**: Detailed speedup and efficiency analysis

**Configuration Options**:
```python
MAX_CONCURRENT_EXPERIMENTS = 3  # Conservative default
# Increase for faster execution (if API limits allow)
# Decrease if encountering rate limiting issues
```

**Usage Examples**:
```bash
# Command line parallel execution
python run_experiments_parallel.py --num-experiments 20 --max-concurrent 5

# Jupyter notebook (experiment_runner.ipynb)
# Uses asyncio.gather() with semaphore control for optimal performance
```

## Data Export System

**Experiment Results** are saved to `experiment_results/` with multiple formats:
- `[ID].json`: Full structured experiment data (single file format)
- `[ID]_complete.json`: Full structured experiment data (legacy format)
- `[ID]_data.csv`: Main conversation transcript data
- `[ID]_initial_evaluation.csv`: Initial Likert scale assessments (before deliberation)
- `[ID]_initial_evaluation.json`: Initial ratings with statistics
- `[ID]_evaluation.csv`: Post-consensus principle evaluations
- `[ID]_evaluation.json`: Final ratings with statistics
- `[ID]_comparison.csv`: Before/after rating comparison analysis
- `[ID]_transcript.txt`: Human-readable conversation log

**Batch Experiment Results** are organized into timestamped directories:
- `hypothesis_test_batch_[TIMESTAMP]/`: Contains batch execution results
- `execution_summary.json`: Summary of batch execution
- `experiment_metadata.json`: Metadata for batch experiments
- `consolidated_rating_data.csv`: Aggregated rating data across experiments
- `statistical_results.json`: Statistical analysis results

## Environment Variables

**Required**:
- `OPENAI_API_KEY`: Primary model provider

**Optional**:
- `ANTHROPIC_API_KEY`: For Claude models
- `DEEPSEEK_API_KEY`: For DeepSeek models
- `GROQ_API_KEY`: For Groq models
- `GEMINI_API_KEY`: For Google Gemini models
- `AGENT_OPS_API_KEY`: For AgentOps monitoring (session named with experiment ID)

## Key Architecture Notes

**Core Classes**:
- `DeliberationManager` (src/maai/core/deliberation_manager.py:25): Main orchestrator for multi-round experiments
- `DeliberationAgent` (src/maai/agents/enhanced.py:14): Enhanced agents with structured outputs
- `ExperimentConfig` (src/maai/core/models.py:115): Pydantic model for experiment configuration
- `PrincipleChoice` (src/maai/core/models.py:59): Structured agent decision representation
- `LikertScale` (src/maai/core/models.py:12): 4-point scale for principle evaluation
- `ExperimentLogger` (src/maai/services/experiment_logger.py:15): In-memory data collector for comprehensive experiment logging

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
2. **Initial Likert Evaluation**: Agents rate all 4 principles before deliberation
3. **Multi-Round Deliberation**: Agents debate until unanimous agreement or timeout
4. **Consensus Detection**: Validate group agreement on chosen principle
5. **Final Likert Evaluation**: Agents re-rate all 4 principles after deliberation
6. **Data Export**: Results saved in multiple formats for analysis

## Implementation Notes

- Built on OpenAI Agents SDK with LitellmModel for multi-provider support
- Supports GPT-4.1, GPT-4.1 mini/nano, Claude, and DeepSeek models
- All operations are async-first using asyncio
- Pydantic models ensure data validation throughout the system
- AgentOps integration provides experiment tracing and monitoring (conditional based on model providers)
- Model provider detection in `src/maai/core/models.py:305` determines tracing strategy

## Advanced Service Configuration

The service architecture enables flexible research experimentation:

```python
# Example: Custom consensus strategy
from src.maai.services.experiment_orchestrator import ExperimentOrchestrator

orchestrator = ExperimentOrchestrator(
    consensus_strategy="threshold",  # or "id_match", "semantic"
    conversation_pattern="sequential",  # or "random", "hierarchical"
    memory_strategy="decomposed"  # or "full", "recent"
)

# Configure different experimental conditions
results = await orchestrator.run_experiment(config)
```

This allows researchers to A/B test different consensus mechanisms, communication patterns, and memory strategies without changing core code.

## Batch Experiment System

**Hypothesis Testing Framework**:
- Use `hypothesis_experiments/` directory for organized batch testing
- Each batch creates a timestamped directory with configs and results
- Supports parallel execution of multiple experiment configurations
- Automatic statistical analysis and data consolidation

**Key Features**:
- **Automated Config Generation**: Generate multiple test configurations with variations
- **Parallel Execution**: Run multiple experiments concurrently with rate limiting
- **Statistical Analysis**: Automatic calculation of statistical significance
- **Data Consolidation**: Aggregate results across experiments for analysis
- **Reproducible Results**: Timestamped directories maintain experiment provenance

## Development Guidelines

### Code Style
- Use descriptive variable names and method names
- Prefer async/await patterns throughout
- All timestamps use `datetime` objects with UTC
- Pydantic models for all data structures
- Type hints on all function parameters and returns

### Testing
- All core functionality has unit tests in `tests/`
- Integration tests use the `quick_test` configuration
- Test files follow the pattern `test_*.py`
- Mock external API calls in tests
- **Prefer simple, focused tests** over complex multi-purpose test scripts
- Each test should verify one specific functionality clearly and concisely

### Configuration Management
- All experiment parameters go in YAML files under `configs/`
- Use the `load_config_from_file()` function consistently
- Validate all configs with Pydantic models
- Default values defined in `DefaultConfig` class

### Error Handling
- All async operations wrapped in try/catch
- Graceful degradation when services fail
- Detailed logging for debugging
- AgentOps automatically captures errors for tracing

### File Structure Conventions
- Core logic in `src/maai/core/`
- Agent implementations in `src/maai/agents/`
- Service layer in `src/maai/services/`
- Configuration management in `src/maai/config/`
- Export functionality in `src/maai/export/`
- All modules have `__init__.py` files
- Documentation in `docs/` directory with visualization tools
- Feature planning in `feature_plan/` directory
- Knowledge base in `knowledge_base/` with SDK documentation and best practices

### Documentation and Analysis Tools
- **Visualization**: Use `docs/visualization/generate_overview.py` for system overview generation
- **Memory Analysis**: Reference `docs/memory_strategies_guide.md` for memory strategy documentation
- **Feature Planning**: Use `feature_plan/` directory for development roadmaps and analysis
- **Knowledge Base**: Complete OpenAI Agents SDK documentation and best practices in `knowledge_base/`