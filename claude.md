# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Master's thesis project implementing a Multi-Agent Distributive Justice Experiment framework. The system implements a **two-phase economic incentive-based game** where autonomous AI agents make decisions about distributive justice principles with real economic consequences. Unlike traditional "veil of ignorance" approaches, agents know they will receive actual monetary payouts based on their income class assignments after choosing principles.

## Architecture

**Core Framework**: Built on OpenAI Agents SDK with structured multi-agent deliberation system

**Key Components**:
- **src/maai/core/**: Core experiment logic and data models (`deliberation_manager.py`, `models.py`)
- **src/maai/agents/**: Enhanced agent classes with specialized roles (`enhanced.py`)
- **src/maai/config/**: YAML-based configuration management (`manager.py`)
- **src/maai/export/**: Legacy export system (deprecated)
- **src/maai/services/**: Service layer for experiment orchestration
- **configs/**: YAML configuration files for different experiment scenarios
- **experiment_results/**: Output directory for all experiment data

**Agent Classes**: 
- `DeliberationAgent` (src/maai/agents/enhanced.py:14): Main reasoning agents that debate principles (with configurable personalities)
- `DiscussionModerator` (src/maai/agents/enhanced.py:65): Manages conversation flow and speaking order
- `FeedbackCollector`: Conducts post-experiment interviews

**Service Architecture**:
- `ExperimentOrchestrator` (src/maai/services/experiment_orchestrator.py): High-level coordination of two-phase experiment flow
- `ConsensusService` (src/maai/services/consensus_service.py): Multiple consensus detection strategies with constraint handling
- `ConversationService` (src/maai/services/conversation_service.py): Communication pattern management
- `MemoryService` (src/maai/services/memory_service.py): Agent memory management strategies
- `EconomicsService` (src/maai/services/economics_service.py): Income distribution management and economic outcome calculation
- `PreferenceService` (src/maai/services/preference_service.py): Preference ranking collection and analysis
- `ValidationService` (src/maai/services/validation_service.py): Principle choice validation and constraint requirement checking
- `ExperimentLogger` (src/maai/services/experiment_logger.py): Comprehensive agent-centric experiment data collection
- `DetailedExamplesService` (src/maai/services/detailed_examples_service.py): Concrete income distribution examples for principle understanding

**Key Design Decisions**:
- **Economic Incentive-Based**: Agents receive real monetary payouts based on income assignments, not philosophical reasoning
- **Two-Phase Structure**: Phase 1 (Individual Familiarization) + Phase 2 (Group Deliberation)
- **Phase 1 Memory System**: Agents generate and preserve memories during individual experiences, creating continuity between phases
- **Preference Rankings**: 1-4 rankings with certainty levels replace Likert scale evaluation
- **Income Distributions**: Multiple distribution scenarios with 5 income classes each (HIGH, MEDIUM_HIGH, MEDIUM, MEDIUM_LOW, LOW)
- **Constraint Handling**: Automatic default values for principle 3 (floor) and 4 (range) constraints when not specified
- **Code-Based Consensus**: Consensus detection uses simple ID matching with constraint validation
- **Configurable Personalities**: Each agent can have a custom personality defined in YAML
- **No Output Truncation**: All agent outputs, messages, and reasoning are stored in full without character limits or truncation

### Distributive Justice Principles

The four principles tested are defined in `src/maai/core/models.py:187-208`:

1. **MAXIMIZING THE FLOOR INCOME**: The most just distribution maximizes the income received by the poorest member of society (Rawlsian difference principle)
2. **MAXIMIZING THE AVERAGE INCOME**: The most just distribution maximizes the average income across all members, regardless of distribution inequality
3. **MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT**: Maximize average income while guaranteeing a specified minimum income to everyone (requires floor constraint parameter)
4. **MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT**: Maximize average income while limiting the income difference between richest and poorest (requires range constraint parameter)

### Game Logic Structure

**Phase 1: Individual Familiarization**
1. **Initial Preference Ranking**: Agents rank all 4 principles (1-4) with certainty levels
2. **Detailed Examples**: Agents review concrete income distribution examples for each principle
3. **Individual Application Rounds**: Agents apply principles in economic scenarios (configurable rounds, default 4)
4. **Post-Individual Ranking**: Agents re-rank principles after gaining experience

**Phase 2: Group Experiment**  
1. **Group Deliberation**: Multi-round discussion to reach unanimous agreement on one principle
2. **Secret Ballot Voting**: Optional voting mechanism for consensus detection
3. **Economic Outcomes**: Apply agreed principle to determine each agent's income class and payout
4. **Final Preference Ranking**: Agents provide final rankings after seeing group outcomes

## Development Commands

### Setup and Installation
```bash
pip install -r requirements.txt
```

### Running Experiments

**Single Experiment Runner**:
```python
# Import and run directly
from maai.runners import run_experiment

# Run with default output directory (experiment_results)
result = await run_experiment('lucas')

# Run with custom output directory
result = await run_experiment('lucas', output_dir='custom_experiments/test_run')
```

**Batch Experiment Runner**:
```python
# Import and run directly
from maai.runners import run_batch

# Run multiple experiments with default settings
results = await run_batch(['config1', 'config2', 'config3'])

# Run with custom output directory and concurrency
results = await run_batch(
    ['config1', 'config2'], 
    max_concurrent=5, 
    output_dir='custom_experiments/batch_run'
)
```

**Configuration Generation**:
```bash
# Generate batch configurations with variations
python config_generator.py
```

**Available Configurations**:
- `new_game_basic`: Basic configuration for new game logic system (recommended starting point)
- `lucas`: Custom configuration for specific research scenarios 
- `lucas_new`: Updated custom configuration
- `phase1_memory_example`: Example configuration with Phase 1 memory features enabled
- `decomposed_memory_test`: 3 agents with decomposed memory strategy
- `temperature_test`: Reproducible experiments with temperature=0.0 for deterministic results
- `default`: Legacy experimental setup (pre-new game logic)
- `comprehensive_example`: Full-featured configuration example
- `hyp_random_XXX`: Generated configurations for hypothesis testing (001-010)
- `test_clean_XXX`: Clean test configurations (001-005)

### Testing
```bash
# Run all tests (consolidated)
python tests/run_all_tests.py

# Run with pytest support
python tests/run_all_tests.py --pytest

# Run individual test files
python tests/test_core.py
python tests/test_decomposed_memory.py
python tests/test_experiment_logger.py
python tests/test_temperature_configuration.py
python tests/test_unified_logging.py
python tests/test_consensus_service.py
python tests/test_conversation_service.py
python tests/test_evaluation_service.py
python tests/test_public_history_service.py
python tests/test_integration.py
python tests/test_detailed_examples_service.py
python tests/test_phase1_memory.py

# Run with pytest directly
pytest tests/ -v --tb=short

# Test Phase 1 memory integration
python test_phase1_integration.py
```

### Direct API Usage

**Single Experiment**:
```python
import asyncio
from maai.runners import run_experiment

# Run with default output directory (experiment_results)
results = await run_experiment('default')

# Run with custom output directory
results = await run_experiment('default', output_dir='custom_experiments/test_run')

# Access output path
print(f"Results saved to: {results['output_path']}")
```

**Batch Experiments**:
```python
import asyncio
from maai.runners import run_batch

# Run multiple experiments with default settings
config_names = ['config1', 'config2', 'config3']
results = await run_batch(config_names)

# Run with custom output directory and concurrency
results = await run_batch(
    config_names, 
    max_concurrent=5, 
    output_dir='custom_experiments/batch_run'
)

# Check results
for result in results:
    if result['success']:
        print(f"✅ {result['experiment_id']}: {result['output_path']}")
    else:
        print(f"❌ {result['experiment_id']}: {result['error']}")
```

### Additional Development Tools

**Configuration Generation**:
```bash
# Generate batch configurations with variations
python config_generator.py
```

**Jupyter Notebook Analysis**:
```bash
# Main experiment analysis notebook
jupyter notebook Experiment.ipynb

# Systematic analysis across models and parameters
jupyter notebook Systematic_Analysis.ipynb
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
  - `"recent"`: Include only the most recent N memory entries (default)
  - `"decomposed"`: Use focused, sequential prompts for improved memory quality
  - `"phase_aware_decomposed"`: Enhanced decomposed strategy that leverages Phase 1 experiences in Phase 2 reasoning
- Decomposed strategy breaks memory generation into three focused steps:
  1. **Factual Recap**: "What actually happened?" (objective events only)
  2. **Agent Analysis**: "Focus on ONE agent's behavior" (specific observations)
  3. **Strategic Action**: "What's ONE concrete thing you could do next?" (actionable strategy)
- Phase-aware strategy enhances steps 2-3 with Phase 1 insights when available:
  - Agent analysis considers individual learning experiences
  - Strategic actions leverage consolidated Phase 1 preferences and economic learnings
- Decomposed strategies reduce cognitive overload and produce more specific, actionable memories

**Example Configuration Structure**:
```yaml
experiment_id: new_game_example
global_temperature: 0.0  # Global temperature for reproducible results

experiment:
  max_rounds: 5
  decision_rule: unanimity
  timeout_seconds: 300

# New game logic configuration
individual_rounds: 4  # Number of individual application rounds
payout_ratio: 0.0001  # $0.0001 per $1 of income (e.g., $20,000 income = $2.00 payout)
enable_detailed_examples: true
enable_secret_ballot: true

# Phase 1 Memory Configuration
enable_phase1_memory: true  # Enable Phase 1 individual memory generation
phase1_memory_frequency: "each_activity"  # Generate memories after each Phase 1 activity
phase1_consolidation_strategy: "summary"  # Use summary consolidation before Phase 2
phase1_memory_integration: true  # Include Phase 1 memories in Phase 2 context
phase1_reflection_depth: "standard"  # Standard depth reflections

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

# Enhanced memory strategy that leverages Phase 1 experiences
memory_strategy: "phase_aware_decomposed"

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

**Phase 1 Memory Configuration Options**:
- `enable_phase1_memory`: Enable/disable Phase 1 memory generation (default: true)
- `phase1_memory_frequency`: When to generate memories - "each_activity"|"each_round"|"phase_end" (default: "each_activity")
- `phase1_consolidation_strategy`: How to consolidate memories - "summary"|"detailed"|"key_insights" (default: "summary")
- `phase1_memory_integration`: Include Phase 1 memories in Phase 2 context (default: true)
- `phase1_reflection_depth`: Depth of reflections - "brief"|"standard"|"detailed" (default: "standard")

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
# Batch execution with custom configs
python run_batch.py

# Single experiment execution
python run_experiment.py
```

## Data Export System

**Experiment Results** are saved to `experiment_results/` with multiple formats:
- `[ID].json`: Full structured experiment data (single file format) - **Complete data with no truncation**
- `[ID]_complete.json`: Full structured experiment data (legacy format)
- `[ID]_data.csv`: Main conversation transcript data
- `[ID]_initial_evaluation.csv`: Initial Likert scale assessments (before deliberation)
- `[ID]_initial_evaluation.json`: Initial ratings with statistics
- `[ID]_evaluation.csv`: Post-consensus principle evaluations
- `[ID]_evaluation.json`: Final ratings with statistics
- `[ID]_comparison.csv`: Before/after rating comparison analysis
- `[ID]_transcript.txt`: Human-readable conversation log

**Important**: All agent outputs, messages, reasoning, and evaluation text are stored in full without any character limits or truncation. The logging system preserves complete conversation history and agent reasoning.

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
4. Export results via `ExperimentLogger.export_unified_json()` in `src/maai/services/experiment_logger.py`

**Main Entry Points**:
- `src/maai/runners/`: Experiment runner module with single and batch capabilities
  - `single.py`: Single experiment runner with detailed result reporting and custom output directory support
  - `batch.py`: Parallel batch execution with semaphore-based rate limiting and custom output directory support
  - `common.py`: Shared utilities for experiment runners
- `run_experiment.py`: Backward compatibility wrapper (DEPRECATED - use `from maai.runners import run_experiment`)
- `run_batch.py`: Backward compatibility wrapper (DEPRECATED - use `from maai.runners import run_batch`)
- `config_generator.py`: Generate multiple configuration variations for batch testing

**Output Directory Control**:
- **Default**: All experiments save to `experiment_results/` directory
- **Custom**: Use `--output-dir` flag (CLI) or `output_dir` parameter (API) to specify custom location
- **Path Format**: Results saved as `{output_dir}/{experiment_id}.json`

**Knowledge Base**:
- `knowledge_base/agents_sdk/`: Complete OpenAI Agents SDK documentation and examples
- `knowledge_base/best_practices/`: Practical guide to building agents (PDF and text)

## Experimental Flow

**Phase 1: Individual Familiarization**
1. **Agent Initialization**: Create agents with economic incentive context and income distribution scenarios
2. **Initial Preference Ranking**: Agents rank all 4 principles (1-4) with certainty levels
3. **Detailed Examples**: Agents review concrete income distribution examples for each principle
4. **Individual Application Rounds**: Agents apply principles in multiple economic scenarios (default 4 rounds)
5. **Post-Individual Ranking**: Agents re-rank principles after gaining hands-on experience

**Phase 2: Group Experiment**
1. **Memory Consolidation**: Consolidate Phase 1 experiences into strategic insights for group discussions
2. **Group Deliberation**: Multi-round discussion to reach unanimous agreement on one principle (with Phase 1 memory context)
3. **Consensus Detection**: Validate group agreement with constraint handling for principles 3 & 4
4. **Economic Outcomes**: Apply agreed principle to assign income classes and calculate real payouts
5. **Final Preference Ranking**: Agents provide final rankings after experiencing group outcomes
6. **Data Export**: Comprehensive agent-centric data export with all interactions and outcomes

### Phase 1 Memory System

The Phase 1 Memory System addresses a critical gap in agent continuity by preserving individual learning experiences for use in group deliberation.

**Memory Types**:
- **Individual Reflection Memory**: Captures reasoning behind preference changes and decisions
- **Learning Accumulation Memory**: Builds understanding across examples and rounds
- **Experience Integration Memory**: Connects economic outcomes with strategic insights
- **Consolidated Memory**: Summary of Phase 1 experiences for Phase 2 context

**Memory Generation Points**:
- After initial preference ranking: Reflection on ranking reasoning
- After detailed examples: Learning from concrete distribution examples
- After each individual round: Integration of economic outcome experiences
- After post-individual ranking: Final reflection on preference evolution
- Before group deliberation: Consolidation of all Phase 1 memories

**Phase Transition Bridge**:
- Agents enter Phase 2 with consolidated Phase 1 insights
- Memory context includes strategic preferences and economic learnings
- Phase-aware memory strategies leverage individual experiences in group settings

**Research Benefits**:
- Complete learning trajectories across both phases
- Enhanced preference evolution analysis
- Realistic cognitive continuity between individual and group decision-making
- Improved ecological validity of agent reasoning

## Implementation Notes

- Built on OpenAI Agents SDK with LitellmModel for multi-provider support
- Supports GPT-4.1, GPT-4.1 mini/nano, Claude, and DeepSeek models
- All operations are async-first using asyncio
- Pydantic models ensure data validation throughout the system

## Advanced Service Configuration

The service architecture enables flexible research experimentation:

```python
# Example: Custom consensus strategy
from src.maai.services.experiment_orchestrator import ExperimentOrchestrator

orchestrator = ExperimentOrchestrator(
    consensus_strategy="threshold",  # or "id_match", "semantic"
    conversation_pattern="sequential",  # or "random", "hierarchical"
    memory_strategy="decomposed"  # or "recent"
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
- **Never truncate output**: All agent messages, reasoning, and outputs must be stored in full without character limits

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