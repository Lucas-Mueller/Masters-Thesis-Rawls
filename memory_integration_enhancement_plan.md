# Memory Integration Enhancement Plan

## Problem Statement

**Current Issue**: Agents are not receiving their complete memory state at each turn during group deliberation. The current system has:

1. **Rich Memory Generation**: Complex `MemoryService` generates detailed Phase 1 and Phase 2 memories
2. **Basic Memory Provision**: `SimpleMemoryService` provides only basic string context to agents
3. **Missing Integration**: Phase 1 consolidated memories and detailed Phase 2 memories are not accessible during agent turns
4. **Fragmented Systems**: Two parallel memory systems with no integration

**Requirement**: Provide agents with their current complete memory state at each turn, positioned right after their bank balance information in the standardized message structure.

## Current Message Structure

```
StandardizedMessage:
1. Role Description       (Working ✅)
2. Negotiation Description (Working ✅) 
3. Bank Balance          (Working ✅) ← Properly integrated with EarningsTrackingService
4. Memory Context        (Limited ❌) ← Currently basic string from SimpleMemoryService
5. Task Instruction      (Working ✅)
```

## Current Memory Systems Analysis

### A. Legacy MemoryService (Complex, Feature-Rich)
- **Phase 1 Memories**: Individual experiences, consolidated insights
- **Phase 2 Memories**: Structured deliberation memories with reasoning
- **Memory Strategies**: Recent, decomposed, phase-aware decomposed
- **Data Structure**: Rich `EnhancedAgentMemory` objects
- **Status**: Generated but NOT provided to agents during turns

### B. SimpleMemoryService (Basic, Currently Used)
- **Basic Storage**: Simple string memory per agent
- **Last Interactions**: Input/output pairs
- **Bank Balance**: Placeholder integration
- **Data Structure**: Dict[str, str]
- **Status**: Used for agent messages but lacks depth

## Solution Design

### Phase 1: Enhanced Memory Context Integration

#### 1.1 Unified Memory Context Builder
**Goal**: Create a comprehensive memory context that combines both systems

**Implementation**: 
- Create `EnhancedMemoryContextBuilder` service
- Integrate both `MemoryService` and `SimpleMemoryService` data
- Generate structured memory context for agent messages

**Components**:
```python
class EnhancedMemoryContextBuilder:
    def __init__(self, memory_service: MemoryService, simple_memory_service: SimpleMemoryService):
        self.memory_service = memory_service
        self.simple_memory_service = simple_memory_service
    
    def build_comprehensive_memory_context(self, agent_id: str, round_number: int) -> str:
        """Build complete memory context including Phase 1 and Phase 2 memories."""
        # Combine Phase 1 consolidated memories + Phase 2 deliberation memories + recent interactions
```

#### 1.2 Memory Context Structure
**Standardized Format**:
```
=== YOUR MEMORY ===

PHASE 1 INDIVIDUAL EXPERIENCE:
- Initial preference: [Principle X - reasoning]
- Key learning: [From detailed examples]
- Individual rounds: [Economic outcomes and strategic insights]
- Post-individual preference: [Updated preference with reasoning]

PHASE 2 GROUP DELIBERATION HISTORY:
- Round 1: [Your position, other agents' positions, key arguments]
- Round 2: [Strategic observations, preference changes]
- [Additional rounds as available]

RECENT INTERACTION:
- Last input: [Previous prompt/question]
- Last output: [Your previous response]

STRATEGIC NOTES:
- [Key insights from memory generation]
- [Patterns observed about other agents]
- [Strategic considerations for next moves]
```

### Phase 2: MessageBuilder Integration

#### 2.1 Enhanced MessageBuilder
**Update**: Modify `MessageBuilderService` to use enhanced memory context

**Changes**:
```python
def build_message(self, 
                 agent: DeliberationAgent,
                 task_instruction: str,
                 round_number: int,  # New parameter
                 memory_context_builder: EnhancedMemoryContextBuilder) -> StandardizedMessage:
    
    # Get comprehensive memory context
    enhanced_memory_context = memory_context_builder.build_comprehensive_memory_context(
        agent.agent_id, round_number
    )
    
    return StandardizedMessage(
        role_description=self.get_role_description(agent),
        negotiation_description=self.get_negotiation_description(),
        bank_balance=self.get_standardized_bank_balance(agent.agent_id),
        memory_context=enhanced_memory_context,  # Enhanced memory
        task_instruction=task_instruction
    )
```

#### 2.2 ConversationService Updates
**Update Both Methods**:
- `conduct_round_simplified()`: Use enhanced memory context
- `conduct_round()`: Integrate enhanced memory with existing complex memory updates

### Phase 3: Service Integration

#### 3.1 ExperimentOrchestrator Integration
**Initialize Enhanced Services**:
```python
# Initialize enhanced memory context builder
self.enhanced_memory_builder = EnhancedMemoryContextBuilder(
    memory_service=self.memory_service,
    simple_memory_service=self.simple_memory_service
)

# Update message builder to use enhanced memory
self.message_builder.memory_context_builder = self.enhanced_memory_builder
```

#### 3.2 Phase 1 Memory Consolidation Bridge
**Ensure Phase 1 Memories Flow to Phase 2**:
- Verify consolidated Phase 1 memories are accessible in Phase 2
- Update memory consolidation process to work with enhanced builder
- Test Phase 1 → Phase 2 memory continuity

## Implementation Steps

### Step 1: Create EnhancedMemoryContextBuilder Service
- **File**: `src/maai/services/enhanced_memory_context_builder.py`
- **Dependencies**: MemoryService, SimpleMemoryService
- **Methods**: 
  - `build_comprehensive_memory_context(agent_id, round_number)`
  - `format_phase1_memories(agent_id)`
  - `format_phase2_memories(agent_id, round_number)`
  - `format_strategic_notes(agent_id)`

### Step 2: Update MessageBuilderService
- **File**: `src/maai/services/message_builder_service.py`
- **Changes**: 
  - Add `memory_context_builder` parameter to `build_message()`
  - Add `round_number` parameter for context
  - Remove simple memory dependency

### Step 3: Update ConversationService
- **File**: `src/maai/services/conversation_service.py`
- **Changes**:
  - Update `conduct_round_simplified()` to use enhanced memory
  - Update `conduct_round()` to integrate enhanced memory
  - Pass `round_number` to message builder

### Step 4: Update ExperimentOrchestrator
- **File**: `src/maai/services/experiment_orchestrator.py`
- **Changes**:
  - Initialize `EnhancedMemoryContextBuilder`
  - Update service dependencies
  - Ensure Phase 1 memory consolidation works with enhanced system

### Step 5: Testing and Validation
- **Unit Tests**: Test enhanced memory context generation
- **Integration Tests**: Test complete message flow with enhanced memory
- **Memory Continuity Tests**: Verify Phase 1 → Phase 2 memory flow
- **Agent Turn Tests**: Verify agents receive complete memory at each turn

## Expected Outcomes

### Before Implementation
```
Agent receives:
"You have a current bank balance of $2.3456"
"Basic memory: Last interaction was about principle 1."
```

### After Implementation
```
Agent receives:
"You have a current bank balance of $2.3456"

"=== YOUR MEMORY ===

PHASE 1 INDIVIDUAL EXPERIENCE:
- Initial preference: Principle 1 (floor income) - believed it ensures fairness for all
- Key learning: From examples learned that principle 2 can sometimes yield higher total welfare
- Individual rounds: Experienced higher income (class HIGH) when principle 2 was applied
- Post-individual preference: Updated to principle 2 - efficiency gains convinced me

PHASE 2 GROUP DELIBERATION HISTORY:
- Round 1: I argued for principle 2, Agent_2 preferred principle 1, no consensus
- Round 2: Agent_2 raised fairness concerns, I acknowledged but maintained efficiency focus

RECENT INTERACTION:
- Last input: What principle do you now support and why?
- Last output: I support principle 2 because efficiency benefits outweigh concerns

STRATEGIC NOTES:
- Agent_2 consistently prioritizes fairness over efficiency
- Need to address fairness concerns while maintaining efficiency argument
- Consider proposing principle 3 with floor constraint as compromise"
```

## Configuration Changes

### New Configuration Options
```yaml
# Enhanced Memory Configuration
memory_integration:
  enabled: true
  include_phase1_memories: true
  include_strategic_notes: true
  max_memory_length: 2000  # Characters
  format_style: "structured"  # or "narrative"

# Backward Compatibility
enable_phase1_memory: true  # Still works
```

## Risk Mitigation

### 1. Performance Impact
- **Risk**: Enhanced memory context increases message length
- **Mitigation**: Add `max_memory_length` configuration option
- **Monitoring**: Track message length and agent response times

### 2. Backward Compatibility
- **Risk**: Breaking existing configurations
- **Mitigation**: Keep existing `enable_phase1_memory` option working
- **Migration**: Provide configuration migration guide

### 3. Memory Complexity
- **Risk**: Overly complex memory contexts confusing agents
- **Mitigation**: Structured formatting with clear sections
- **Testing**: A/B test memory formats with different agents

### 4. Service Dependencies
- **Risk**: Circular dependencies between memory services
- **Mitigation**: Clear service initialization order
- **Architecture**: Dependency injection pattern

## Success Metrics

1. **Memory Provision**: 100% of agent turns receive complete memory context
2. **Phase 1 Integration**: Phase 1 memories appear in 100% of Phase 2 agent contexts
3. **Strategic Continuity**: Agents demonstrate memory of previous positions and reasoning
4. **Performance**: No significant increase in response times (<10% impact)
5. **Agent Behavior**: Improved decision consistency and strategic reasoning

## Files to Modify

### New Files
- `src/maai/services/enhanced_memory_context_builder.py`

### Existing Files
- `src/maai/services/message_builder_service.py`
- `src/maai/services/conversation_service.py`
- `src/maai/services/experiment_orchestrator.py`
- `src/maai/core/models.py` (if new config models needed)

### Test Files
- `tests/test_enhanced_memory_context_builder.py`
- `tests/test_memory_integration.py`
- Update existing service tests

This plan ensures that agents receive their complete memory state at each turn, positioned right after their bank balance, while maintaining the existing standardized message structure and backward compatibility with current configurations.