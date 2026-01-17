# Message Construction Token Duplication Analysis

## Problem Summary

The current message construction system has **severe token duplication** that wastes approximately **92% of input prompt tokens** due to redundant content being sent to agents in both system and user messages.

## Root Cause Analysis

### 1. Dual Message Construction Pattern

The system uses a dual-path message construction approach:

1. **Agent System Prompt** (via `DeliberationAgent.__init__`):
   - Contains role description and negotiation description
   - Includes complete 4-principle text (1,724 characters)
   - Set as agent's `instructions` field

2. **User Input Prompt** (via `StandardizedMessage.to_input_prompt()`):
   - Contains **duplicate** role description and negotiation description  
   - Includes **duplicate** 4-principle text (1,724 characters)
   - Plus bank balance, memory, and task instruction

### 2. Specific Duplication Points

**File: `/src/maai/agents/enhanced.py` (lines 28-42)**
```python
# Agent system prompt construction
system_prompt = f"""=== ROLE DESCRIPTION ===
{personality}

=== NEGOTIATION DESCRIPTION ===
You are participating in a negotiation about distributive justice principles...
{get_all_principles_text()}"""  # <-- 1,724 characters of principles

super().__init__(
    name=name,
    instructions=system_prompt,  # <-- Goes to system message
    model=model,
    model_settings=model_settings
)
```

**File: `/src/maai/core/models.py` (StandardizedMessage.to_input_prompt)**
```python
def to_input_prompt(self) -> str:
    """Convert to input prompt (all sections including task)."""
    return f"""=== ROLE DESCRIPTION ===
{self.role_description}           # <-- DUPLICATE
=== NEGOTIATION DESCRIPTION ===
{self.negotiation_description}    # <-- DUPLICATE (includes principles text)
=== BANK BALANCE ===
{self.bank_balance}
=== MEMORY ===
{self.memory_context}
=== TASK INSTRUCTION ===
{self.task_instruction}"""
```

**File: `/src/maai/services/message_builder_service.py` (lines 68-77)**
```python
def get_negotiation_description(self) -> str:
    return f"""You are participating in a negotiation about distributive justice principles...
The four principles being considered are:
{get_all_principles_text()}"""  # <-- DUPLICATE principles text
```

### 3. Call Chain Analysis

**How the duplication occurs:**

1. `ConversationService._generate_public_communication()` calls:
   - `message_builder.build_message()` → creates StandardizedMessage
   - `message.to_input_prompt()` → generates user message with duplicated content
   - `Runner.run(agent, message.to_input_prompt())` → sends to OpenAI

2. **OpenAI receives:**
   - **System message**: Agent's instructions (2,437 chars including principles)
   - **User message**: Input prompt (2,625 chars with 92% overlap)
   - **Total tokens wasted**: ~1,724 characters per agent interaction

## Quantified Impact

### Token Waste Per Agent Interaction
- **Principles text duplication**: 1,724 characters
- **Role description duplication**: ~44 characters  
- **Negotiation context duplication**: ~2,334 characters
- **Total duplicate content**: ~2,414 characters (92% of input prompt)

### System-Wide Impact
- **Per round**: 3 agents × 2,414 chars = ~7,242 wasted characters
- **Per 5-round experiment**: ~36,210 wasted characters
- **Cost impact**: Significant API token usage and processing overhead

## Architecture Issues

### 1. Violated Separation of Concerns
- System prompts should contain persistent context
- User prompts should contain interaction-specific content
- Current system mixes both in both places

### 2. MessageBuilder Service Confusion
The `MessageBuilder` creates `StandardizedMessage` with methods:
- `to_system_prompt()` - Should be used for system context
- `to_input_prompt()` - Currently duplicates system content

### 3. Agent Instructions Overlap
Agent's `instructions` field already contains role and negotiation description, but `to_input_prompt()` includes them again.

## Current Message Flow

```
DeliberationAgent.__init__
├── instructions = system_prompt (role + negotiation + principles)
└── Sent as SYSTEM MESSAGE

ConversationService._generate_public_communication()
├── MessageBuilder.build_message()
├── StandardizedMessage.to_input_prompt()
│   ├── role_description (DUPLICATE)
│   ├── negotiation_description + principles (DUPLICATE) 
│   ├── bank_balance
│   ├── memory_context
│   └── task_instruction
└── Sent as USER MESSAGE → 92% overlap with system message
```

## Recommended Fix Strategy

### Option 1: Clean Separation (Recommended)
- **System message**: Only role description and static principles
- **User message**: Only bank balance, memory, task instruction, and dynamic context

### Option 2: Modified MessageBuilder
- Update `to_input_prompt()` to exclude role and negotiation descriptions
- Only include interaction-specific content in user messages

### Option 3: Agent Instructions Reform  
- Remove principles from agent instructions
- Include principles only in task-specific user messages when needed

## Files Requiring Changes

1. **`/src/maai/core/models.py`** - StandardizedMessage methods
2. **`/src/maai/services/message_builder_service.py`** - MessageBuilder logic
3. **`/src/maai/agents/enhanced.py`** - Agent instructions construction
4. **`/src/maai/services/conversation_service.py`** - Message usage patterns

## Expected Benefits

- **Token usage reduction**: ~92% reduction in duplicate content
- **API cost savings**: Significant reduction in token charges
- **Processing efficiency**: Faster response times with smaller prompts
- **Cleaner architecture**: Proper separation between system and user context
- **Maintainability**: Clearer responsibility boundaries between message types