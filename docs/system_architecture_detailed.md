# MAAI System Architecture - Detailed Technical View

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    MAAI FRAMEWORK DETAILED ARCHITECTURE                                        │
│                                         Service-Oriented Design                                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           API LAYER                                                            │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│  DeliberationManager (src/maai/core/deliberation_manager.py:26)                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  __init__(config, consensus_service=None, conversation_service=None, memory_service=None)                 │ │
│  │                                                                                                             │ │
│  │  + run_experiment() → ExperimentResults                                                                    │ │
│  │  + consensus_service: ConsensusService    (property access for research)                                  │ │
│  │  + conversation_service: ConversationService                                                               │ │
│  │  + memory_service: MemoryService                                                                           │ │
│  │  + get_experiment_state() → dict                                                                           │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                    │                                                            │
│  run_single_experiment(config) → ExperimentResults (Convenience function with AgentOps init)                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                     │
                                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      ORCHESTRATION LAYER                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│  ExperimentOrchestrator (src/maai/services/experiment_orchestrator.py:20)                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  State Management:                            Lifecycle Methods:                                           │ │
│  │  • config: ExperimentConfig                   • run_experiment(config) → ExperimentResults                │ │
│  │  • agents: List[DeliberationAgent]            • _initialize_agents()                                       │ │
│  │  • moderator: DiscussionModerator             • _initial_evaluation()                                      │ │
│  │  • transcript: List[DeliberationResponse]     • _run_deliberation_rounds() → ConsensusResult               │ │
│  │  • feedback_responses: List[FeedbackResponse] • _collect_feedback(consensus_result)                        │ │
│  │  • current_round: int                         • _finalize_results(consensus_result) → ExperimentResults    │ │
│  │  • start_time: datetime                                                                                     │ │
│  │  • performance_metrics: PerformanceMetrics    Service Integration:                                         │ │
│  │                                               • consensus_service: ConsensusService                        │ │
│  │  Monitoring:                                  • conversation_service: ConversationService                  │ │
│  │  • get_experiment_state() → dict              • memory_service: MemoryService                              │ │
│  │  • reset_experiment()                                                                                       │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                          │                                │                                │
                          ▼                                ▼                                ▼
┌───────────────────────────────────┬─────────────────────────────────────┬───────────────────────────────────────┐
│         CONSENSUS SERVICE         │       CONVERSATION SERVICE         │          MEMORY SERVICE               │
├───────────────────────────────────┼─────────────────────────────────────┼───────────────────────────────────────┤
│                                   │                                     │                                       │
│ ConsensusService                  │ ConversationService                 │ MemoryService                         │
│ (consensus_service.py:85)         │ (conversation_service.py:61)        │ (memory_service.py:74)                │
│                                   │                                     │                                       │
│ ┌─────────────────────────────┐   │ ┌───────────────────────────────┐   │ ┌─────────────────────────────────┐   │
│ │ Core Methods:               │   │ │ Core Methods:                 │   │ │ Core Methods:                   │   │
│ │ • detect_consensus()        │   │ │ • conduct_initial_evaluation()│   │ │ • update_agent_memory()         │   │
│ │   → ConsensusResult         │   │ │   → List[DeliberationResponse]│   │ │   → MemoryEntry                 │   │
│ │ • validate_consensus()      │   │ │ • conduct_round()             │   │ │ • get_agent_memory()            │   │
│ │   → bool                    │   │ │   → List[DeliberationResponse]│   │ │   → AgentMemory                 │   │
│ │ • set_detection_strategy()  │   │ │ • generate_speaking_order()   │   │ │ • get_all_agent_memories()      │   │
│ │                             │   │ │   → List[str]                 │   │ │   → List[AgentMemory]           │   │
│ │ Strategy Pattern:           │   │ │ • set_communication_pattern() │   │ │ • set_memory_strategy()         │   │
│ │ • detection_strategy        │   │ │                               │   │ │                                 │   │
│ │   ConsensusDetectionStrategy│   │ │ Strategy Pattern:             │   │ │ Strategy Pattern:               │   │
│ └─────────────────────────────┘   │ │ • pattern                     │   │ │ • memory_strategy               │   │
│                                   │ │   CommunicationPattern        │   │ │   MemoryStrategy                │   │
│ ┌─────────────────────────────┐   │ │ • speaking_orders: List[]     │   │ │ • agent_memories: Dict          │   │
│ │ Available Strategies:       │   │ └───────────────────────────────┘   │ └─────────────────────────────────┘   │
│ │                             │   │                                     │                                       │
│ │ IdMatchingStrategy          │   │ ┌───────────────────────────────┐   │ ┌─────────────────────────────────┐   │
│ │ ├─ detect() → ConsensusResult│  │ │ Available Patterns:           │   │ │ Available Strategies:           │   │
│ │                             │   │ │                               │   │ │                                 │   │
│ │ ThresholdBasedStrategy      │   │ │ RandomCommunicationPattern    │   │ │ FullMemoryStrategy              │   │
│ │ ├─ __init__(threshold=0.8)  │   │ │ ├─ generate_speaking_order()  │   │ │ ├─ should_include_memory()     │   │
│ │ ├─ detect() → ConsensusResult│  │ │ │   (last≠first constraint)    │   │ │ ├─ get_memory_context_limit() │   │
│ │                             │   │ │                               │   │ │                                 │   │
│ │ SemanticSimilarityStrategy  │   │ │ SequentialCommunicationPattern│   │ │ RecentMemoryStrategy            │   │
│ │ ├─ detect() → ConsensusResult│  │ │ ├─ generate_speaking_order()  │   │ │ ├─ __init__(max_entries=3)    │   │
│ │   (future NLP analysis)     │   │ │ │   (A→B→C→A rotation)         │   │ │ ├─ should_include_memory()     │   │
│ └─────────────────────────────┘   │ │                               │   │ │                                 │   │
│                                   │ │ HierarchicalCommunicationPatt.│   │ │ SelectiveMemoryStrategy         │   │
│ ┌─────────────────────────────┐   │ │ ├─ __init__(leader_count=1)   │   │ │ ├─ __init__(max_rounds=3)     │   │
│ │ Validation Features:        │   │ │ ├─ generate_speaking_order()  │   │ │ ├─ should_include_memory()     │   │
│ │ • Multi-agent participation │   │ │ │   (leaders first, then rest) │   │ │   (round-based filtering)     │   │
│ │ • Reasoning diversity check │   │ └───────────────────────────────┘   │ └─────────────────────────────────┘   │
│ │ • Temporal validation       │   │                                     │                                       │
│ │ • Artificial consensus det. │   │ ┌───────────────────────────────┐   │ ┌─────────────────────────────────┐   │
│ └─────────────────────────────┘   │ │ RoundContext:                 │   │ │ Memory Context Building:        │   │
│                                   │ │ • round_number: int           │   │ │ • Previous conversation         │   │
│                                   │ │ • agents: List[Agent]         │   │ │ • Current round progress        │   │
│                                   │ │ • transcript: List[Response]  │   │ │ • Agent's previous memories     │   │
│                                   │ │ • speaking_order: List[str]   │   │ │ • Strategy filtering applied    │   │
│                                   │ │ • agent_lookup: Dict          │   │ │                                 │   │
│                                   │ └───────────────────────────────┘   │ │ Memory Entry Structure:         │   │
│                                   │                                     │ │ • situation_assessment: str     │   │
│                                   │                                     │ │ • other_agents_analysis: str    │   │
│                                   │                                     │ │ • strategy_update: str          │   │
│                                   │                                     │ │ • round_number: int             │   │
│                                   │                                     │ │ • timestamp: datetime           │   │
│                                   │                                     │ │ • speaking_position: int        │   │
│                                   │                                     │ └─────────────────────────────────┘   │
└───────────────────────────────────┴─────────────────────────────────────┴───────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                          AGENT LAYER                                                           │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│  Agent Creation & Management (src/maai/agents/enhanced.py)                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  create_deliberation_agents(num_agents, models, personalities) → List[DeliberationAgent]                  │ │
│  │  create_discussion_moderator() → DiscussionModerator                                                       │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                    DeliberationAgent                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Core Attributes:                              Behavior Characteristics:                              │ │ │
│  │  │  • agent_id: str (unique identifier)          • Personality-driven reasoning                         │ │ │
│  │  │  • name: str (human-readable)                 • Structured output generation                         │ │ │
│  │  │  • model: str (LLM provider/model)            • Memory integration                                   │ │ │
│  │  │  • personality: str (custom persona)          • Multi-round persistence                              │ │ │
│  │  │  • current_choice: PrincipleChoice            • Veil of ignorance context                            │ │ │
│  │  │                                               • Strategic reasoning                                   │ │ │
│  │  │  Lifecycle Methods:                           • Consensus-oriented communication                      │ │ │
│  │  │  • Created via OpenAI Agents SDK                                                                      │ │ │
│  │  │  • Configured with LitellmModel wrapper       Communication Flow:                                    │ │ │
│  │  │  • Initialized with personality context       • Receives context from MemoryService                  │ │ │
│  │  │  • Maintained across conversation rounds      • Generates public messages                            │ │ │
│  │  │                                               • Updates principle choice                              │ │ │
│  │  │  State Management:                            • Maintains strategic reasoning                         │ │ │
│  │  │  • current_choice updated each round                                                                  │ │ │
│  │  │  • Memory entries stored in MemoryService                                                             │ │ │
│  │  │  • Conversation context via transcript                                                                │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                   DiscussionModerator                                                      │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Purpose: Administrative support for deliberation                                                      │ │ │
│  │  │                                                                                                         │ │ │
│  │  │  Core Functions:                               Technical Implementation:                               │ │ │
│  │  │  • Extract principle choices from free text    • Neutral LLM instance                                │ │ │
│  │  │  • Validate response formatting                • No personality injection                             │ │ │
│  │  │  • Parse structured outputs                    • Simple extraction prompts                           │ │ │
│  │  │  • Quality assurance for data                  • Pattern matching for principle IDs                  │ │ │
│  │  │                                                • Fallback to default choice (1) if unclear           │ │ │
│  │  │  Non-participating Role:                                                                               │ │ │
│  │  │  • Does not contribute opinions                Extraction Process:                                    │ │ │
│  │  │  • Does not influence deliberation             1. Receive agent response text                         │ │ │
│  │  │  • Pure facilitator function                  2. Generate extraction prompt                          │ │ │
│  │  │  • Maintains experiment integrity              3. Parse LLM response for principle ID                 │ │ │
│  │  │                                                4. Create PrincipleChoice object                       │ │ │
│  │  │                                                5. Return structured choice with reasoning             │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         DATA MODEL LAYER                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│  Core Data Models (src/maai/core/models.py) - Pydantic-based validation                                       │
│                                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                    Input/Configuration Models                                               │ │
│  │                                                                                                             │ │
│  │  ExperimentConfig                            PrincipleChoice                                               │ │
│  │  ├─ experiment_id: str                       ├─ principle_id: int (1-4, validated)                       │ │
│  │  ├─ num_agents: int (3-50, validated)       ├─ principle_name: str                                        │ │
│  │  ├─ max_rounds: int (≥1)                    ├─ reasoning: str (truncated to 500 chars)                   │ │
│  │  ├─ decision_rule: str ("unanimity")                                                                       │ │
│  │  ├─ timeout_seconds: int (≥30)              MemoryEntry                                                    │ │
│  │  ├─ models: List[str]                       ├─ round_number: int (≥0)                                     │ │
│  │  ├─ personalities: List[str]                ├─ timestamp: datetime (auto-generated)                       │ │
│  │                                             ├─ situation_assessment: str                                   │ │
│  │                                             ├─ other_agents_analysis: str                                  │ │
│  │                                             ├─ strategy_update: str                                        │ │
│  │                                             ├─ speaking_position: int                                      │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                    Process/State Models                                                    │ │
│  │                                                                                                             │ │
│  │  DeliberationResponse                       AgentMemory                                                    │ │
│  │  ├─ agent_id: str                           ├─ agent_id: str                                               │ │
│  │  ├─ agent_name: str                         ├─ memory_entries: List[MemoryEntry]                          │ │
│  │  ├─ public_message: str                     ├─ add_memory(entry): void                                     │ │
│  │  ├─ private_memory_entry: Optional[Memory]  ├─ get_latest_memory(): Optional[MemoryEntry]                 │ │
│  │  ├─ updated_choice: PrincipleChoice         ├─ get_strategy_evolution(): List[str]                        │ │
│  │  ├─ round_number: int (≥0)                                                                                 │ │
│  │  ├─ timestamp: datetime                     ConsensusResult                                                │ │
│  │  ├─ speaking_position: int                  ├─ unanimous: bool                                             │ │
│  │                                             ├─ agreed_principle: Optional[PrincipleChoice]                 │ │
│  │                                             ├─ dissenting_agents: List[str]                                │ │
│  │                                             ├─ rounds_to_consensus: int (≥0)                               │ │
│  │                                             ├─ total_messages: int (≥0)                                    │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                    Output/Results Models                                                   │ │
│  │                                                                                                             │ │
│  │  ExperimentResults                          FeedbackResponse                                               │ │
│  │  ├─ experiment_id: str                      ├─ agent_id: str                                               │ │
│  │  ├─ configuration: ExperimentConfig         ├─ agent_name: str                                             │ │
│  │  ├─ deliberation_transcript: List[Response] ├─ satisfaction_rating: int (1-10)                            │ │
│  │  ├─ agent_memories: List[AgentMemory]       ├─ fairness_rating: int (1-10)                                │ │
│  │  ├─ speaking_orders: List[List[str]]        ├─ would_choose_again: bool                                    │ │
│  │  ├─ consensus_result: ConsensusResult       ├─ alternative_preference: Optional[int] (1-4)                │ │
│  │  ├─ feedback_responses: List[Feedback]      ├─ reasoning: str                                              │ │
│  │  ├─ performance_metrics: PerformanceMetrics ├─ confidence_in_feedback: float (0.0-1.0)                    │ │
│  │  ├─ start_time: datetime                    ├─ timestamp: datetime                                         │ │
│  │  ├─ end_time: Optional[datetime]                                                                           │ │
│  │                                             PerformanceMetrics                                             │ │
│  │                                             ├─ total_duration_seconds: float                               │ │
│  │                                             ├─ average_round_duration: float                               │ │
│  │                                             ├─ errors_encountered: int                                     │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                               Utility Functions & Constants                                                │ │
│  │                                                                                                             │ │
│  │  DISTRIBUTIVE_JUSTICE_PRINCIPLES: Dict[int, dict]                                                          │ │
│  │  ├─ 1: "Maximize the Minimum Income" (Rawlsian maximin)                                                    │ │
│  │  ├─ 2: "Maximize the Average Income" (Utilitarian)                                                         │ │
│  │  ├─ 3: "Floor Constraint" (Guaranteed minimum + average maximization)                                     │ │
│  │  ├─ 4: "Range Constraint" (Limited inequality + average maximization)                                     │ │
│  │                                                                                                             │ │
│  │  Helper Functions:                                                                                         │ │
│  │  ├─ get_principle_by_id(id) → dict                                                                         │ │
│  │  ├─ get_all_principles_text() → str (formatted for agent prompts)                                         │ │
│  │  ├─ detect_consensus(responses) → ConsensusResult (backward compatibility)                                 │ │
│  │  ├─ get_default_personality() → str                                                                        │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      CONFIGURATION & I/O LAYER                                                 │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│  Configuration Management (src/maai/config/manager.py)                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  load_config_from_file(config_name: str) → ExperimentConfig                                                │ │
│  │  ├─ YAML file loading from configs/ directory                                                              │ │
│  │  ├─ Pydantic validation and type conversion                                                                │ │
│  │  ├─ Default value population                                                                               │ │
│  │  ├─ Error handling with descriptive messages                                                               │ │
│  │                                                                                                             │ │
│  │  Available Configurations:                                                                                 │ │
│  │  ├─ quick_test: 3 agents, 2 rounds (development/testing)                                                  │ │
│  │  ├─ lucas: Custom configuration                                                                            │ │
│  │  ├─ large_group: 8 agents, 10 rounds (comprehensive studies)                                              │ │
│  │  ├─ multi_model: Different LLM providers per agent                                                        │ │
│  │  ├─ default: Standard experimental setup                                                                  │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                                 │
│  Data Export System (src/maai/export/data_export.py)                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  export_experiment_data(results: ExperimentResults) → Dict[str, str]                                       │ │
│  │                                                                                                             │ │
│  │  Output Formats:                                    Export Features:                                       │ │
│  │  ├─ [ID]_complete.json (Full structured data)       ├─ Timestamped filenames                              │ │
│  │  ├─ [ID]_summary.csv (Key metrics)                  ├─ Organized in experiment_results/ directory         │ │
│  │  ├─ [ID]_transcript.csv (Conversation data)         ├─ Configurable output formats                        │ │
│  │  ├─ [ID]_feedback.csv (Agent feedback)              ├─ Multiple simultaneous formats                      │ │
│  │  ├─ [ID]_choice_evolution.csv (Decision timeline)   ├─ Research-friendly structure                        │ │
│  │  ├─ [ID]_transcript.txt (Human-readable)            ├─ Machine-parseable JSON                             │ │
│  │  ├─ [ID]_summary.txt (Executive summary)            ├─ Statistical analysis CSV                           │ │
│  │                                                     ├─ Narrative text formats                             │ │
│  │  Data Enrichment:                                   ├─ Cross-format consistency                           │ │
│  │  ├─ Calculated metrics and derived statistics       ├─ Metadata preservation                               │ │
│  │  ├─ Cross-references and data relationships         ├─ Error handling and validation                       │ │
│  │  ├─ Human-readable formatting and summaries                                                                │ │
│  │  ├─ Timeline and evolution tracking                                                                        │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        TECHNOLOGY FOUNDATION                                                   │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│  OpenAI Agents SDK Integration                         LLM Provider Abstraction                                │
│  ┌─────────────────────────────────────────────────┐   ┌─────────────────────────────────────────────────┐   │
│  │  Core Components:                               │   │  LitellmModel Wrapper:                          │   │
│  │  ├─ Runner.run(agent, prompt) → Result          │   │  ├─ Multi-provider support                      │   │
│  │  ├─ ItemHelpers.text_message_outputs(items)     │   │  ├─ Unified API interface                       │   │
│  │  ├─ trace(name) → context manager               │   │  ├─ Provider-specific optimizations             │   │
│  │                                                 │   │  ├─ Automatic retries and error handling        │   │
│  │  Features:                                      │   │                                                 │   │
│  │  ├─ Agent lifecycle management                  │   │  Supported Providers:                          │   │
│  │  ├─ Conversation state persistence              │   │  ├─ OpenAI (GPT-4.1, GPT-4.1-mini, nano)      │   │
│  │  ├─ Multi-provider LLM support                 │   │  ├─ Anthropic (Claude 3.5, Claude 3)           │   │
│  │  ├─ Built-in observability and tracing          │   │  ├─ DeepSeek (DeepSeek-R1, DeepSeek-V3)        │   │
│  │  ├─ Async operations support                    │   │  ├─ Extensible for future providers            │   │
│  │  ├─ Error handling and resilience               │   │                                                 │   │
│  └─────────────────────────────────────────────────┘   └─────────────────────────────────────────────────┘   │
│                                                                                                                 │
│  Monitoring & Observability (AgentOps)                Supporting Libraries                                     │
│  ┌─────────────────────────────────────────────────┐   ┌─────────────────────────────────────────────────┐   │
│  │  Session Management:                            │   │  Pydantic (Data Validation):                   │   │
│  │  ├─ Experiment session tracking                 │   │  ├─ Type safety and validation                  │   │
│  │  ├─ Distributed tracing across services        │   │  ├─ Automatic serialization/deserialization     │   │
│  │  ├─ Real-time performance monitoring           │   │  ├─ Schema documentation                        │   │
│  │  ├─ Error tracking and alerting                │   │  ├─ Default value handling                      │   │
│  │                                                 │   │                                                 │   │
│  │  Analytics:                                     │   │  AsyncIO (Concurrency):                        │   │
│  │  ├─ Token usage and cost tracking              │   │  ├─ Concurrent LLM operations                   │   │
│  │  ├─ Response time analysis                     │   │  ├─ Non-blocking I/O operations                 │   │
│  │  ├─ Agent behavior patterns                    │   │  ├─ Efficient resource utilization              │   │
│  │  ├─ Session replay capabilities                │   │  ├─ Scalable experiment execution               │   │
│  │  ├─ Comparative experiment analysis            │   │                                                 │   │
│  └─────────────────────────────────────────────────┘   │  YAML (Configuration):                         │   │
│                                                         │  ├─ Human-readable configuration format        │   │
│                                                         │  ├─ Hierarchical configuration structure       │   │
│                                                         │  ├─ Version control friendly                   │   │
│                                                         │  ├─ Comments and documentation support          │   │
│                                                         └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```