# Scientific Hypothesis Testing Plan: Distributive Justice Assessment Changes

## Hypothesis
**"The initial and final assessment of the 4 different principles differs"**

## Revised Scientific Approach

### 1. Understanding the Configuration System
Based on thorough analysis, the system allows independent control of:

**Agent-Level Parameters:**
- Individual `temperature` settings per agent (0.0-2.0)
- Individual `model` per agent (mix of different AI models)
- Individual `personality` per agent (different reasoning approaches)
- Global `global_temperature` (overrides individual settings)

**System-Level Parameters:**
- `memory_strategy`: "full", "recent", "decomposed"
- `consensus.strategy`: "id_match", "threshold", "semantic"  
- `conversation.pattern`: "sequential", "random", "hierarchical"
- `evaluation.randomize_principle_order`: true/false
- `max_rounds`: 2-20
- `num_agents`: Variable agent count

**Available Data for Analysis:**
- `*_comparison.csv`: Before/after ratings with `Initial_Numeric`, `Final_Numeric`, `Rating_Change`
- `*_initial_evaluation.csv`: Pre-deliberation `Satisfaction_Numeric` (1-4 scale)
- `*_evaluation.csv`: Post-deliberation `Satisfaction_Numeric` (1-4 scale)
- `*_complete.json`: Agent memories, conversation patterns, timing data

### 2. Scientific Experimental Design (10 Experiments)

Using **Mixed-Level Factorial Design** with **Maximum Variance Coverage**:

#### Core Design Principles:
1. **Agent Heterogeneity Gradient**: From homogeneous to maximally heterogeneous agents
2. **Temperature Strategy Variation**: Global vs individual temperature controls
3. **Cognitive Architecture Variation**: Different memory and consensus strategies
4. **Communication Pattern Variation**: How agents interact and reach decisions
5. **Scale Variation**: Different group sizes and deliberation lengths

#### Experiment Configurations:

**Experiment 1: Baseline Homogeneous**
- Purpose: Minimal complexity baseline
- Agents: 3 identical agents (same model, personality, temperature)
- Config: All `gpt-4.1-mini`, temp=0.0, default personality, 2 rounds
- Memory: "full", Consensus: "id_match", Conversation: "sequential"

**Experiment 2: Maximum Heterogeneity**
- Purpose: Maximum agent diversity
- Agents: 6 different agents (different models, personalities, temperatures)
- Agent 1: `gpt-4.1`, temp=0.1, economist personality
- Agent 2: `claude-sonnet-4`, temp=0.8, philosopher personality  
- Agent 3: `deepseek-chat`, temp=0.3, pragmatist personality
- Agent 4: `llama-4-maverick`, temp=0.6, sociologist personality
- Agent 5: `grok-3-mini`, temp=0.9, data scientist personality
- Agent 6: `gpt-4.1-nano`, temp=0.2, ethicist personality
- Config: 5 rounds, "decomposed" memory, "semantic" consensus, "random" conversation

**Experiment 3: Global Temperature Control**
- Purpose: Test global temperature override effects
- Agents: 4 agents with different individual temps (0.1, 0.4, 0.7, 1.0)
- Override: `global_temperature: 0.0` (should make all deterministic)
- Models: Mixed (`gpt-4.1`, `claude-sonnet-4`, `deepseek-chat`, `llama-3-70B`)
- Config: 3 rounds, "recent" memory, "threshold" consensus (0.75)

**Experiment 4: Memory Strategy Focus**
- Purpose: Test decomposed memory impact
- Agents: 5 agents, varied models but consistent personalities
- Config: "decomposed" memory, 4 rounds, "hierarchical" conversation
- Models: All different, consistent economist personalities, temp=0.3

**Experiment 5: Conversation Pattern Analysis**
- Purpose: Test random vs sequential communication
- Agents: 3 agents, identical setup to Exp 1 except conversation
- Config: "random" conversation pattern, randomize_initial_order=true
- Memory: "full", 4 rounds, varied temperatures (0.2, 0.5, 0.8)

**Experiment 6: Consensus Strategy Analysis**
- Purpose: Test semantic consensus detection
- Agents: 4 agents, mixed models, similar personalities
- Config: "semantic" consensus, "sequential" conversation, 3 rounds
- Memory: "recent" (window=2), individual temps (0.1, 0.3, 0.7, 0.9)

**Experiment 7: Scale and Duration Test**
- Purpose: Test extended deliberation with more agents
- Agents: 6 agents, alternating models (3x gpt-4.1-mini, 3x deepseek-reasoner)
- Config: 8 rounds, varied personalities, "full" memory, temp=0.4 global

**Experiment 8: Mixed Temperature Strategy**
- Purpose: Test individual vs global temperature interaction
- Agents: 5 agents with extreme individual temperatures (0.0, 0.25, 0.5, 0.75, 1.0)
- Config: No global override, 3 rounds, mixed models, "decomposed" memory

**Experiment 9: Evaluation Order Analysis**
- Purpose: Test principle order randomization effects
- Agents: 3 agents, identical to Exp 1 setup
- Config: randomize_principle_order=true, 2 rounds
- Additional: Compare to Exp 1 to isolate order effects

**Experiment 10: Threshold Consensus Analysis**
- Purpose: Test non-unanimous consensus
- Agents: 6 agents, decision_rule="majority", "threshold" consensus (0.67)
- Config: Mixed models/personalities, 4 rounds, "recent" memory

### 3. Statistical Analysis Plan

#### Primary Hypothesis Tests:
1. **Overall Change Test**: Paired t-test on `Rating_Change` across all experiments
2. **Individual Principle Tests**: Separate analysis for each of 4 principles
3. **Effect Size Calculation**: Cohen's d for magnitude assessment

#### Secondary Analyses:
1. **Configuration Impact Analysis**:
   - Memory strategy effects on rating stability
   - Temperature variation impact on consensus time
   - Agent heterogeneity effects on deliberation quality
   - Conversation pattern impact on outcome variance

2. **Agent-Level Analysis**:
   - Individual agent behavior patterns using memory data
   - Model-specific response patterns
   - Personality impact on principle preferences

3. **Process Analysis**:
   - Rounds to consensus vs configuration complexity
   - Speaking pattern analysis from conversation data
   - Memory evolution analysis using complete JSON data

#### Advanced Analyses:
1. **Multi-level Modeling**: Agent nested within experiment
2. **Time Series Analysis**: Rating evolution across rounds
3. **Text Analysis**: Reasoning pattern analysis from memory data
4. **Network Analysis**: Agent interaction patterns

### 4. Data Utilization Strategy

#### Primary Data Sources:
- `*_comparison.csv`: `Rating_Change` for hypothesis testing
- `*_initial_evaluation.csv` & `*_evaluation.csv`: Raw rating data
- `*_complete.json`: Memory evolution, timing, agent behavior

#### Data Processing Pipeline:
1. **Load comparison CSV files**: Extract before/after ratings
2. **Parse complete JSON files**: Extract agent memories, timing, conversation patterns
3. **Create multi-level dataset**: Experiment -> Agent -> Principle structure
4. **Calculate derived variables**: Change magnitudes, consensus efficiency, etc.

### 5. Variance Maximization Rationale

This design maximizes variance by:
1. **Agent Configuration Spectrum**: From identical to maximally diverse agents
2. **Temperature Strategy Coverage**: Global override vs individual control
3. **Cognitive Architecture Variation**: All three memory strategies tested
4. **Communication Complexity**: From simple sequential to complex random patterns
5. **Decision Mechanisms**: Multiple consensus strategies and thresholds
6. **Scale Variation**: 3-6 agents, 2-8 rounds
7. **Control Conditions**: Specific comparisons to isolate effects

### 6. Expected Outcomes

#### Strong Evidence for Hypothesis:
- Significant overall change in ratings post-deliberation
- Consistent direction of change across configurations
- Effect sizes > 0.5 (medium to large effects)

#### Configuration-Specific Predictions:
- **Decomposed memory**: Larger rating changes due to better reflection
- **Heterogeneous agents**: More diverse initial ratings, larger changes
- **Random conversation**: Potentially larger variance in outcomes
- **Extended deliberation**: Potential stabilization of ratings

### 7. Implementation Notes

#### Configuration Generation:
- Use proper YAML structure with individual agent arrays
- Implement service-level configurations properly
- Ensure all parameters are independently controlled

#### Data Analysis:
- Use actual CSV column names (`Initial_Numeric`, `Final_Numeric`, `Rating_Change`)
- Leverage complete JSON for rich behavioral analysis
- Implement proper multi-level statistical models

#### Quality Control:
- Validate each configuration before execution
- Monitor execution success and adjust failed experiments
- Implement proper error handling and retry logic

This design provides a scientifically rigorous test of the hypothesis while maximizing our understanding of the factors that influence deliberation outcomes in AI agent systems.