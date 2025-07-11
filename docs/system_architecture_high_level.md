# MAAI System Architecture - High Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT DISTRIBUTIVE JUSTICE EXPERIMENT                 │
│                              (MAAI FRAMEWORK)                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EXPERIMENT LIFECYCLE                              │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────────┤
│   INITIALIZE    │   INDIVIDUAL    │   DELIBERATE    │      FINALIZE &         │
│     AGENTS      │   EVALUATION    │   (ROUNDS 1-N)  │       EXPORT            │
│                 │   (ROUND 0)     │                 │                         │
│ • Create agents │ • Each agent    │ • Multi-round   │ • Collect feedback      │
│ • Assign        │   privately     │   discussions   │ • Calculate metrics     │
│   personalities │   evaluates     │ • Consensus     │ • Export multiple       │
│ • Initialize    │   4 principles  │   detection     │   formats (JSON/CSV)    │
│   memory        │ • No discussion │ • Memory &      │ • Generate summaries    │
│                 │   yet           │   strategy      │                         │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CORE SERVICE ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────────────┐
                              │  DELIBERATION        │
                              │     MANAGER          │
                              │ (API Compatibility)  │
                              └──────────┬───────────┘
                                         │
                              ┌──────────▼───────────┐
                              │  EXPERIMENT          │
                              │   ORCHESTRATOR       │
                              │ (Coordinates All)    │
                              └──┬───┬───┬───┬───────┘
                                 │   │   │   │
            ┌────────────────────┘   │   │   └────────────────────┐
            │                        │   │                        │
  ┌─────────▼─────────┐   ┌─────────▼──▼────────┐   ┌────────────▼────────────┐
  │   CONSENSUS       │   │    CONVERSATION     │   │       MEMORY            │
  │    SERVICE        │   │      SERVICE        │   │      SERVICE            │
  │                   │   │                     │   │                         │
  │ • Detect consensus│   │ • Speaking orders   │   │ • Agent memory mgmt     │
  │ • Validate        │   │ • Communication     │   │ • Context building      │
  │   agreements      │   │   patterns          │   │ • Strategy retention    │
  │ • Strategy        │   │ • Round execution   │   │ • Memory filtering      │
  │   switching       │   │                     │   │                         │
  └───────────────────┘   └─────────────────────┘   └─────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AGENT ECOSYSTEM                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DELIBERATION AGENTS                               │
│                                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │   AGENT A   │    │   AGENT B   │    │   AGENT C   │    │     ...     │      │
│  │             │    │             │    │             │    │             │      │
│  │ Personality:│    │ Personality:│    │ Personality:│    │ Personality:│      │
│  │ "Economist" │    │"Philosopher"│    │ "Pragmatist"│    │   Custom    │      │
│  │             │    │             │    │             │    │             │      │
│  │ Current     │    │ Current     │    │ Current     │    │ Current     │      │
│  │ Choice: P2  │    │ Choice: P1  │    │ Choice: P3  │    │ Choice: P?  │      │
│  │             │    │             │    │             │    │             │      │
│  │ Private     │    │ Private     │    │ Private     │    │ Private     │      │
│  │ Memory &    │    │ Memory &    │    │ Memory &    │    │ Memory &    │      │
│  │ Strategy    │    │ Strategy    │    │ Strategy    │    │ Strategy    │      │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────┘

                                ┌─────────────────────┐
                                │ DISCUSSION MODERATOR│
                                │                     │
                                │ • Extract choices   │
                                │ • Validate responses│
                                │ • Neutral support   │
                                └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                       DISTRIBUTIVE JUSTICE PRINCIPLES                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┬──────────────────────┬──────────────────────┬──────────────────────┐
│    PRINCIPLE 1       │    PRINCIPLE 2       │    PRINCIPLE 3       │    PRINCIPLE 4       │
│                      │                      │                      │                      │
│  MAXIMIZE THE        │  MAXIMIZE THE        │  FLOOR CONSTRAINT    │  RANGE CONSTRAINT    │
│  MINIMUM INCOME      │  AVERAGE INCOME      │                      │                      │
│                      │                      │  • Guaranteed        │  • Limited           │
│  (Rawlsian)          │  (Utilitarian)       │    minimum income    │    inequality gap    │
│  Ensure worst-off    │  Greatest total      │  • Then maximize     │  • Then maximize     │
│  are as well-off     │  wealth regardless   │    average above     │    average income    │
│  as possible         │  of distribution     │    floor             │                      │
└──────────────────────┴──────────────────────┴──────────────────────┴──────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                            TECHNOLOGY FOUNDATION                                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LLM PROVIDERS                                     │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────────┤
│     OPENAI      │   ANTHROPIC     │    DEEPSEEK     │        FUTURE           │
│                 │                 │                 │                         │
│ • GPT-4.1       │ • Claude 3.5    │ • DeepSeek-R1   │ • Extensible for        │
│ • GPT-4.1-mini  │ • Claude 3      │ • DeepSeek-V3   │   new providers         │
│ • GPT-4.1-nano  │ • Other models  │                 │ • Plugin architecture  │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         UNDERLYING FRAMEWORKS                                  │
├──────────────────────────────┬──────────────────────────────────────────────────┤
│         OPENAI AGENTS SDK    │              SUPPORTING LIBRARIES               │
│                              │                                                  │
│ • Agent lifecycle mgmt       │ • Pydantic (data validation)                    │
│ • Multi-provider support     │ • AsyncIO (concurrent operations)               │
│ • Conversation state         │ • YAML (configuration)                          │
│ • Observability & tracing    │ • AgentOps (monitoring)                         │
└──────────────────────────────┴──────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW SUMMARY                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

Configuration (YAML) → Experiment Creation → Agent Initialization → 
Individual Evaluation → Multi-Round Deliberation → Consensus Detection → 
Feedback Collection → Result Packaging → Multi-Format Export

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUT FORMATS                                    │
├──────────────┬──────────────┬──────────────┬──────────────┬────────────────────┤
│     JSON     │     CSV      │     TXT      │   SUMMARY    │     RESEARCH       │
│              │              │              │              │                    │
│ • Complete   │ • Tabular    │ • Human-     │ • Executive  │ • Choice evolution │
│   structured │   data for   │   readable   │   overview   │ • Memory timeline  │
│   export     │   analysis   │   transcript │ • Key        │ • Speaking orders  │
│ • Machine    │ • Statistics │ • Narrative  │   metrics    │ • Performance data │
│   parseable  │   friendly   │   format     │ • Outcomes   │                    │
└──────────────┴──────────────┴──────────────┴──────────────┴────────────────────┘
```