At the end of this message, I will ask you to do something. Please follow the "Explore, Plan, Code, Test" workflow when you start.

Explore
First, use parallel subagents to find and read all files that may be useful for implementing the ticket, either as examples or as edit targets. The subagents should return relevant file paths, and any other info that may be useful.

Plan
Next, think hard and write up a detailed implementation plan. Don't forget to include tests, lookbook components, and documentation. Use your judgement as to what is necessary, given the standards of this repo.

If there are things you are not sure about, use parallel subagents to do some web research. They should only return useful information, no noise.

If there are things you still do not understand or questions you have for the user, pause here to ask them before continuing.

Code
When you have a thorough implementation plan, you are ready to start writing code. Follow the style of the existing codebase (e.g. we prefer clearly named variables and methods to extensive comments). Make sure to run our autoformatting script when you're done, and fix linter warnings that seem reasonable to you.

Test
Use parallel subagents to run tests, and make sure they all pass.

If your changes touch the UX in a major way, use the browser to make sure that everything works correctly. Make a list of what to test for, and use a subagent for this step.

If your testing shows problems, go back to the planning stage and think ultrahard.

Write up your work
When you are happy with your work, write up a short report that could be used as the PR description. Include what you set out to do, the choices you made with their brief justification, and any commands you ran in the process that may be useful for future developers to know about.


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
