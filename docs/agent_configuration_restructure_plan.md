# Agent Configuration Restructure Plan

**Date:** July 11, 2025  
**Purpose:** Restructure YAML configuration to support individual agent specification with per-agent properties

---

## CURRENT PROBLEM

The current YAML structure separates agent properties into different arrays, making it difficult to understand which agent gets which configuration:

```yaml
experiment:
  num_agents: 3
  models: ["gpt-4.1-mini", "gpt-4.1", "gpt-4.1-mini"]

personalities:
  - "You are an economist focused on efficiency"
  - "You are a philosopher concerned with fairness" 
  - "You love to debate just for the sake of it"
```

**Issues:**
- **Implicit Mapping:** Agent 1 gets `models[0]` and `personalities[0]`, but this isn't obvious
- **Error Prone:** Easy to misalign arrays (wrong personality with wrong model)
- **Limited Flexibility:** Can't easily specify different properties per agent
- **Scaling Issues:** Adding new per-agent properties requires new arrays
- **Readability:** Hard to see complete agent configuration at a glance

---

## PROPOSED SOLUTION

### New YAML Structure

```yaml
experiment_id: my_experiment
experiment:
  max_rounds: 5
  decision_rule: unanimity
  timeout_seconds: 300

# New explicit agent configuration
agents:
  - name: "Economist"
    personality: "You are an economist focused on efficiency and optimal resource allocation."
    model: "gpt-4.1"
    
  - name: "Philosopher"
    personality: "You are a philosopher concerned with justice and fairness for all members of society."
    model: "gpt-4.1-mini"
    
  - name: "Debater"
    personality: "You love to debate just for the sake of it, simply take the opposite view of your fellow debaters."
    # model not specified - uses default
    
  - name: "Pragmatist"
    # personality not specified - uses default
    model: "gpt-4.1-nano"
    
  - # completely default agent
    {}

# Defaults for when agent properties aren't specified
defaults:
  personality: "You are an agent tasked to design a future society."
  model: "gpt-4.1-mini"

output:
  directory: experiment_results
  formats: [json, csv, txt]
```

### Key Benefits

1. **Explicit Configuration:** Each agent's complete configuration is clearly visible
2. **Flexible Defaults:** Can specify defaults that apply when properties are missing
3. **Easy Extension:** Can add new per-agent properties without breaking existing configs
4. **Better Validation:** Can validate each agent's configuration individually
5. **Human Readable:** Clear mapping between agent properties
6. **Future Proof:** Easy to add agent-specific timeouts, roles, etc.

---

## IMPLEMENTATION PLAN

### Phase 1: Extend Data Models

#### 1.1 Create New Agent Configuration Model
```python
# src/maai/core/models.py

@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    name: Optional[str] = None
    personality: Optional[str] = None
    model: Optional[str] = None
    # Future: timeout_seconds, role, etc.

@dataclass  
class DefaultConfig:
    """Default values for agent properties."""
    personality: str = "You are an agent tasked to design a future society."
    model: str = "gpt-4.1-mini"

@dataclass
class ExperimentConfig:
    # ... existing fields ...
    agents: Optional[List[AgentConfig]] = None
    defaults: Optional[DefaultConfig] = None
    
    # Keep existing fields for backward compatibility
    num_agents: Optional[int] = None
    models: Optional[List[str]] = None
    personalities: Optional[List[str]] = None
```

#### 1.2 Add Configuration Resolution Logic
```python
def resolve_agent_configurations(config: ExperimentConfig) -> List[AgentConfig]:
    """
    Resolve final agent configurations by merging specified values with defaults.
    Supports both new agent-based format and legacy array-based format.
    """
    pass
```

### Phase 2: Update Configuration Loading

#### 2.1 Support Both Formats
The config loader should detect and handle both formats:

```python
def _detect_config_format(config_data: dict) -> str:
    """Detect whether config uses new 'agents' format or legacy format."""
    if "agents" in config_data:
        return "agents_format"
    elif "personalities" in config_data or "models" in config_data.get("experiment", {}):
        return "legacy_format"
    else:
        return "minimal_format"

def _load_agents_format(config_data: dict) -> Tuple[List[AgentConfig], DefaultConfig]:
    """Load configuration from new agents-based format."""
    pass

def _load_legacy_format(config_data: dict) -> Tuple[List[AgentConfig], DefaultConfig]:
    """Convert legacy format to agent configurations."""
    pass
```

#### 2.2 Enhanced Validation
```python
def _validate_agent_configurations(agents: List[AgentConfig], defaults: DefaultConfig) -> None:
    """Validate agent configurations and apply defaults where needed."""
    # Validate models exist
    # Validate personality strings are non-empty
    # Check for duplicate agent names
    # Ensure all agents have resolved configurations
```

### Phase 3: Backward Compatibility

#### 3.1 Legacy Format Support
Maintain full support for existing YAML files:

```yaml
# This should still work exactly as before
experiment:
  num_agents: 3
  models: ["gpt-4.1-mini", "gpt-4.1", "gpt-4.1-mini"]
personalities:
  - "Economist personality"
  - "Philosopher personality"
  - "Debater personality"
```

#### 3.2 Automatic Migration Tool
```python
def migrate_legacy_config(legacy_path: str, new_path: str) -> None:
    """Convert legacy YAML config to new agents-based format."""
    pass
```

#### 3.3 Hybrid Support
Allow mixing formats temporarily:
```yaml
experiment:
  max_rounds: 5

# Some agents specified explicitly
agents:
  - name: "Custom Agent"
    personality: "Special personality"
    model: "gpt-4.1"

# Fallback to legacy for remaining agents  
num_agents: 5  # Total agents (including the 1 above)
models: ["gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini"]
personalities: ["Default 1", "Default 2", "Default 3", "Default 4"]
```

### Phase 4: Enhanced Features

#### 4.1 Agent Naming and Identification
```python
def generate_agent_names(agents: List[AgentConfig]) -> List[AgentConfig]:
    """Generate human-readable names for agents that don't have them."""
    # Agent_1, Agent_2, etc. or based on personality
```

#### 4.2 Configuration Templates
```yaml
# Template for different experiment types
templates:
  economic_debate:
    agents:
      - name: "Economist"
        personality: "You focus on economic efficiency"
        model: "gpt-4.1"
      - name: "Social_Worker" 
        personality: "You focus on social welfare"
        model: "gpt-4.1"

  philosophical_discussion:
    agents:
      - name: "Utilitarian"
        personality: "You believe in greatest good for greatest number"
      - name: "Deontologist"
        personality: "You believe in moral duties and rules"
```

#### 4.3 Agent Roles and Specialized Behavior
```yaml
agents:
  - name: "Moderator"
    personality: "You help facilitate discussion"
    model: "gpt-4.1"
    role: "moderator"  # Special behavior
    
  - name: "Devil's Advocate"
    personality: "You challenge every proposal"
    role: "challenger"
    
  - name: "Consensus Builder"
    personality: "You try to find common ground"
    role: "mediator"
```

---

## MIGRATION STRATEGY

### Option 1: Gradual Migration (Recommended)

1. **Phase 1:** Implement new format support alongside existing format
2. **Phase 2:** Add migration tools and documentation
3. **Phase 3:** Encourage new format in examples and templates
4. **Phase 4:** Eventually deprecate legacy format (with long notice period)

### Option 2: Immediate Transition

1. Convert all existing configs to new format
2. Update all documentation immediately
3. Higher risk but cleaner codebase

### Option 3: Dual Support Indefinitely

1. Support both formats permanently
2. Lower risk but more complex maintenance

## VALIDATION STRATEGY

### New Validation Rules

```python
class AgentConfigValidator:
    def validate_agent_config(self, agent: AgentConfig, defaults: DefaultConfig) -> List[str]:
        """Return list of validation errors."""
        errors = []
        
        # Personality validation
        personality = agent.personality or defaults.personality
        if not personality or len(personality.strip()) < 10:
            errors.append(f"Agent {agent.name}: Personality too short")
            
        # Model validation  
        model = agent.model or defaults.model
        if model not in SUPPORTED_MODELS:
            errors.append(f"Agent {agent.name}: Unsupported model {model}")
            
        # Name uniqueness
        # ... other validations
        
        return errors
```

### Configuration Validation Flow

```
1. Parse YAML → Raw config dict
2. Detect format (agents vs legacy)
3. Convert to unified AgentConfig list
4. Apply defaults where needed
5. Validate each agent configuration
6. Validate experiment-level settings
7. Create final ExperimentConfig object
```

---

## IMPLEMENTATION CHECKLIST

### Core Implementation
- [ ] Create `AgentConfig` and `DefaultConfig` data models
- [ ] Implement `resolve_agent_configurations()` function
- [ ] Add format detection to config loader
- [ ] Implement new format parsing
- [ ] Maintain legacy format support
- [ ] Add comprehensive validation

### Testing Strategy
- [ ] Unit tests for new data models
- [ ] Unit tests for configuration resolution
- [ ] Integration tests for both formats
- [ ] Validation tests for edge cases
- [ ] Backward compatibility tests

### Documentation Updates
- [ ] Update configuration documentation
- [ ] Create migration guide
- [ ] Update example configurations
- [ ] Add new format examples to README

### Tools and Utilities
- [ ] Configuration migration script
- [ ] Configuration validation CLI tool
- [ ] Configuration template generator
- [ ] Format conversion utilities

---

## EXAMPLE CONFIGURATIONS

### Simple Configuration
```yaml
experiment_id: simple_test
experiment:
  max_rounds: 3

agents:
  - personality: "You are practical and solution-focused"
  - personality: "You are idealistic and principled"  
  - personality: "You are skeptical and analytical"

defaults:
  model: "gpt-4.1-mini"
```

### Complex Configuration
```yaml
experiment_id: complex_debate
experiment:
  max_rounds: 10
  timeout_seconds: 600

agents:
  - name: "Chief Economist"
    personality: "You are a senior economist focused on GDP growth and market efficiency"
    model: "gpt-4.1"
    
  - name: "Social Justice Advocate" 
    personality: "You prioritize equality, human rights, and social welfare"
    model: "gpt-4.1"
    
  - name: "Environmental Scientist"
    personality: "You focus on sustainability and long-term environmental impact"
    model: "gpt-4.1-mini"
    
  - name: "Pragmatic Politician"
    personality: "You focus on what's politically feasible and popular"
    
  - name: "Philosopher"
    personality: "You think about fundamental principles and moral frameworks"
    model: "claude-3.5-sonnet"

defaults:
  model: "gpt-4.1-mini"
  personality: "You are a thoughtful participant in policy discussions"

output:
  directory: complex_results
  formats: [json, csv, txt]
```

### Mixed Research Configuration
```yaml
experiment_id: model_comparison
experiment:
  max_rounds: 5

agents:
  - name: "GPT_Agent_1"
    personality: "You are analytical and data-driven"
    model: "gpt-4.1"
    
  - name: "Claude_Agent_1"  
    personality: "You are analytical and data-driven"
    model: "claude-3.5-sonnet"
    
  - name: "DeepSeek_Agent_1"
    personality: "You are analytical and data-driven" 
    model: "deepseek-r1"
    
  # Test same personality across different models
  - name: "GPT_Agent_2"
    personality: "You prioritize fairness above all else"
    model: "gpt-4.1"
    
  - name: "Claude_Agent_2"
    personality: "You prioritize fairness above all else"
    model: "claude-3.5-sonnet"

defaults:
  model: "gpt-4.1-mini"
```

---

## CONCLUSION

This restructure will significantly improve the flexibility and usability of the MAAI configuration system while maintaining backward compatibility. The explicit agent-based configuration makes experiments easier to design, understand, and maintain.

**Key Success Metrics:**
- Backward compatibility maintained (all existing configs work)
- New configurations are more readable and flexible
- Easy migration path from legacy to new format
- Enhanced validation prevents configuration errors
- Foundation for future per-agent enhancements

**Timeline Estimate:** 2-3 weeks for full implementation including testing and documentation.