# Gemini Codebase Explanation: Masters-Thesis-Rawls

## Project Overview

This project appears to be a Python-based research framework for a Master's Thesis. The central theme seems to be the implementation and experimentation of multi-agent AI systems. Given the project name "Masters-Thesis-Rawls-", it is highly probable that this thesis explores concepts from the philosopher John Rawls, likely related to justice, fairness, and social contract theory, as applied to interacting AI agents.

The system is designed to orchestrate experiments where multiple AI agents deliberate and work towards a consensus. It is heavily configuration-driven, allowing researchers to define different experimental setups using YAML files.

## Core Concepts & Architecture

*   **Multi-Agent System (MAS):** The foundation of the project is the interaction of multiple AI agents. The `src/maai/agents/` directory likely contains the definitions for these agents.
*   **Experiment Orchestration:** The project is not a single application but a framework for running experiments. The `src/maai/services/experiment_orchestrator.py` is a key component, likely responsible for setting up and running experiments based on configuration files.
*   **Deliberation and Consensus:** This is the core mechanic being investigated. Agents engage in a process of deliberation, managed by `src/maai/core/deliberation_manager.py`, to reach an agreement. The `src/maai/services/consensus_service.py` likely implements the specific algorithms for achieving this consensus, possibly inspired by Rawlsian principles.
*   **Configuration-Driven:** Experiments are defined in YAML files located in the `configs/` directory. This allows for easy modification of parameters, agent roles, and scenarios without changing the source code. The `src/maai/config/manager.py` is responsible for loading and managing these configurations.
*   **Knowledge Base & SDK:** The `knowledge_base/agents_sdk/` directory contains extensive documentation and examples for an Agents SDK. This suggests the project is built on top of a specific framework for creating AI agents, and this directory serves as a reference.

## Key Directories

*   `src/maai/`: The main source code for the project, containing the core logic for agents, services, and orchestration.
    *   `agents/`: Defines the behavior of the AI agents.
    *   `core/`: Contains central logic like the `deliberation_manager.py`.
    *   `services/`: Implements the main functionalities like orchestration, consensus, and conversation management.
    *   `config/`: Manages the loading of experiment configurations.
*   `configs/`: Contains YAML configuration files for different experiments (e.g., `default.yaml`, `quick_test.yaml`).
*   `docs/`: Contains project documentation, including design goals, architecture diagrams, and implementation plans.
*   `demos/`: Contains Python scripts to demonstrate specific phases or capabilities of the system.
*   `knowledge_base/`: A large repository of documentation, examples, and best practices, primarily for the underlying Agents SDK used in this project.
*   `tests/`: Contains unit tests for the project's core functionality.

## How to Run

The project includes several top-level Python scripts for execution:

*   **Install Dependencies:** `pip install -r requirements.txt`
*   **Run Tests:** `python run_tests.py`
*   **Run a Quick Demo:** `python run_quick_demo.py`
*   **Run a Configured Experiment:** `python run_config.py --config_name <config_file.yaml>` (based on the file's likely function).
*   **Example Usage:** The `example_service_usage.py` script likely shows how to interact with the project's services programmatically.
