# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Master's thesis project implementing a Multi-Agent Distributive Justice Experiment framework. The system simulates Rawls' "veil of ignorance" scenario where autonomous AI agents must reach unanimous agreement on distributive justice principles without knowing their future economic position.

## Architecture

**Core Framework**: Built on OpenAI Agents SDK with structured multi-agent deliberation system

**Key Components**:
- **src/maai/core/**: Core experiment logic and data models
- **src/maai/agents/**: Enhanced agent classes with specialized roles
- **src/maai/config/**: YAML-based configuration management
- **src/maai/export/**: Multi-format data export system
- **configs/**: YAML configuration files for different experiment scenarios
- **experiment_results/**: Output directory for all experiment data

**Agent System**: 
- `DeliberationAgent`: Main reasoning agents that debate principles (with configurable personalities)
- `DiscussionModerator`: Manages conversation flow
- `FeedbackCollector`: Conducts post-experiment interviews

**Key Design Changes**:
- **No Confidence Scores**: LLMs cannot reliably assess confidence, so confidence scoring has been removed entirely
- **Code-Based Consensus**: Consensus detection uses simple ID matching rather than LLM assessment
- **Configurable Personalities**: Each agent can have a custom personality defined in YAML
- **Neutral Descriptions**: Principle descriptions avoid references to philosophical authorities

### Distributive Justice Principles
1. Maximize the Minimum Income (ensures worst-off are as well-off as possible)
2. Maximize the Average Income (focuses on greatest total income regardless of distribution)
3. Floor Constraint (hybrid with guaranteed minimum income plus maximizing average)
4. Range Constraint (hybrid that limits inequality gap plus maximizing average)

## Development Commands

### Setup and Installation
```bash
pip install -r requirements.txt
```

### Running Experiments

**Quick Test (3 agents, 2 rounds)**:
```bash
python run_quick_demo.py
```

**Universal Configuration Runner**:
```bash
python run_config.py
# Edit CONFIG_NAME variable on line 20 to switch configurations
```

**Available Configurations**:
- `quick_test`: 3 agents, 2 rounds (1-2 minutes)
- `lucas`: Custom configuration
- `large_group`: 8 agents, 10 rounds (5-10 minutes)
- `multi_model`: Uses different AI models (GPT-4.1, Claude, DeepSeek)
- `default`: Standard experimental setup

### Testing
```bash
# Run all tests
python run_tests.py

# Individual test suites
python tests/test_phase1.py                    # Core deliberation system
python tests/test_phase1_comprehensive.py     # Comprehensive functionality  
python tests/test_phase2_feedback.py          # Feedback collection
python tests/test_phase2_logging.py           # Data export system
python tests/test_phase2_config.py            # Configuration management
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

## Configuration System

**YAML Configuration Files** in `configs/`:
- Define experiment parameters (agents, rounds, timeouts, models)
- Specify output formats and directories
- Configure agent personalities and behavior settings

**Personality System**:
- Each agent can have a custom personality defined in the `personalities` array
- If fewer personalities than agents are specified, remaining agents use the default: "You are an agent tasked to design a future society."
- Personalities can be full text descriptions or references to saved personality templates

**Example Configuration Structure**:
```yaml
experiment_id: my_experiment
experiment:
  num_agents: 3
  max_rounds: 5
  decision_rule: unanimity
  timeout_seconds: 300
  models: [gpt-4.1-mini, gpt-4.1, gpt-4.1-mini]

personalities:
  - "You are an economist focused on efficiency and optimal resource allocation."
  - "You are a philosopher concerned with justice and fairness for all members of society."
  - "You are a pragmatist who focuses on what works in practice rather than theory."

output:
  directory: experiment_results
  formats: [json, csv, txt]
  include_feedback: true
```

## Data Export System

**Experiment Results** are saved to `experiment_results/` with multiple formats:
- `[ID]_complete.json`: Full structured experiment data
- `[ID]_summary.csv`: Key metrics and outcomes
- `[ID]_transcript.csv`: Complete conversation data
- `[ID]_feedback.csv`: Post-experiment agent feedback
- `[ID]_choice_evolution.csv`: How agent choices changed over time
- `[ID]_transcript.txt`: Human-readable conversation log
- `[ID]_summary.txt`: Executive summary of results

## Environment Variables

**Required**:
- `OPENAI_API_KEY`: Primary model provider

**Optional**:
- `ANTHROPIC_API_KEY`: For Claude models
- `DEEPSEEK_API_KEY`: For DeepSeek models
- `AGENT_OPS_API_KEY`: For agent operations tracking

## Design Principles

- **Simplistic code**: Keep code concise and easy to understand
- **Modular design**: Create reusable components and functions
- **Extensive documentation**: Document all code thoroughly
- **Testing**: Create unit tests for crucial components
- **Cloud-ready**: Design with AWS deployment in mind
- **Async-first**: Use asyncio for concurrent agent operations

## Knowledge Base

The `knowledge_base/` directory contains:
- `agents_sdk/`: Complete OpenAI Agents SDK documentation and examples
- `best_practices/`: Practical guide to building agents (PDF and text)

## File Structure

**Current Enhanced System**:
```
src/maai/
├── core/
│   ├── models.py                    # Data models with Pydantic validation
│   └── deliberation_manager.py     # Core multi-agent deliberation engine
├── agents/
│   └── enhanced.py                  # Enhanced agent classes with specialized roles
├── config/
│   └── manager.py                   # YAML configuration management system
└── export/
    └── data_export.py               # Multi-format data export system

configs/                             # YAML configuration files
├── quick_test.yaml                  # 3 agents, 2 rounds
├── lucas.yaml                       # Custom configuration
├── large_group.yaml                 # 8 agents, 10 rounds
├── multi_model.yaml                 # Different AI models
└── default.yaml                     # Standard setup

tests/                               # Test suites
├── test_phase1.py                   # Core deliberation system
├── test_phase1_comprehensive.py    # Comprehensive functionality
├── test_phase2_feedback.py         # Feedback collection
├── test_phase2_logging.py          # Data export system
└── test_phase2_config.py           # Configuration management

experiment_results/                  # Output directory
└── [experiment_id]_*.*             # Multiple format outputs
```

**Legacy System** (in `legacy/`):
- `MAAI.py`: Original experimental logic and agent definitions
- `Logs_MAAI/`: CSV output files with experimental results

## Current Implementation Status

### ✅ Phase 1 - Core Multi-Agent Deliberation System (COMPLETED)
- ✅ Enhanced agent architecture (`DeliberationAgent`, `ConsensusJudge`, `DiscussionModerator`)
- ✅ Multi-round deliberation engine with `DeliberationManager`
- ✅ Consensus detection and resolution system
- ✅ Structured data models with Pydantic validation
- ✅ Comprehensive testing framework
- ✅ Performance metrics tracking and error handling
- ✅ Rich communication transcripts and data collection

### ✅ Phase 2 - Data Collection Enhancement (COMPLETED)
- ✅ Post-experiment feedback collection (`FeedbackCollector` agent)
- ✅ Enhanced logging system with multiple formats
- ✅ Configuration management system
- ✅ YAML configuration files in `configs/` directory
- ✅ Preset configurations for common scenarios

## Experimental Flow

1. **Agent Initialization**: Create agents with "veil of ignorance" context
2. **Multi-Round Deliberation**: Agents debate until unanimous agreement or timeout
3. **Consensus Detection**: Validate group agreement on chosen principle
4. **Feedback Collection**: Post-experiment interviews with agents
5. **Data Export**: Results saved in multiple formats for analysis

## World Knowledge Notes

- GPT-4.1 exists as well as GPT-4.1 mini and nano
- This project is based on the OpenAI Agents SDK (agents_sdk) - documentation available in `knowledge_base/agents_sdk/`
- The framework supports multiple AI model providers through LitellmModel integration

## Design Principles

- **Simplistic code**: Code should be concise and easy to understand
- **Modular design**: Create reusable components and functions
- **Extensive documentation**: Document everything in the code
- **Testing**: Create unit tests for crucial components
- **Cloud-ready**: Design with AWS deployment in mind
- **Async-first**: Use asyncio for concurrent agent operations
- **Adaptable structure**: Modify file structure as needed for improvements