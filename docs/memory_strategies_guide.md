# Memory Strategies Guide

**Multi-Agent Distributive Justice Experiment Framework**

---

## Overview

The memory system is a crucial component that determines how agents remember and process information from previous rounds of deliberation. Different memory strategies can significantly impact the quality of agent reasoning, strategic development, and ultimately the patterns of consensus formation.

This document provides a comprehensive comparison of all available memory strategies and guidance on when to use each one.

---

## Memory System Architecture

### Core Concepts

**Memory Entries**: Each agent maintains private memories containing:
- **Situation Assessment**: Agent's understanding of the deliberation state
- **Other Agents Analysis**: Observations about other agents' positions and behavior
- **Strategy Update**: Specific plan for the next round

**Memory Generation**: Occurs before each agent speaks, using LLM prompts to analyze:
- Recent conversation transcript
- Agent's previous memories (filtered by strategy)
- Current round context

**Memory Usage**: Memories inform agent decision-making and strategic planning in subsequent rounds.

---

## Available Memory Strategies

### 1. Full Memory Strategy (`"full"`)

**Description**: Include all previous memory entries without any filtering.

**How It Works**:
- Agents receive complete history of all their previous memories
- No limit on the number of memory entries included
- Uses all available context from the beginning of the experiment

**Memory Generation Process**:
```
Single comprehensive prompt asking agent to:
1. Assess current deliberation state
2. Analyze all other agents' positions and motivations  
3. Update strategy based on complete history
```

**Advantages**:
- ✅ Complete context preservation
- ✅ No information loss
- ✅ Agents can reference any previous insight
- ✅ Consistent with how humans might remember everything

**Disadvantages**:
- ❌ Context window limitations in longer experiments (10+ rounds)
- ❌ Information overload can reduce decision quality
- ❌ Slower processing due to large context
- ❌ May reinforce early biases or incorrect assessments

**Best Use Cases**:
- Short experiments (≤5 rounds)
- Research studying complete memory retention effects
- When you want maximum information availability
- Baseline comparisons with other strategies

**Performance Impact**:
- **API Calls**: 1 per agent per round
- **Token Usage**: High (scales linearly with experiment length)
- **Quality**: Can suffer from cognitive overload in longer experiments

---

### 2. Recent Memory Strategy (`"recent"`)

**Description**: Include only the most recent N memory entries (default: 5).

**How It Works**:
- Agents only see their last N memory entries
- Older memories are discarded from context
- Focus on immediate recent experience

**Memory Generation Process**:
```
Single prompt with limited memory context:
1. Assess current state using recent memories only
2. Analyze other agents based on recent observations
3. Update strategy based on recent trends
```

**Advantages**:
- ✅ Consistent context size regardless of experiment length
- ✅ Focus on most relevant recent information
- ✅ Reduces cognitive overload
- ✅ Adapts quickly to changing dynamics

**Disadvantages**:
- ❌ Loss of potentially important early insights
- ❌ May miss long-term patterns or commitments
- ❌ Can lead to inconsistent strategy evolution
- ❌ Forgets previous successful approaches

**Best Use Cases**:
- Long experiments (10+ rounds)
- Dynamic situations where recent events matter most
- When you want to study adaptability over consistency
- Resource-constrained scenarios

**Configuration**:
```python
RecentMemoryStrategy(max_entries=5)  # Customizable limit
```

**Performance Impact**:
- **API Calls**: 1 per agent per round
- **Token Usage**: Constant (doesn't grow with experiment length)
- **Quality**: Good for recent context, may miss important history

---

### 3. Decomposed Memory Strategy (`"decomposed"`) ⭐ **NEW**

**Description**: Break memory generation into three focused, sequential micro-prompts to improve quality and reduce cognitive overload.

**How It Works**:
- **Step 1**: Generate factual recap of recent events
- **Step 2**: Analyze ONE specific agent's behavior in detail
- **Step 3**: Develop ONE concrete strategic action

**Memory Generation Process**:
```
Step 1 - Factual Recap (Objective):
- "What actually happened in recent conversation?"
- Focus on facts: who spoke, what choices, key topics
- 2-3 sentences, no interpretations

Step 2 - Agent Analysis (Focused):
- "Focus ONLY on [selected agent]'s behavior"  
- Specific observations about one agent
- Evidence-based analysis, avoid assumptions

Step 3 - Strategic Action (Concrete):
- "What is ONE specific thing you could do next round?"
- Actionable strategy, not general plans
- Target specific agent or concern
```

**Agent Selection Logic**:
- Targets most recent speaker who isn't the current agent
- Ensures focused analysis rather than scattered observations
- Adapts to conversation dynamics

**Advantages**:
- ✅ **Higher Quality**: Focused prompts produce specific, actionable insights
- ✅ **Reduced Cognitive Overload**: Each step has single clear focus
- ✅ **More Strategic**: Concrete action plans vs. vague intentions
- ✅ **Evidence-Based**: Factual foundation reduces hallucinations
- ✅ **Scalable**: Quality doesn't degrade with experiment length

**Disadvantages**:
- ❌ **3x API Calls**: More expensive than other strategies
- ❌ **Sequential Processing**: Takes longer to complete
- ❌ **Less Comprehensive**: Focuses on one agent at a time
- ❌ **Complexity**: More moving parts than simple strategies

**Best Use Cases**:
- **Research Priority**: When memory quality is crucial for research validity
- **Cognitive Studies**: Studying realistic agent reasoning patterns
- **Strategic Analysis**: When you need detailed strategic evolution data
- **Quality Over Speed**: When cost is less important than insight quality

**Configuration**:
```yaml
memory_strategy: "decomposed"
```

**Performance Impact**:
- **API Calls**: 3 per agent per round (3x increase)
- **Token Usage**: Lower per call (3 short prompts vs. 1 long prompt)
- **Quality**: Significantly higher specificity and actionability
- **Total Time**: Longer due to sequential processing

---

## Strategy Comparison Matrix

| Strategy | API Calls | Context Growth | Memory Quality | Cognitive Load | Best Use Case |
|----------|-----------|---------------|----------------|----------------|---------------|
| **Full** | 1x | High | Good→Poor | High | Short experiments (≤5 rounds) |
| **Recent** | 1x | Constant | Moderate | Low | Long experiments (10+ rounds) |
| **Decomposed** | 3x | Low | High | Low | Quality-focused research |

---

## Research Implications

### Memory Quality Impact on Consensus

Different memory strategies can significantly affect experimental outcomes:

**Full Memory**:
- May show more consistent agent behavior
- Could lead to entrenchment in positions
- Better for studying long-term commitment effects

**Recent Memory**:
- More adaptive agent behavior
- Faster consensus changes
- Better for studying flexibility and responsiveness

**Decomposed Memory**:
- More realistic reasoning patterns
- Higher quality strategic development
- Better for studying sophisticated negotiation dynamics

### Recommended A/B Testing

For robust research, consider comparing:

1. **Baseline vs. Quality**: `full` vs. `decomposed`
2. **Memory Scope**: `full` vs. `recent`
3. **Quality vs. Cost**: `decomposed` vs. `recent`

---

## Configuration Examples

### Basic Strategy Selection
```yaml
# Simple strategy change
memory_strategy: "decomposed"
```

### Research Comparison Setup
```yaml
# Experiment A - Baseline
experiment_id: "memory_comparison_full"
memory_strategy: "full"
# ... agents configuration

# Experiment B - Quality Focus  
experiment_id: "memory_comparison_decomposed"
memory_strategy: "decomposed"
# ... same agents configuration
```

### Advanced Configuration with Different Models
```yaml
experiment_id: "advanced_memory_test"
memory_strategy: "decomposed"

agents:
  - name: "Agent_1"
    model: "gpt-4.1"  # Powerful model for quality
    personality: "You are a careful analyst focused on evidence-based reasoning."
  
  - name: "Agent_2"  
    model: "gpt-4.1-mini"  # Efficient model
    personality: "You are a pragmatic decision-maker who values concrete outcomes."
```

---

## Performance Guidelines

### Cost Optimization

**For Budget-Conscious Research**:
```yaml
memory_strategy: "recent"  # 1x cost, good quality
```

**For Quality Research**:
```yaml
memory_strategy: "decomposed"  # 3x cost, best quality
```

**For Long Experiments**:
```yaml
memory_strategy: "recent"  # Constant cost, good for long experiments
```

### Model Selection Impact

The choice of memory strategy interacts with model selection:

**GPT-4.1 + Decomposed**: Best quality, highest cost
**GPT-4.1-mini + Decomposed**: Good quality, medium cost  
**GPT-4.1-nano + Recent**: Basic quality, lowest cost

---

## Implementation Notes

### Adding Custom Memory Strategies

The memory system uses a strategy pattern that makes it easy to add new approaches:

```python
class CustomMemoryStrategy(MemoryStrategy):
    def should_include_memory(self, memory_entry, current_round):
        # Custom filtering logic
        return your_logic_here
    
    def get_memory_context_limit(self):
        return your_limit
    
    async def generate_memory_entry(self, agent, round_number, speaking_position, transcript, memory_context):
        # Custom memory generation
        return custom_memory_entry
```

### Future Enhancements

Potential memory strategy improvements:
- **Adaptive Strategy**: Adjusts approach based on round complexity
- **Semantic Strategy**: Uses embedding similarity for relevant memory selection  
- **Hybrid Strategy**: Combines multiple approaches
- **Importance-Weighted**: Prioritizes memories by impact on decisions

---

## Troubleshooting

### Common Issues

**Memory Context Too Large**:
- Solution: Switch from `full` to `selective` or `recent`
- Check: Agent count × rounds × memory size

**Generic Memory Content**:
- Solution: Switch from `full` to `decomposed`
- Check: Prompt complexity vs. model capabilities  

**Inconsistent Agent Behavior**:
- Solution: Switch from `recent` to `full`
- Check: Is important context being lost?

**High API Costs**:
- Solution: Switch from `decomposed` to `recent`
- Check: Quality requirements vs. budget constraints

### Debugging Memory Content

To analyze memory quality:
```python
# Check memory content in results
results = await run_single_experiment(config)
for agent_memory in results.agent_memories:
    for memory in agent_memory.memory_entries:
        print(f"Round {memory.round_number}:")
        print(f"  Situation: {memory.situation_assessment}")
        print(f"  Analysis: {memory.other_agents_analysis}")
        print(f"  Strategy: {memory.strategy_update}")
```

---

## Conclusion

Memory strategy selection significantly impacts both the computational cost and research value of experiments. The new **decomposed strategy** offers the highest quality agent reasoning at increased computational cost, while traditional strategies provide efficient alternatives for different research needs.

Choose your memory strategy based on:
- **Research Goals**: Quality vs. efficiency
- **Budget Constraints**: API call costs  
- **Experiment Length**: Short (full) vs. long (recent) deliberations
- **Analysis Needs**: Strategic detail (decomposed) vs. general patterns (full/recent)

**Quick Selection Guide**:
- **`"full"`**: Short experiments ≤5 rounds, complete context needed
- **`"recent"`**: Long experiments 10+ rounds, adaptive behavior focus
- **`"decomposed"`**: Quality-focused research, realistic reasoning patterns

The decomposed strategy represents a significant advancement in agent memory quality and opens new possibilities for studying sophisticated multi-agent negotiation dynamics.