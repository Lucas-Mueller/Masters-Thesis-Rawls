# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Master's thesis project implementing an experimental framework to test distributive justice principles using autonomous agents. The project simulates Rawls' "veil of ignorance" scenario where agents must unanimously agree on a principle of distributive justice without knowing their future economic position.

## Architecture

- **Core Framework**: Built on OpenAI Agents SDK (agents_sdk) - documentation available in `knowledge_base/agents_sdk/`
- **Main Application**: `MAAI.py` - Contains the complete experimental logic
- **Agent System**: Multi-agent deliberation system with 4 configurable agents
- **Logging**: Results saved to `Logs_MAAI/` directory as CSV files with timestamps

## Key Components

### Agent Configuration
- Base agents (1-4) with different model configurations (GPT-4.1, Claude, DeepSeek)
- Agreement judge agent for evaluating responses
- Agents can be configured with different LLM providers via LitellmModel

### Experimental Flow
1. **Initialization Phase**: All agents individually evaluate 4 distributive justice principles
2. **Deliberation Phase**: Agents discuss until unanimous agreement (future implementation)
3. **Data Collection**: Responses, choices, and agreement status tracked in pandas DataFrame

### Distributive Justice Principles
1. Maximize the Minimum Income (Rawlsian difference principle)
2. Maximize the Average Income (utilitarian)
3. Maximize Average Income with Floor Constraint (hybrid with safety net)
4. Maximize Average Income with Range Constraint (hybrid with inequality limits)

## Development Commands

### Setup
```bash
pip install -r requirements.txt
```

### Running the Experiment

**Phase 1 Enhanced System:**
```bash
# Run basic test
python test_phase1.py

# Run comprehensive tests
python test_phase1_comprehensive.py

# Run demonstrations
python demo_phase1.py
python demo_phase2.py

# Run comprehensive tests
python test_phase2_feedback.py
python test_phase2_logging.py
python test_phase2_config.py

# Use configuration management
python -c "
import asyncio
from config_manager import load_config_from_file, PresetConfigs
from deliberation_manager import run_single_experiment

# Use preset configuration
config = PresetConfigs.quick_test()
asyncio.run(run_single_experiment(config))

# Or load from YAML file
config = load_config_from_file('quick_test')
asyncio.run(run_single_experiment(config))
"
```

**Legacy System:**
```bash
python MAAI.py
```

### Environment Variables Required
- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `ANTHROPIC_API_KEY`
- `AGENT_OPS_API_KEY`

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

## File Structure Notes

**Enhanced System (Phases 1 & 2):**
- `deliberation_manager.py`: Core multi-agent deliberation engine
- `agents_enhanced.py`: Enhanced agent classes with specialized roles
- `models.py`: Structured data models with Pydantic validation
- `data_export.py`: Multi-format data export system (JSON, CSV, TXT)
- `config_manager.py`: YAML configuration management system
- `configs/`: YAML configuration files for different scenarios
- `test_phase1*.py`: Phase 1 functionality tests
- `test_phase2*.py`: Phase 2 functionality tests
- `demo_phase1.py`: Phase 1 demonstration script
- `demo_phase2.py`: Phase 2 demonstration script
- `implementation_plan.md`: Detailed implementation roadmap

**Legacy System:**
- `MAAI.py`: Original experimental logic and agent definitions
- `requirements.txt`: Python dependencies
- `design_goal.md`: Detailed experimental design and objectives
- `Logs_MAAI/`: CSV output files with experimental results
- `agentops.log`: Agent operations logging

## Current Implementation Status

### ✅ Phase 1 - Core Multi-Agent Deliberation System (COMPLETED)
- ✅ Enhanced agent architecture (`DeliberationAgent`, `ConsensusJudge`, `DiscussionModerator`)
- ✅ Multi-round deliberation engine with `DeliberationManager`
- ✅ Consensus detection and resolution system
- ✅ Structured data models with Pydantic validation (`models.py`)
- ✅ Comprehensive testing framework (`test_phase1.py`, `test_phase1_comprehensive.py`)
- ✅ Performance metrics tracking and error handling
- ✅ Rich communication transcripts and data collection

### ✅ Phase 2 - Data Collection Enhancement (COMPLETED)
- ✅ Post-experiment feedback collection (`FeedbackCollector` agent)
- ✅ Enhanced logging system with multiple formats (`data_export.py`)
- ✅ Configuration management system (`config_manager.py`)
- ✅ YAML configuration files in `configs/` directory
- ✅ Preset configurations for common scenarios

## Testing Strategy

- Create unit tests for agent response parsing
- Test agreement detection logic
- Validate CSV logging functionality
- Test async operations with multiple agents

World Knowledge:
GPT-4.1 exists as well as GPT-4.1 mini and nano
This project is based on the Open AI Agents sdk also known as agents_sdk, you dont know this framework sinc it was published after your knowledge cut-off. The documentation of the Open AI Agents SDK is in the knowledge base. Use it if you need it. You find it in this folder  knowledge_base/agents_sdk
In the folder documentation is a visualization of this system. Pleae ignore this. 


Design Principles: 
Simplistic code
Code should be concise and easy to understand. 
I have a great understanding of python intermediate skills in HTML and CSS but are open to learn new langauges and frameworks if they bring value. 
Keep the code simple but effective
Create modular code 
Adapt the file strucutre if needed
Ask questions back if you are unsure
Make improvements for suggestions 
Be open to challgenge me 
Document everything in the code
Create test for crucial components
Keep in mind that I want to host this project at some point via a Cloud provider like AWS
Create Unit test for subsystems 
Always challenge yourself to create simple and easy to understand code