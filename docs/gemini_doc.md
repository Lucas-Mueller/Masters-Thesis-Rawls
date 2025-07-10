# Gemini Documentation: Masters Thesis Rawls Codebase

This document provides a comprehensive overview of the "Masters Thesis Rawls" codebase, a multi-agent system designed to simulate and study distributive justice principles based on John Rawls' "veil of ignorance" thought experiment.

## 1. Project Objective

The primary goal of this project is to conduct an experiment to determine which principle of distributive justice a group of autonomous AI agents will unanimously select when they are made impartial by a "veil of ignorance." This means they must agree on a principle for distributing wealth without knowing their own future position in the economic hierarchy.

The experiment is designed to test which of the following principles is favored:
1.  **Maximize the Minimum Income:** Ensuring the worst-off member is as well-off as possible.
2.  **Maximize the Average Income:** Aiming for the greatest total income, regardless of distribution.
3.  **Maximize the Average Income with a Floor Constraint:** A hybrid that sets a minimum income safety net and then maximizes the average.
4.  **Maximize the Average Income with a Range Constraint:** A hybrid that limits the gap between the richest and poorest and then maximizes the average.

## 2. System Architecture and Design

The system is built using a multi-agent architecture, where specialized agents interact to achieve a collective goal. The implementation heavily relies on an agents SDK, as indicated in the design documents.

### Key Architectural Components:

*   **Multi-Agent Deliberation:** The core of the system is a multi-round deliberation process where agents discuss the merits of the principles to reach a unanimous consensus.
*   **Specialized Agents:** The system uses different types of agents with specific roles:
    *   `DeliberationAgent`: The base agent that participates in discussions.
    *   `DiscussionModerator`: Manages the rounds of discussion and ensures the conversation progresses.
    *   `ConsensusJudge`: Monitors the deliberation to determine if and when a unanimous agreement has been reached.
    *   `FeedbackCollector`: Gathers post-experiment feedback from each agent.
*   **Configuration Management:** Experiments are configured using YAML files, allowing for easy modification of parameters like the number of agents, deliberation rounds, and which principles are being considered.
*   **Data Collection and Export:** The system is designed to meticulously log all aspects of the experiment, including full deliberation transcripts, agent choices, and performance metrics. This data is then exported into structured formats like JSON, CSV, and plain text for analysis.

## 3. Codebase Structure

The project is organized into several key files and directories:

| File/Directory | Description |
| :--- | :--- |
| `MAAI.py` | The main entry point for running the multi-agent simulation. |
| `deliberation_manager.py` | Orchestrates the entire deliberation process, managing the agents and the flow of the experiment from start to finish. |
| `agents_enhanced.py` | Contains the definitions for the specialized agent classes (`DeliberationAgent`, `ConsensusJudge`, etc.). |
| `models.py` | Defines the Pydantic data models used for structured data exchange between agents and for logging (e.g., `PrincipleChoice`, `DeliberationResponse`). |
| `config_manager.py` | Handles loading and validating the experiment configurations from the YAML files in the `configs/` directory. |
| `data_export.py` | Contains the logic for exporting the collected experimental data into various formats. |
| `demo_phase1.py` / `demo_phase2.py` | Scripts to demonstrate the functionality of the completed phases of the project. |
| `test_*.py` | A suite of tests to ensure the reliability and correctness of the system's components. |
| `configs/` | A directory containing YAML configuration files for different experimental setups (e.g., `default.yaml`, `large_group.yaml`). |
| `experiment_results/` | The output directory where all the data from the experiments is saved. |
| `knowledge_base/` | Contains documentation and resources related to the agents SDK and other relevant topics. |
| `Logs_MAAI/` | Directory for runtime logs. |

## 4. How the Experiment Works

The simulation proceeds in the following phases:

### Phase 1: Deliberation and Choice (Completed)
1.  **Initialization**: The `DeliberationManager` loads the experiment configuration and initializes the specified number of `DeliberationAgents`, along with the `DiscussionModerator` and `ConsensusJudge`.
2.  **Familiarization**: Each agent is individually presented with the principles of justice and forms an initial private preference.
3.  **Deliberation**: The agents enter a shared communication channel managed by the `DiscussionModerator`. They debate the principles over multiple rounds.
4.  **Consensus**: The `ConsensusJudge` monitors the discussion. The deliberation continues until a unanimous agreement is reached or a timeout/maximum round limit is hit.
5.  **Logging**: The entire deliberation transcript, including each agent's messages and evolving choices, is logged.

### Phase 2: Data Collection and Feedback (Completed)
1.  **Feedback**: After the deliberation concludes, the `FeedbackCollector` agent interviews each `DeliberationAgent` individually to gather feedback on their satisfaction with the outcome and the fairness of the chosen principle.
2.  **Data Export**: The `DataExporter` compiles all the data from the experiment—including configuration, transcripts, consensus results, feedback, and performance metrics—into a set of structured files in the `experiment_results/` directory.

## 5. Current Status and Future Work

As per the `implementation_plan.md`, the project is divided into several phases:

*   **Phase 1 & 2 (Completed):** The core multi-agent deliberation system and the enhanced data collection framework are fully implemented and tested.
*   **Phase 3 (Pending):** This phase will introduce experimental variations, such as using a majority rule for decisions instead of unanimity.
*   **Phase 4 (Pending):** This phase focuses on production readiness, including performance optimization and preparing for potential cloud deployment.
