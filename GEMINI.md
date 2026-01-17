# GEMINI.md

This file provides guidance to Gemini when working with code in this repository.

## Project Overview

This is a Master's thesis project implementing a **Multi-Agent Distributive Justice Experiment framework**. The system simulates a novel **two-phase economic incentive-based game** where autonomous AI agents make decisions about distributive justice principles with real economic consequences. Unlike traditional "veil of ignorance" approaches, agents receive actual monetary payouts based on their income class assignments after choosing principles.

The framework is built on the **OpenAI Agents SDK** and features a service-oriented architecture that allows for flexible and modular experiment design.

## Architecture

**Core Framework**: Built on OpenAI Agents SDK with a structured multi-agent deliberation system.

**Key Components**:
- **`src/maai/core/`**: Core experiment logic, data models, and the main `deliberation_manager.py`.
- **`src/maai/agents/`**: Contains `enhanced.py` with the `DeliberationAgent` and `DiscussionModerator` classes.
- **`src/maai/config/`**: YAML-based configuration management via `manager.py`.
- **`src/maai/services/`**: A comprehensive service layer for orchestrating experiments.
- **`configs/`**: YAML files for defining various experiment scenarios.
- **`experiment_results/`**: The output directory for all experiment data.

### Service Architecture

The system employs a modular, service-oriented architecture coordinated by the `ExperimentOrchestrator`. This design allows for easy extension and modification of the experimental procedure.

- **`ExperimentOrchestrator`**: The high-level coordinator for all services, managing the two-phase experiment flow.
- **`ConsensusService`**: Detects consensus among agents, with strategies for handling principles that require constraints.
- **`ConversationService`**: Manages the flow of conversation between agents (e.g., sequential, random).
- **`MemoryService`**: Manages agent memories with different strategies (e.g., full, recent, decomposed).
- **`EconomicsService`**: Handles economic calculations, income distribution, and payout determination.
- **`PreferenceService`**: Manages the collection and analysis of agent preference rankings.
- **`ValidationService`**: Validates agent choices and ensures that constraints for principles are met.
- **`DetailedExamplesService`**: Presents detailed examples of the principles to the agents.
- **`ExperimentLogger`**: A unified, agent-centric JSON logging system that captures all experiment data.
- **`PublicHistoryService`**: Manages the public conversation history.

### Distributive Justice Principles

The four principles tested are defined in `src/maai/core/models.py`:

1.  **Maximize the Minimum Income**: Ensures the worst-off are as well-off as possible (Rawlsian).
2.  **Maximize the Average Income**: Focuses on the greatest total income, regardless of distribution.
3.  **Floor Constraint**: A hybrid principle that guarantees a minimum income and then maximizes the average.
4.  **Range Constraint**: A hybrid principle that limits the inequality gap and then maximizes the average.

## Experimental Flow

The experiment is divided into two main phases:

**Phase 1: Individual Familiarization**
1.  **Initial Preference Ranking**: Agents rank the four principles and provide certainty levels.
2.  **Detailed Examples**: Agents are presented with concrete examples of how each principle affects income distribution.
3.  **Individual Application Rounds**: Agents individually apply the principles for a set number of rounds and receive economic outcomes.
4.  **Post-Individual Ranking**: Agents re-rank the principles after their individual experiences.

**Phase 2: Group Experiment**
1.  **Group Deliberation**: Agents deliberate to reach a unanimous consensus on a single principle.
2.  **Economic Outcomes**: The agreed-upon principle is applied to determine each agent's income class and monetary payout.
3.  **Final Preference Ranking**: Agents provide a final ranking of the principles after the group outcome.
4.  **Data Export**: All results are saved to a single, unified JSON file.

## Development Commands

### Setup and Installation
```bash
pip install -r requirements.txt
```

### Running Experiments

**Single Experiment Runner**:
```bash
# Run with a specific configuration file
python run_experiment.py --config new_game_basic

# Override the output directory
python run_experiment.py --config new_game_basic --output-dir custom_experiments/my_test
```

**Batch Experiment Runner**:
```bash
# Run multiple experiments defined in run_batch.py
python run_batch.py
```

**Available Configurations**:
- `new_game_basic`: Recommended starting point for the new game logic.
- `lucas`: Custom configuration for specific research scenarios.
- `decomposed_memory_test`: Tests the decomposed memory strategy.
- `temperature_test`: For reproducible experiments with temperature=0.0.
- `default`: Legacy experimental setup.

## Configuration System

Experiments are configured using **YAML files** located in the `configs/` directory. These files define all experiment parameters, including:

- Agent configurations (name, model, personality)
- Experiment parameters (rounds, timeouts, decision rules)
- Game logic parameters (individual rounds, payout ratios, income distributions)
- Memory strategy and logging settings

**Example Configuration Structure**:
```yaml
experiment_id: new_game_example
global_temperature: 0.0

experiment:
  max_rounds: 5
  decision_rule: unanimity

individual_rounds: 4
payout_ratio: 0.0001
enable_detailed_examples: true

income_distributions:
  - distribution_id: 1
    name: "Distribution A"
    income_by_class:
      HIGH: 50000
      MEDIUM_HIGH: 40000
      MEDIUM: 30000
      MEDIUM_LOW: 20000
      LOW: 10000

memory_strategy: "decomposed"

agents:
  - name: "Economist"
    model: "gpt-4.1-mini"
    personality: "You are an economist focused on efficiency."
  - name: "Philosopher"
    model: "gpt-4.1-mini"
    personality: "You are a philosopher concerned with fairness."

output:
  directory: experiment_results
  formats: [json]
```

## Data Export System

The primary output is a single, comprehensive **agent-centric JSON file** in the `experiment_results/` directory. This file contains all data from the experiment, including:

- `experiment_metadata`: Overall experiment details and configuration.
- `[agent_id]`: A top-level key for each agent, containing all their data, such as:
  - `overall`: The agent's configuration.
  - `assessments`: Pre- and post-experiment assessments.
  - `individual_rounds`: Data from the individual familiarization phase.
  - `deliberation_rounds`: Detailed data for each deliberation round.
  - `final_consensus`: The agent's final consensus data.

The old data export system that produced multiple CSV and TXT files is **deprecated**.

## Environment Variables

**Required**:
- `OPENAI_API_KEY`: For OpenAI models.

**Optional**:
- `ANTHROPIC_API_KEY`: For Claude models.
- `DEEPSEEK_API_KEY`: For DeepSeek models.
- `GEMINI_API_KEY`: For Gemini models.
- `GROQ_API_KEY`: For Groq models.

## Key Dependencies

The project relies on the following key Python libraries:

- `openai-agents`: The core framework for building multi-agent systems.
- `litellm`: For multi-provider support for LLMs.
- `pydantic`: For data validation and settings management.
- `pyyaml`: For parsing YAML configuration files.
- `pandas`: For data manipulation and analysis.
- `numpy`: For numerical operations.

## Development Guidelines

### Code Style
- Use `async/await` patterns for all asynchronous operations.
- Use type hints for all function parameters and return values.
- Use Pydantic models for all data structures to ensure validation.
- Write descriptive variable and method names.
- **Never truncate output**: Store all agent messages and reasoning in full.

### Testing
- All core functionality has unit tests in the `tests/` directory.
- Run all tests using `python tests/run_all_tests.py`.
- Test files follow the pattern `test_*.py`.
- Mock external API calls in tests to ensure they are hermetic.

### File Structure Conventions
- Core logic: `src/maai/core/`
- Agent implementations: `src/maai/agents/`
- Service layer: `src/maai/services/`
- Configuration management: `src/maai/config/`
- All modules should have `__init__.py` files.