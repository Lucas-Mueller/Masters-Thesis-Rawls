# MEMORANDUM

**TO:** Research Team  
**FROM:** System Architecture Team  
**DATE:** July 10, 2025  
**RE:** Multi-Agent Distributive Justice Experiment (MAAI) System Architecture

---

## EXECUTIVE SUMMARY

The Multi-Agent Distributive Justice Experiment (MAAI) framework implements a sophisticated simulation of Rawls' "veil of ignorance" scenario. The system coordinates autonomous AI agents in structured deliberation to reach unanimous agreement on distributive justice principles without knowing their future economic positions.

**Key Architecture Characteristics:**
- **Decomposed Service Architecture:** Four specialized services handle distinct responsibilities
- **OpenAI Agents SDK Foundation:** Built on enterprise-grade agent orchestration platform
- **Multi-Provider LLM Support:** Integrates GPT, Claude, and DeepSeek models
- **Configurable Strategy Patterns:** Pluggable algorithms for consensus, communication, and memory
- **Comprehensive Data Export:** Multi-format results for research analysis

---

## SYSTEM OVERVIEW

### Core Purpose
The system simulates multi-agent deliberation under uncertainty to study how rational agents reach consensus on distributive justice when they cannot predict their future economic status. This addresses fundamental questions in political philosophy and game theory.

### Deliberation Process Flow
1. **Agent Initialization:** Create agents with unique personalities behind "veil of ignorance"
2. **Individual Evaluation:** Each agent privately assesses four distributive justice principles
3. **Multi-Round Deliberation:** Agents engage in structured discussion until unanimous agreement
4. **Consensus Detection:** System validates agreement using configurable detection algorithms
5. **Feedback Collection:** Post-experiment agent interviews capture decision reasoning
6. **Data Export:** Results exported in multiple formats for comprehensive analysis

### Distributive Justice Principles
The system presents four well-established principles:

1. **Maximize the Minimum Income** - Rawlsian maximin principle ensuring the worst-off are as well-off as possible
2. **Maximize the Average Income** - Utilitarian approach maximizing total societal wealth
3. **Floor Constraint Hybrid** - Guaranteed minimum income with average maximization above that floor
4. **Range Constraint Hybrid** - Limited inequality gap with average income maximization

---

## DETAILED ARCHITECTURE

### Service-Oriented Design

The system employs a decomposed architecture with four specialized services, each implementing the Strategy pattern for research flexibility:

#### 1. ConsensusService (`src/maai/services/consensus_service.py`)
**Responsibility:** Detecting and validating unanimous agreement among agents

**Core Components:**
- **ConsensusDetectionStrategy (Abstract):** Interface for different consensus algorithms
- **IdMatchingStrategy:** Simple principle ID comparison (current default)
- **ThresholdBasedStrategy:** Configurable percentage-based agreement (e.g., 80%)
- **SemanticSimilarityStrategy:** Future NLP-based reasoning analysis

**Key Methods:**
- `detect_consensus(responses) → ConsensusResult`: Main consensus detection
- `validate_consensus(result, responses) → bool`: Authenticity verification
- `set_detection_strategy(strategy)`: Runtime strategy switching

**Validation Mechanisms:**
- Multi-agent participation verification
- Reasoning diversity checks to prevent artificial consensus
- Temporal validation ensuring deliberation occurred

#### 2. ConversationService (`src/maai/services/conversation_service.py`)
**Responsibility:** Managing agent communication flow and speaking patterns

**Core Components:**
- **CommunicationPattern (Abstract):** Interface for speaking order generation
- **RandomCommunicationPattern:** Random order with last-speaker constraint (current default)
- **SequentialCommunicationPattern:** Fixed rotation (A→B→C→A...)
- **HierarchicalCommunicationPattern:** Designated leaders speak first

**Key Methods:**
- `conduct_initial_evaluation(agents, transcript)`: Individual principle assessment
- `conduct_round(round_context, memory_service, moderator)`: Single deliberation round
- `generate_speaking_order(agents, round_num)`: Order determination
- `set_communication_pattern(pattern)`: Runtime pattern switching

**Communication Constraints:**
- Last speaker in round N cannot be first speaker in round N+1
- Maximum 10 attempts to generate valid speaking order before fallback
- Position tracking for memory and transcript correlation

#### 3. MemoryService (`src/maai/services/memory_service.py`)
**Responsibility:** Centralized agent memory management and strategy application

**Core Components:**
- **MemoryStrategy (Abstract):** Interface for memory retention policies
- **FullMemoryStrategy:** Retain all previous memories (current default)
- **RecentMemoryStrategy:** Keep only last N memory entries
- **SelectiveMemoryStrategy:** Remember only last N rounds

**Key Methods:**
- `update_agent_memory(agent, round, position, transcript)`: Create new memory entry
- `get_agent_memory(agent_id)`: Retrieve complete agent memory
- `set_memory_strategy(strategy)`: Runtime strategy switching

**Memory Structure:**
Each memory entry contains:
- **Situation Assessment:** Agent's understanding of current deliberation state
- **Other Agents Analysis:** Evaluation of other agents' positions and motivations
- **Strategy Update:** Private tactical planning for next communication

#### 4. ExperimentOrchestrator (`src/maai/services/experiment_orchestrator.py`)
**Responsibility:** High-level coordination of all services and experiment lifecycle

**Core Responsibilities:**
- Agent initialization with personality configuration
- Service coordination and data flow management
- Performance metrics collection and timing
- Result packaging and export coordination

**Key Methods:**
- `run_experiment(config)`: Complete experiment execution
- `get_experiment_state()`: Real-time monitoring data
- `reset_experiment()`: Clean state for new experiments

---

## DATA MODELS AND FLOW

### Core Data Structures

#### ExperimentConfig
Configuration specification containing:
- **Experiment metadata:** ID, agent count, round limits
- **Model configuration:** LLM providers and specific models per agent
- **Personality definitions:** Custom agent personas or references
- **Timeout and decision rule parameters**

#### DeliberationResponse
Individual agent communication record:
- **Public message:** Content shared with other agents
- **Private memory entry:** Internal analysis and strategy
- **Updated principle choice:** Current preference with reasoning
- **Metadata:** Timestamp, round number, speaking position

#### ConsensusResult
Agreement detection outcome:
- **Unanimous flag:** Boolean consensus indicator
- **Agreed principle:** Chosen distributive justice principle (if unanimous)
- **Dissenting agents:** List of non-agreeing agent IDs
- **Convergence metrics:** Rounds to consensus, total messages

#### ExperimentResults
Complete experiment package:
- **Configuration snapshot:** Exact experimental parameters
- **Full transcript:** Complete conversation history
- **Agent memories:** Private reasoning evolution
- **Performance metrics:** Timing and error data
- **Speaking orders:** Communication sequence records

### Data Flow Architecture

```
ExperimentConfig → ExperimentOrchestrator → Services → ExperimentResults
                         ↓
                  ┌─────────────┬─────────────┬─────────────┐
                  ↓             ↓             ↓             ↓
           ConsensusService ConversationService MemoryService AgentManagement
                  ↓             ↓             ↓             ↓
              Detection      Speaking      Memory        Agent
              Strategies     Patterns     Strategies    Instances
                  ↓             ↓             ↓             ↓
              Validation    Communication  Context      LLM
              Results       Coordination   Building     Calls
                  ↓             ↓             ↓             ↓
                  └─────────────┴─────────────┴─────────────┘
                                     ↓
                            DeliberationResponse[]
                                     ↓
                              Data Export Layer
                                     ↓
                        Multiple Format Outputs
                    (JSON, CSV, TXT, Structured)
```

---

## AGENT SYSTEM INTEGRATION

### OpenAI Agents SDK Integration
The system leverages the OpenAI Agents SDK for:
- **Agent lifecycle management:** Creation, configuration, and cleanup
- **Conversation state management:** Maintaining context across rounds
- **Multi-provider support:** Seamless switching between LLM providers
- **Observability:** Built-in tracing and monitoring capabilities

### Agent Types and Roles

#### DeliberationAgent (`src/maai/agents/enhanced.py`)
**Primary reasoning agents** participating in deliberation:
- **Personality-driven behavior:** Configurable personas affecting reasoning style
- **Structured output generation:** Consistent principle choice formatting
- **Memory integration:** Access to private analysis and strategy
- **Multi-round persistence:** Maintaining context across deliberation phases

#### DiscussionModerator
**Supporting agent** for administrative tasks:
- **Choice extraction:** Parsing principle selections from free-form text
- **Response validation:** Ensuring proper formatting and completeness
- **Neutral facilitation:** No opinion injection in deliberation content

### LLM Provider Support

#### Supported Models
- **OpenAI:** GPT-4.1, GPT-4.1-mini, GPT-4.1-nano
- **Anthropic:** Claude family models (with API key)
- **DeepSeek:** DeepSeek reasoning models (with API key)

#### Model Assignment Strategies
- **Per-agent specification:** Different models for different agents
- **Heterogeneous experiments:** Comparing reasoning across LLM families
- **Fallback mechanisms:** Graceful degradation if preferred model unavailable

---

## CONFIGURATION SYSTEM

### YAML Configuration Files (`configs/`)
The system uses declarative YAML configuration for experiment specification:

```yaml
experiment_id: experiment_name
experiment:
  num_agents: 3-50
  max_rounds: 1-100
  decision_rule: "unanimity"
  timeout_seconds: 30-3600
  models: [model_list]

personalities:
  - "Custom personality description"
  - "Another agent persona"

output:
  directory: "experiment_results"
  formats: [json, csv, txt]
  include_feedback: true
```

### Personality System
- **Custom definitions:** Full-text personality descriptions
- **Template references:** Saved personality configurations
- **Default fallback:** Standard neutral persona for unspecified agents
- **Dynamic assignment:** Personality count can differ from agent count

### Configuration Loading (`src/maai/config/manager.py`)
- **File-based loading:** `load_config_from_file(config_name)`
- **Validation:** Pydantic model verification
- **Environment integration:** API key and runtime parameter injection

---

## EXECUTION FLOW DETAIL

### Phase 1: Initialization
1. **Configuration parsing:** YAML to Pydantic model conversion
2. **Service instantiation:** Creating service instances with default strategies
3. **Agent creation:** Instantiating DeliberationAgent objects with personalities
4. **Memory initialization:** Setting up AgentMemory objects for each agent
5. **AgentOps integration:** Enabling experiment tracing and monitoring

### Phase 2: Initial Evaluation (Round 0)
1. **Speaking order generation:** Random order using ConversationService
2. **Sequential evaluation:** Each agent individually assesses principles
3. **Choice extraction:** DiscussionModerator parses principle selections
4. **Transcript recording:** Storing individual evaluations
5. **Early consensus check:** Detecting immediate unanimous agreement

### Phase 3: Multi-Round Deliberation (Rounds 1-N)
**Per Round Process:**
1. **Speaking order generation:** Applying communication pattern with constraints
2. **Agent memory updates:** MemoryService builds private context and strategy
3. **Public communication:** Agents communicate based on memory analysis
4. **Choice extraction and recording:** Updating agent preferences
5. **Consensus detection:** ConsensusService evaluates agreement status
6. **Continuation decision:** Proceeding if no consensus and rounds remaining

### Phase 4: Feedback Collection
1. **Consensus outcome analysis:** Determining final agreement status
2. **Satisfaction calculation:** Simple algorithm based on final choices
3. **Feedback generation:** Creating FeedbackResponse objects for each agent
4. **Reasoning capture:** Recording decision justifications

### Phase 5: Result Finalization
1. **Performance metric calculation:** Timing and error rate compilation
2. **Data package assembly:** Creating complete ExperimentResults object
3. **Memory collection:** Gathering all AgentMemory objects
4. **Speaking order compilation:** Recording all communication sequences

### Phase 6: Data Export
1. **Multi-format export:** JSON, CSV, TXT generation via export service
2. **File organization:** Timestamped files in configured output directory
3. **Summary generation:** Executive summary and transcript creation
4. **Metadata inclusion:** Configuration and performance data preservation

---

## PERFORMANCE AND MONITORING

### AgentOps Integration
- **Distributed tracing:** Complete experiment execution visibility
- **Performance metrics:** Timing, token usage, and error tracking
- **Agent behavior analysis:** Individual agent performance patterns
- **Session replay:** Detailed execution reconstruction capabilities

### Error Handling and Resilience
- **Graceful degradation:** Continuing experiments despite individual failures
- **Timeout management:** Per-round and total experiment time limits
- **API failure recovery:** Retry logic for LLM provider connectivity issues
- **State preservation:** Maintaining experiment integrity across failures

### Performance Characteristics
- **Typical execution time:** 1-10 minutes depending on configuration
- **Scalability:** Supports 3-50 agents with linear performance degradation
- **Memory usage:** Proportional to conversation length and agent count
- **API efficiency:** Batched operations where possible to minimize costs

---

## BACKWARD COMPATIBILITY AND MIGRATION

### API Preservation
The refactored system maintains complete backward compatibility:
- **Existing import statements:** All original imports continue to work
- **Method signatures:** No changes to public DeliberationManager interface
- **Configuration format:** Existing YAML files require no modification
- **Result format:** ExperimentResults structure unchanged

### Gradual Adoption Path
Researchers can adopt new capabilities incrementally:
1. **Continue using defaults:** No immediate changes required
2. **Experiment with services:** Access services through manager properties
3. **Custom configurations:** Inject custom services into DeliberationManager
4. **Advanced research:** Direct service usage for specialized experiments

### Legacy Support
- **Original monolithic methods:** Still available but delegated to services
- **Import compatibility:** Old import paths continue to work
- **Configuration compatibility:** All existing configurations remain valid

---

## CONCLUSION

The MAAI system provides a robust, flexible platform for studying multi-agent deliberation under uncertainty. The service-oriented architecture enables sophisticated research while maintaining simplicity for basic usage. The system successfully balances research flexibility with operational reliability, providing a solid foundation for distributive justice experimentation.

**Key Strengths:**
- **Modular design** enabling independent component research
- **Strategy pattern implementation** allowing algorithm experimentation
- **Comprehensive data capture** for thorough analysis
- **Production-ready reliability** with proper error handling and monitoring
- **Research flexibility** without sacrificing ease of use

The architecture positions the system as both a practical research tool and a platform for advancing understanding of multi-agent consensus formation in philosophical and economic contexts.