# Public History Enhancement Plan

## Overview

This plan outlines the implementation of a two-mode public history system for the multi-agent deliberation framework. The enhancement will provide researchers with flexibility to choose between comprehensive historical context and concise summarized context.

## Current System Analysis

### Current Public History Behavior
- **Scope**: Only current round speakers (very limited)
- **Location**: `ConversationService._build_public_context()` 
- **Format**: Simple list of current round messages
- **Limitations**: No historical context, agents lose track of previous arguments

### Current Memory System
- **Scope**: Last 10 messages from all previous rounds + current round
- **Location**: `MemoryService._build_memory_context()`
- **Strategies**: Full, recent, decomposed
- **Issue**: Private memory vs. public history are separate systems

## Proposed Enhancement

### Mode 1: Full Public History
- **Description**: Include all public messages from all previous rounds
- **Format**: Chronological list of all agent messages across all rounds
- **Use Case**: Experiments requiring complete transparency and context
- **Performance**: Higher token usage, more comprehensive context

### Mode 2: Summarized Public History
- **Description**: AI-generated summaries of each completed round
- **Format**: Structured summaries created by helper agent
- **Use Case**: Long experiments, token optimization, focused context
- **Performance**: Lower token usage, condensed key information

## Implementation Plan

### Phase 1: Core Architecture Changes

#### 1.1 Configuration System Updates
**File**: `src/maai/core/models.py`
- Add `PublicHistoryMode` enum with values: `FULL`, `SUMMARIZED`
- Add `public_history_mode` field to `ExperimentConfig`
- Add `summary_agent_model` configuration option (default: "gpt-4.1-mini")

#### 1.2 Public History Service Creation
**New File**: `src/maai/services/public_history_service.py`
- Create `PublicHistoryService` class
- Implement `build_full_public_history()` method
- Implement `build_summarized_public_history()` method
- Handle mode switching logic

#### 1.3 Helper Agent Implementation
**New File**: `src/maai/agents/summary_agent.py`
- Create `SummaryAgent` class extending base agent
- Specialized prompts for round summarization
- Lightweight agent focused on historical synthesis
- Output format: structured summaries with key decisions and arguments

### Phase 2: Integration Points

#### 2.1 ConversationService Updates
**File**: `src/maai/services/conversation_service.py`
- Modify `_build_public_context()` to delegate to `PublicHistoryService`
- Remove current limited public history logic
- Add integration points for summary generation

#### 2.2 DeliberationManager Updates
**File**: `src/maai/core/deliberation_manager.py`
- Add summary generation trigger at round completion
- Integrate `PublicHistoryService` initialization
- Handle summary agent lifecycle

#### 2.3 Experiment Orchestrator Updates
**File**: `src/maai/services/experiment_orchestrator.py`
- Initialize `PublicHistoryService` with configuration
- Pass public history mode to conversation service
- Handle summary agent creation and management

### Phase 3: Summary Agent Design

#### 3.1 Summary Agent Prompts
**Purpose**: Create concise, structured summaries of round discussions

**Prompt Template**:
```
You are a summary agent for a multi-agent deliberation experiment about distributive justice principles.

ROUND {round_number} SUMMARY TASK:
Review the complete discussion below and create a structured summary.

DISCUSSION:
{full_round_messages}

REQUIRED OUTPUT FORMAT:
## Round {round_number} Summary

### Key Arguments Presented:
- Agent_X: [main argument/position]
- Agent_Y: [main argument/position]

### Principle Preferences:
- Principle 1: [agents supporting, key reasons]
- Principle 2: [agents supporting, key reasons]
- Principle 3: [agents supporting, key reasons]
- Principle 4: [agents supporting, key reasons]

### Consensus Status:
- Current agreement level: [none/partial/unanimous]
- Main disagreement points: [if any]

### Round Outcome:
- Principle choices made: [list]
- Key shifts in position: [if any]
- Next round implications: [strategic considerations]

Keep summary concise but comprehensive. Focus on decision-relevant information.
```

#### 3.2 Summary Storage Strategy
**Data Structure**:
```python
@dataclass
class RoundSummary:
    round_number: int
    summary_text: str
    key_arguments: Dict[str, str]  # agent_name -> main_argument
    principle_preferences: Dict[str, List[str]]  # principle -> supporting_agents
    consensus_status: str
    timestamp: datetime
    summary_agent_model: str
```

### Phase 4: Data Flow Architecture

#### 4.1 Full History Mode Flow
1. Agent requests public context
2. `PublicHistoryService.build_full_public_history()`
3. Retrieve all messages from all previous rounds
4. Format chronologically with round markers
5. Return complete public history

#### 4.2 Summarized History Mode Flow
1. **Round Completion**: Trigger summary generation
2. **Summary Agent**: Process full round discussion
3. **Summary Storage**: Store structured summary
4. **Next Round**: Agent requests public context
5. **Summary Retrieval**: Load all previous round summaries
6. **Format Output**: Present summarized public history

### Phase 5: Configuration Integration

#### 5.1 YAML Configuration Schema
```yaml
experiment_id: enhanced_public_history_test
public_history_mode: "SUMMARIZED"  # or "FULL"
summary_agent:
  model: "gpt-4.1-mini"
  temperature: 0.1
  max_tokens: 1000

experiment:
  max_rounds: 10
  # ... existing config
```

#### 5.2 ProbabilisticConfigGenerator Updates
- Add `public_history_mode_probabilities` parameter
- Add `summary_agent_model_probabilities` parameter
- Include in configuration generation logic

### Phase 6: Testing Strategy

#### 6.1 Unit Tests
- `TestPublicHistoryService`: Test both modes
- `TestSummaryAgent`: Test summary generation quality
- `TestConfigurationIntegration`: Test config loading

#### 6.2 Integration Tests
- **Full History Mode**: Verify complete context availability
- **Summarized Mode**: Verify summary quality and consistency
- **Performance Testing**: Compare token usage between modes
- **Long Experiment Testing**: Multi-round summary accumulation

#### 6.3 A/B Testing Framework
- Run identical experiments with both modes
- Compare decision quality and consensus achievement
- Measure performance differences
- Analyze summary accuracy vs. full context

### Phase 7: Performance Considerations

#### 7.1 Token Usage Analysis
- **Full History**: Linear growth with rounds (O(n))
- **Summarized**: Logarithmic growth with fixed summary size (O(log n))
- **Break-even Point**: Calculate when summarized becomes beneficial

#### 7.2 Caching Strategy
- Cache generated summaries to avoid regeneration
- Implement summary validation and refresh logic
- Consider summary versioning for different summary agent models

#### 7.3 Memory Management
- Implement summary storage limits
- Add summary compression for very long experiments
- Consider summary hierarchies (round summaries → phase summaries)

### Phase 8: Research Applications

#### 8.1 Comparative Studies
- **Context Dependency**: How does history mode affect decision quality?
- **Consensus Speed**: Which mode leads to faster agreement?
- **Argument Quality**: Full context vs. summarized context effects

#### 8.2 Experiment Design Recommendations
- **Short Experiments (≤5 rounds)**: Use FULL mode
- **Long Experiments (>5 rounds)**: Use SUMMARIZED mode
- **Token-Limited Scenarios**: Use SUMMARIZED mode
- **Research Questions**: Choose mode based on context dependency requirements

### Phase 9: Implementation Timeline

#### Week 1-2: Foundation
- Core architecture changes
- Configuration system updates
- Basic public history service

#### Week 3-4: Summary Agent
- Summary agent implementation
- Prompt engineering and testing
- Integration with deliberation flow

#### Week 5-6: Integration
- Full integration with existing services
- Comprehensive testing
- Performance optimization

#### Week 7-8: Validation
- A/B testing framework
- Research validation studies
- Documentation and examples

### Phase 10: Future Enhancements

#### 10.1 Advanced Summary Strategies
- **Hierarchical Summaries**: Round → Phase → Experiment summaries
- **Adaptive Summaries**: Context-aware summary detail levels
- **Multi-Agent Summaries**: Different agents create different summary perspectives

#### 10.2 Dynamic Mode Switching
- **Auto-Detection**: Switch modes based on experiment length
- **Runtime Configuration**: Allow mode changes during experiment
- **Hybrid Approaches**: Combine full recent history with older summaries

#### 10.3 Research Integration
- **Summary Quality Metrics**: Automated evaluation of summary accuracy
- **Context Effectiveness**: Measure decision quality correlation with history mode
- **Cognitive Load Analysis**: Study agent performance with different history modes

## Risk Assessment

### Technical Risks
- **Summary Quality**: Poor summaries could mislead agents
- **Performance Impact**: Summary generation adds computational overhead
- **Integration Complexity**: Multiple service coordination challenges

### Mitigation Strategies
- **Summary Validation**: Implement quality checks and human review options
- **Caching**: Reduce computational overhead through intelligent caching
- **Gradual Rollout**: Implement with extensive testing and fallback options

### Research Risks
- **Context Dependency**: May affect experimental validity
- **Comparison Challenges**: Different modes may not be directly comparable
- **Bias Introduction**: Summary agent may introduce systematic biases

## Success Metrics

### Technical Success
- ✅ Both modes implemented and functional
- ✅ Performance improvement in token usage (summarized mode)
- ✅ No degradation in system reliability
- ✅ Comprehensive test coverage

### Research Success
- ✅ Maintained decision quality across both modes
- ✅ Clear performance/quality tradeoff analysis
- ✅ Validated use cases for each mode
- ✅ Research community adoption

## Conclusion

This enhancement will provide researchers with powerful flexibility to optimize the balance between comprehensive context and computational efficiency. The two-mode system addresses different experimental needs while maintaining the core deliberation quality that makes the framework valuable for distributive justice research.

The implementation plan prioritizes robustness and research validity while introducing innovative AI-assisted summarization techniques that could benefit the broader multi-agent research community.