# Decomposed Memory Strategy Implementation Plan

**Date**: January 2025  
**Feature**: Add new "Decomposed" memory strategy as fourth option alongside existing strategies  
**Priority**: HIGH - Addresses core memory quality issues  
**Estimated Effort**: 1-2 weeks  

---

## Problem Statement

**Current Issue**: Memory update prompts are cognitively overwhelming, asking agents to simultaneously assess complex multi-round negotiations, psychoanalyze multiple agents, and develop strategic responses. This leads to generic, low-quality responses that reduce experiment realism and research value.

**Evidence**: Current single prompt approach often produces responses like "People disagree, I'll try to compromise" instead of specific, actionable insights.

## Solution Overview

**Core Approach**: Create a new `DecomposedMemoryStrategy` that joins the existing strategy options (Full, Recent, Selective) as a fourth memory management approach.

**Integration Point**: Add as new strategy class that implements the existing `MemoryStrategy` interface, requiring minimal changes to the current system.

**Key Benefits**:
- Higher quality, more specific memory content
- Reduced cognitive load per prompt step
- Better agent reasoning and strategic thinking
- Maintains full compatibility with existing research

**Design Principle**: Break complex memory generation into sequential focused steps while fitting cleanly into the existing memory service architecture.

---

## Technical Design

### 1. **Existing Strategy Pattern Integration**

**Current Memory Strategies**:
- `FullMemoryStrategy`: Include all previous memory entries
- `RecentMemoryStrategy`: Include only the most recent N entries  
- `SelectiveMemoryStrategy`: Include only memory from the last N rounds

**New Addition**:
- `DecomposedMemoryStrategy`: Generate memory using focused, sequential prompts

### 2. **DecomposedMemoryStrategy Implementation**

**Strategy Class**: Implement the existing `MemoryStrategy` interface without changes to the base system.

**Core Approach**: Replace the single complex memory generation call with three focused sequential steps:

1. **Factual Recap**: "What actually happened?" (objective events only)
2. **Agent Analysis**: "Focus on ONE agent's behavior" (specific observations)  
3. **Strategic Action**: "What's ONE concrete thing you could do next?" (actionable strategy)

**Integration**: Uses existing `MemoryEntry` structure by mapping decomposed results to current fields:
- Step 1 result → `situation_assessment`
- Step 2 result → `other_agents_analysis` 
- Step 3 result → `strategy_update`

**Sequential Execution**: Each step builds on the previous:
- Step 1: Generate factual recap using recent transcript
- Step 2: Generate agent analysis using factual recap as context
- Step 3: Generate strategic action using both previous steps as context

### 3. **Memory Service Integration**

**No Changes to Core MemoryService**: The new strategy plugs directly into existing memory service architecture.

**Strategy Selection**: Add "decomposed" as fourth option in strategy selection logic alongside existing "full", "recent", "selective" options.

**Memory Entry Handling**: All existing memory entry processing, storage, and retrieval works unchanged since the decomposed strategy produces standard `MemoryEntry` objects.

### 4. **Context Building Compatibility**

**Existing Context Building**: Current `_build_memory_context()` method works unchanged since decomposed strategy outputs to same `MemoryEntry` fields.

**Optional Enhancement**: Could add metadata field to track generation method for research analysis, but not required for functionality.

---

## Three-Step Process Details

### **Step 1: Factual Recap**
**Purpose**: Establish objective foundation without interpretation
**Prompt Focus**: "What factual events occurred in the recent conversation?"
**Expected Output**: Brief, concrete summary of who said what and chose what
**Example**: "Agent_1 spoke first, chose principle 1, mentioned veil of ignorance concerns. Agent_3 spoke second, switched from principle 2 to principle 3, cited political necessity."

### **Step 2: Agent Analysis** 
**Purpose**: Focus analytical attention on specific behavioral observations
**Prompt Focus**: "Focus only on [selected agent]'s behavior and statements"
**Agent Selection Logic**: Choose agent who had most significant recent activity (spoke, changed position, raised new concerns)
**Expected Output**: Specific observations about one agent's consistency, concerns, and apparent motivations
**Example**: "Agent_3 shows strategic flexibility - switched positions when faced with opposition. Their use of 'political necessity' suggests they're calculating group dynamics rather than personal conviction."

### **Step 3: Strategic Action**
**Purpose**: Generate specific, actionable next step based on analysis
**Prompt Focus**: "Given what you observed, what's ONE specific thing you could do next round?"
**Expected Output**: Concrete action plan targeting specific agent or concern
**Example**: "Focus on Agent_3's efficiency concerns. Propose principle 3 with wealth cap mechanism that preserves incentives while addressing Agent_1's inequality worries."

---

## System-Wide Impact Analysis

### **1. Performance Impact**

**API Calls**:
- **Current**: 1 LLM call per agent per round for memory
- **New Strategy**: 3 LLM calls per agent per round for memory  
- **Impact**: 3x increase in memory-related API calls (but significantly shorter, focused prompts)

**Token Efficiency**:
- Shorter individual prompts reduce token waste
- Focused prompts likely to produce higher quality responses
- Sequential building reduces need for massive context windows

### **2. Data Export Impact**

**Export Compatibility**: No changes needed to existing data export functionality since decomposed strategy uses standard `MemoryEntry` structure.

**Research Value**: Higher quality memory content provides better data for post-experiment analysis of agent reasoning patterns.

### **3. Research Impact**

**Enhanced Research Questions**:
- Do decomposed memories lead to different consensus patterns?
- How does memory structure affect strategic sophistication?
- What's the relationship between memory quality and deliberation outcomes?

**A/B Testing Capability**:
- Run identical experiments with different memory strategies
- Compare consensus speed, quality, and agent behavior patterns
- Analyze difference in strategic sophistication between approaches

---

## Implementation Plan

### **Phase 1: Core Implementation (Week 1)**

**Day 1-2: Strategy Class Implementation**
- Create `DecomposedMemoryStrategy` class implementing existing `MemoryStrategy` interface
- Implement three-step sequential prompt generation methods
- Add agent selection logic for focused analysis step

**Day 3-4: Integration Points**
- Add "decomposed" option to memory strategy selection in `MemoryService`
- Update configuration loading to support new strategy option
- Test integration with existing memory service workflow

**Day 5-7: Configuration & Testing**
- Add YAML configuration support for decomposed strategy
- Create comprehensive unit tests for new strategy
- Test end-to-end experiment execution with decomposed memory

### **Phase 2: Refinement & Documentation (Week 2)**

**Day 8-10: Optimization & Quality**
- Refine prompt templates based on initial testing
- Optimize sequential execution flow and error handling
- Add fallback mechanisms if any step fails

**Day 11-12: Research Tools**
- Create comparative analysis tools for different memory strategies
- Add optional metadata tracking for research purposes
- Test A/B experiment configurations

**Day 13-14: Documentation & Validation**
- Update system documentation with new strategy option
- Create usage examples and configuration guides
- Validate with real experiment scenarios

---

## Configuration Options

### **YAML Configuration Example**
```yaml
# configs/decomposed_memory_test.yaml
experiment_id: decomposed_memory_test
experiment:
  max_rounds: 5

# Memory strategy configuration  
memory_strategy: "decomposed"

agents:
  - name: "Agent_1"
    model: "gpt-4.1-mini"
  - name: "Agent_2" 
    model: "gpt-4.1-mini"
  - name: "Agent_3"
    model: "gpt-4.1-mini"
```

### **Strategy Selection Options**
Available memory strategies:
- `"full"` - Include all previous memory entries (existing)
- `"recent"` - Include only most recent N entries (existing)  
- `"selective"` - Include only last N rounds (existing)
- `"decomposed"` - Use focused sequential prompts (new)

---

## Testing Strategy

**Unit Tests**:
- Test `DecomposedMemoryStrategy` class implementation
- Verify three-step sequential prompt generation
- Test agent selection logic for focused analysis
- Validate integration with existing `MemoryStrategy` interface

**Integration Tests**:
- Run complete experiments using decomposed memory strategy
- Test memory context building with decomposed entries
- Verify existing data export functionality works unchanged
- Test switching between different memory strategies

**Performance Tests**:
- Measure impact of 3x API calls on total experiment time
- Compare memory quality between strategies
- Test system reliability with new strategy option

**Quality Tests**:
- Compare specificity of memory content between strategies
- Measure actionability of strategic outputs
- Analyze correlation between memory quality and consensus outcomes

---

## Migration & Rollout

### **Rollout Strategy**
1. **Additive**: New strategy added alongside existing options, no changes to defaults
2. **Opt-in**: Decomposed strategy available through configuration selection
3. **Compatible**: Uses existing memory infrastructure, no migration needed
4. **Experimental**: Enables controlled comparison studies between memory approaches

### **Research Transition**
- Existing experiments continue working unchanged
- New experiments can opt into decomposed memory
- Comparative studies can run identical setups with different memory strategies
- No breaking changes to existing analysis tools or data formats

---

## Success Metrics

### **Quality Metrics**
- **Memory Specificity**: Measure concrete details vs generic statements in memory entries
- **Strategic Actionability**: Measure if strategies contain specific, actionable next steps
- **Agent Analysis Depth**: Measure focus and specificity of agent behavioral assessments

### **Research Metrics**
- **Consensus Quality**: Do better memories lead to more sophisticated consensus formation?
- **Strategic Evolution**: Do agents develop more effective strategies over time?
- **Deliberation Realism**: Do conversations become more realistic and engaging?

### **Performance Metrics**
- **Total Experiment Time**: Impact of 3x memory calls on overall experiment duration
- **Response Quality**: Compare specificity and usefulness of memory content
- **System Reliability**: Error rates and fallback frequency for new strategy

---

## Risk Mitigation

### **Technical Risks**
1. **Performance Impact**: Mitigated by shorter, focused prompts and maintaining sequential execution
2. **Integration Issues**: Mitigated by implementing existing interface without core system changes
3. **Quality Regression**: Mitigated by maintaining existing strategies as options and gradual rollout

### **Research Risks**
1. **Behavior Changes**: Document and study how improved memory affects experimental outcomes
2. **Comparability**: Maintain ability to run identical experiments with different memory strategies
3. **Cost Overhead**: Monitor if additional API calls significantly impact experiment feasibility

---

## Future Extensions

### **Post-Implementation Enhancements**
1. **Adaptive Decomposition**: Adjust number of steps based on round complexity
2. **Alternative Step Configurations**: Different decomposition patterns for different research questions
3. **Hybrid Strategies**: Combine decomposed approach with other memory filtering strategies
4. **Step Customization**: Allow researchers to customize the specific focus of each decomposition step

### **Research Extensions**
1. **Memory Quality Scoring**: Develop automated metrics for memory content quality
2. **Strategy Effectiveness Analysis**: Track which memory strategies lead to better experimental outcomes
3. **Cross-Strategy Comparison Tools**: Build analysis frameworks for comparing different memory approaches

---

## Conclusion

This implementation plan adds decomposed memory as a clean fourth option in the existing strategy framework, enabling researchers to choose the memory approach that best fits their experimental needs while maintaining full system compatibility. The decomposed approach should significantly improve memory quality by breaking complex cognitive tasks into focused, manageable steps, leading to more realistic agent behavior and richer research insights.