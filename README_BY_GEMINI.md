# README by Gemini: A Deep Dive into the Multi-Agent Distributive Justice Experiment

This document provides a comprehensive explanation of the codebase for the Multi-Agent Distributive Justice Experiment. It is intended for developers and researchers who want to understand the project's architecture, data flow, and the detailed execution process.

## 1. Codebase Architecture

The project is designed with a modular, service-oriented architecture to promote separation of concerns, testability, and extensibility. The core logic is encapsulated within the `src/maai/` directory.

### Core Components

- **`run_config.py`**: The main entry point for running experiments. It loads a configuration, initializes the necessary services, and orchestrates the entire experiment from start to finish.

- **`src/maai/config/manager.py`**: Responsible for loading, parsing, and validating experiment configurations from YAML files. It also handles environment variable overrides, ensuring a flexible setup.

- **`src/maai/core/models.py`**: Defines all the data structures used throughout the project using `Pydantic`. This ensures data integrity and provides clear, self-documenting models for experiments, agents, responses, and results.

- **`src/maai/agents/enhanced.py`**: Contains the definitions for the different types of AI agents used in the simulation:
    - `DeliberationAgent`: The primary agent participating in the deliberation.
    - `DiscussionModerator`: A specialized agent used to interpret and structure the conversation.
    - `FeedbackCollector`: An agent designed to interview `DeliberationAgent`s after the experiment.

- **`src/maai/services/`**: This directory contains the key services that manage the experiment's logic:
    - **`experiment_orchestrator.py`**: The high-level conductor of the experiment. It coordinates the other services to execute the experiment's phases in the correct order.
    - **`conversation_service.py`**: Manages the flow of communication between agents. It determines the speaking order and structures each round of deliberation.
    - **`consensus_service.py`**: Responsible for detecting whether the agents have reached a unanimous agreement based on their stated choices.
    - **`memory_service.py`**: Manages the private memory of each agent, allowing them to reflect on the conversation and update their strategy.

- **`src/maai/export/data_export.py`**: Handles the serialization of the experiment results into various formats (JSON, CSV, TXT) for analysis.

### Data Flow

1.  An experiment is initiated via `run_config.py`.
2.  The `ConfigManager` loads a YAML configuration, creating an `ExperimentConfig` object.
3.  The `ExperimentOrchestrator` receives the configuration and initializes the agents and services.
4.  The `ConversationService` manages the rounds of deliberation, and in each round:
    a. The `MemoryService` helps each agent to form a private strategy.
    b. Agents generate public messages.
    c. The `ConsensusService` checks for agreement.
5.  After the deliberation, the `ExperimentOrchestrator` collects feedback.
6.  Finally, the `DataExporter` saves the complete `ExperimentResults` to disk.

## 2. The Detailed Procedure of `run_config.py`

The execution of an experiment is a carefully orchestrated sequence of steps. Here is a detailed breakdown of what happens when you run `python run_config.py`:

### Step 1: Initialization and Configuration Loading

1.  **Environment Setup**: The script sets up the Python path and loads environment variables from a `.env` file (if present) using `dotenv`.
2.  **Tracing Configuration**: It pre-emptively loads the specified YAML configuration (e.g., `quick_test.yaml`) to determine if all the language models used in the experiment are from OpenAI. This is done to enable or disable OpenAI's specific tracing features.
3.  **Core Imports**: Key modules like `run_single_experiment` from `deliberation_manager.py` are imported *after* the tracing is configured.
4.  **AgentOps Initialization**: If an `AGENT_OPS_API_KEY` is found in the environment, the AgentOps monitoring service is initialized to track the experiment.
5.  **Final Configuration Load**: The `load_config_from_file` function from `config.manager` is called. This function reads the specified YAML file, applies any environment variable overrides, validates the structure, and returns a populated `ExperimentConfig` Pydantic model.

### Step 2: The `run_single_experiment` Function

This function, located in `deliberation_manager.py`, is the heart of the experiment execution. It wraps the entire process in a single `trace` for monitoring purposes.

1.  **DeliberationManager Instantiation**: A `DeliberationManager` is created, which in turn initializes the `ExperimentOrchestrator` and all the necessary services (`ConsensusService`, `ConversationService`, `MemoryService`).
2.  **Orchestrator Execution**: The `run_experiment` method of the `ExperimentOrchestrator` is called. This is where the main phases of the experiment are executed sequentially.

### Step 3: The Experiment Phases (within `ExperimentOrchestrator`)

1.  **Phase 1: Agent Initialization**
    - The `create_deliberation_agents` function is called, which iterates through the agent configurations in the `ExperimentConfig`.
    - For each agent, it determines the correct language model (handling different providers like OpenAI, Anthropic, etc.) and personality.
    - An instance of `DeliberationAgent` is created for each participant.
    - A `DiscussionModerator` agent is also created.
    - The `MemoryService` is initialized with a memory store for each agent.

2.  **Phase 2: Initial Individual Evaluation**
    - The `ConversationService`'s `conduct_initial_evaluation` method is called.
    - A speaking order for this initial round is generated.
    - Each agent is prompted individually to evaluate the four principles of distributive justice and make an initial choice. Their response is recorded in the `deliberation_transcript`.
    - After this phase, the `ConsensusService` checks if, by chance, a unanimous agreement has already been reached.

3.  **Phase 3: Multi-Round Deliberation**
    - The orchestrator enters a loop that runs for a maximum number of rounds (defined in the config).
    - In each round:
        a. The `ConversationService` generates a new speaking order.
        b. For each agent in the speaking order:
            i. The `MemoryService` is called to prompt the agent to perform a *private analysis* of the situation and form a strategy.
            ii. The agent is then prompted to generate a *public message* to the group, based on its private strategy.
            iii. The `DiscussionModerator` is used to extract the agent's current principle choice from their public message.
            iv. A `DeliberationResponse` object, containing the public message, private memory, and updated choice, is added to the transcript.
        c. At the end of the round, the `ConsensusService` is called to check for unanimous agreement among the agents' latest choices.
        d. If consensus is reached, the loop breaks. If not, it continues to the next round.

4.  **Phase 4: Post-Experiment Feedback Collection**
    - After the deliberation ends (either by consensus or by reaching the maximum number of rounds), the `_collect_feedback` method is called.
    - This method generates a `FeedbackResponse` for each agent, calculating their satisfaction based on whether they were part of the consensus (if any).

5.  **Phase 5: Finalize and Export Results**
    - The `_finalize_results` method is called to package all the data into a single `ExperimentResults` object.
    - This object contains the configuration, the full transcript, all agent memories, the consensus result, feedback responses, and performance metrics.
    - The `export_experiment_data` function is then called, which uses the `DataExporter` to write the results to disk in multiple formats (`.json`, `.csv`, `.txt`).

### Step 4: Conclusion

The `run_config.py` script prints a final summary of the experiment's outcome, including whether consensus was reached, the duration, and where the results have been saved. If AgentOps is enabled, the session is marked as complete.

This detailed process ensures that each experiment is run in a structured, repeatable, and well-documented manner, capturing a rich dataset for research and analysis.