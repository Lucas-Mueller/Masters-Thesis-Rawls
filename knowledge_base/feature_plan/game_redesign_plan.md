# Game Logic Redesign Implementation Plan

## Executive Summary

This document outlines the implementation plan to transition from the current Rawls "veil of ignorance" distributive justice experiment to a new game logic focused on individual familiarization with principles, preference ranking, and economic outcomes through income distribution scenarios.

## Current System Analysis

### Current Game Flow
1. **Agent Initialization**: Agents start with "veil of ignorance" context
2. **Initial Likert Evaluation**: 4-point scale rating of all principles before deliberation  
3. **Multi-Round Deliberation**: Agents debate until unanimous agreement or timeout
4. **Consensus Detection**: Validate group agreement on chosen principle
5. **Final Likert Evaluation**: Agents re-rate all principles after deliberation
6. **Data Export**: Results saved in multiple formats

### Current Principles (4 principles)
1. **Maximize the Minimum Income**: Focus on worst-off welfare
2. **Maximize the Average Income**: Focus on total income without distribution consideration
3. **Maximize Average with Floor Constraint**: Hybrid with guaranteed minimum
4. **Maximize Average with Range Constraint**: Hybrid limiting inequality gap

### Current System Strengths to Preserve
- **Service-oriented architecture** with modular components
- **YAML-based configuration system** for experiment parameters
- **Comprehensive logging system** without truncation
- **Multi-provider LLM support** (OpenAI, Claude, DeepSeek, etc.)
- **Parallel execution capabilities** for batch experiments
- **Robust data export system** with multiple formats

## New System Requirements

### Phase 1: Individual Familiarization
1. **Principle Reading**: Agents read the 4 principles with updated definitions
2. **Simple Preference Ranking**: Rank principles 1-4 (Best to Worst)
3. **Certainty Rating**: 5-point scale (Very unsure to Very Sure)
4. **Detailed Example Explanation**: Dynamic income distribution tables
5. **Outcome Mapping**: Show how each principle maps to specific distributions
6. **Repeated Application**: 4 rounds of principle application with economic outcomes

### Phase 2: Group Experiment
1. **Group Discussion**: Multi-agent deliberation on principles
2. **Voting Process**: Secret ballot system
3. **Economic Assignment**: Random assignment to income classes
4. **Payoff Calculation**: 1$ per 10,000$ earned (configurable ratio)

### Key New Features Required
- **Dynamic Income Distribution Tables**: Configurable via YAML
- **Economic Outcome Simulation**: Apply chosen principles to get actual income
- **Bank Account System**: Track agent wealth across rounds
- **Choice Validation**: Ensure valid principle selections (especially for floor/range constraints)
- **Random Assignment System**: Assign agents to income classes post-decision

## Implementation Architecture Changes

### 1. Core Models Updates (`src/maai/core/models.py`)

#### New Models Required
```python
# Income distribution system
class IncomeClass(str, Enum):
    HIGH = "High"
    MEDIUM_HIGH = "Medium high" 
    MEDIUM = "Medium"
    MEDIUM_LOW = "Medium low"
    LOW = "Low"

class IncomeDistribution(BaseModel):
    distribution_id: int
    income_by_class: Dict[IncomeClass, int]  # Dollar amounts

class DistributionSet(BaseModel):
    distributions: List[IncomeDistribution]
    name: str
    description: Optional[str]

# Preference ranking system
class PreferenceRanking(BaseModel):
    agent_id: str
    rankings: List[int]  # [1,2,3,4] representing principle preferences
    certainty_level: CertaintyLevel
    reasoning: str
    timestamp: datetime

class CertaintyLevel(str, Enum):
    VERY_UNSURE = "very_unsure"
    UNSURE = "unsure" 
    NO_OPINION = "no_opinion"
    SURE = "sure"
    VERY_SURE = "very_sure"

# Economic outcome tracking
class EconomicOutcome(BaseModel):
    agent_id: str
    round_number: int
    chosen_principle: int
    assigned_income_class: IncomeClass
    actual_income: int
    payout_amount: float  # Based on payout_ratio
    cumulative_wealth: float

# Enhanced principle choice with constraints
class EnhancedPrincipleChoice(BaseModel):
    principle_id: int
    principle_name: str
    floor_constraint: Optional[int] = None  # For principle 3
    range_constraint: Optional[int] = None  # For principle 4
    reasoning: str
    is_valid: bool = True
    validation_errors: List[str] = []
```

#### Updated Principle Definitions
```python
DISTRIBUTIVE_JUSTICE_PRINCIPLES = {
    1: {
        "name": "MAXIMIZING THE FLOOR INCOME",
        "description": "The most just distribution of income is that which maximizes the floor (or lowest) income in the society. This principle considers only the welfare of the worst-off individual in society. In judging among income distributions, the distribution which ensures the poorest person the highest income is the most just. No person's income can go up unless it increases the income of the people at the very bottom.",
        "short_name": "Floor Income"
    },
    2: {
        "name": "MAXIMIZING THE AVERAGE INCOME", 
        "description": "The most just distribution of income is that which maximizes the average income in the society. For any society maximizing the average income maximizes the total income in the society.",
        "short_name": "Average Income"
    },
    3: {
        "name": "MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT",
        "description": "The most just distribution of income is that which maximizes the average income only after a certain specified minimum income is guaranteed to everyone. Such a principle ensures that the attempt to maximize the average is constrained so as to ensure that individuals \"at the bottom\" receive a specified minimum. To choose this principle one must specify the value of the floor (lowest income).",
        "short_name": "Floor Constraint",
        "requires_parameter": True,
        "parameter_type": "floor_amount"
    },
    4: {
        "name": "MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT", 
        "description": "The most just distribution of income is that which attempts to maximize the average income only after guaranteeing that the difference between the poorest and the richest individuals (i.e., the range of income) in the society is not greater than a specified amount. Such a principle ensures that the attempt to maximize the average does not allow income differences between rich and poor to exceed a specified amount. To choose this principle one must specify the dollar difference between the high and low incomes.",
        "short_name": "Range Constraint",
        "requires_parameter": True,
        "parameter_type": "range_amount"
    }
}
```

### 2. Configuration System Updates (`src/maai/config/manager.py`)

#### New Configuration Schema
```yaml
# Example new configuration structure
experiment_id: "new_game_logic_test"

# Phase 1: Individual familiarization settings
phase1:
  enable_detailed_examples: true
  repeated_applications: 4
  
# Phase 2: Group experiment settings  
phase2:
  enable_secret_ballot: true
  require_unanimous_vote_agreement: true

# Economic simulation settings
economics:
  payout_ratio: 0.0001  # $1 per $10,000 earned
  starting_wealth: 0.0
  
# Income distribution scenarios (configurable)
income_distributions:
  - distribution_id: 1
    name: "Distribution 1"
    income_by_class:
      High: 32000
      Medium_high: 27000
      Medium: 24000
      Medium_low: 13000
      Low: 12000
  - distribution_id: 2  
    name: "Distribution 2"
    income_by_class:
      High: 28000
      Medium_high: 22000
      Medium: 20000
      Medium_low: 17000
      Low: 13000
  # ... additional distributions

# Principle-to-distribution mappings (dynamic)
principle_mappings:
  distribution_set_1:
    maximizing_floor: 4
    maximizing_average: 1
    floor_constraints:
      12000: 1
      13000: 2  
      14000: 3
      15000: 4
    range_constraints:
      20000: 1
      17000: 3
      15000: 2
```

### 3. Service Layer Changes

#### New Services Required

**`src/maai/services/economics_service.py`**
- Manage income distributions and economic outcomes
- Calculate payoffs based on chosen principles and assigned classes
- Track cumulative wealth across rounds
- Apply principle logic to select appropriate distributions

**`src/maai/services/preference_service.py`**  
- Manage preference ranking collection and validation
- Handle certainty level tracking
- Provide ranking comparison utilities

**`src/maai/services/validation_service.py`**
- Validate principle choices (especially constraint parameters)
- Ensure floor/range constraint values are provided when required
- Send error messages for invalid choices

**`src/maai/services/voting_service.py`**
- Implement secret ballot functionality
- Manage voting process and agreement detection
- Handle vote tallying and result determination

#### Updated Services

**`src/maai/services/conversation_service.py`**
- Remove "veil of ignorance" references 
- Update prompts to focus on principle application rather than philosophical debate
- Add support for individual application rounds
- Integrate economic outcome feedback

**`src/maai/services/evaluation_service.py`**
- Replace Likert scale evaluation with preference ranking system
- Add certainty level collection
- Integrate detailed example explanations

### 4. Agent System Updates (`src/maai/agents/enhanced.py`)

#### Agent State Enhancements
```python
class DeliberationAgent(Agent):
    def __init__(self, ...):
        # ... existing initialization
        self.current_wealth: float = 0.0
        self.economic_history: List[EconomicOutcome] = []
        self.preference_rankings: List[PreferenceRanking] = []
        self.current_principle_choice: Optional[EnhancedPrincipleChoice] = None
```

#### New Agent Instructions
- Remove all "veil of ignorance" language
- Focus on principle understanding and application
- Include economic consequences in decision-making
- Add bank account awareness for repeated rounds

### 5. Experiment Flow Redesign (`src/maai/core/deliberation_manager.py`)

#### New Experiment Phases

**Phase 1 Implementation**
1. **Principle Introduction**: Present updated principle definitions
2. **Initial Ranking**: Collect preference rankings with certainty
3. **Detailed Examples**: Show income distribution tables and mappings
4. **Understanding Verification**: (Optional - can be skipped per requirements)
5. **Repeated Application Rounds**: 4 iterations of:
   - Present distribution scenario
   - Agent selects principle (with constraint validation)
   - Apply principle to determine outcome distribution
   - Randomly assign agent to income class
   - Calculate and award payout
   - Update agent's bank account
6. **Final Ranking**: Collect updated preference rankings

**Phase 2 Implementation** 
1. **Group Instructions**: Explain voting process and economic consequences
2. **Group Discussion**: Multi-agent deliberation (similar to current system)
3. **Vote Initiation**: Any agent can call for a vote
4. **Secret Ballot**: Collect private votes from all agents
5. **Vote Resolution**: 
   - If unanimous: Apply chosen principle, assign income classes, calculate payouts
   - If not unanimous: Random assignment to income classes from default distribution
6. **Final Ranking**: Collect post-group preference rankings

### 6. Data Export System Updates (`src/maai/services/experiment_logger.py`)

#### New Data Structures for Export
- **Preference rankings** across all phases
- **Economic outcomes** for each application round
- **Bank account histories** tracking cumulative wealth
- **Principle choice validation** results and errors
- **Voting records** (while maintaining secret ballot privacy)
- **Income distribution scenarios** used in experiment

#### Enhanced Export Formats
- Add economic outcome CSV files
- Include wealth tracking across rounds
- Maintain existing JSON/CSV/TXT formats with new data

### 7. Validation and Error Handling

#### Principle Choice Validation
- **Floor Constraint Validation**: Ensure dollar amount is specified for principle 3
- **Range Constraint Validation**: Ensure dollar amount is specified for principle 4  
- **Error Response System**: Send clear error messages to agents for invalid choices
- **Retry Mechanism**: Allow agents to resubmit corrected choices

#### Economic Logic Validation
- **Distribution Selection**: Ensure selected distributions exist in configuration
- **Payout Calculation**: Verify economic calculations are correct
- **Wealth Tracking**: Maintain accurate cumulative wealth records

## Implementation Phases

### Phase A: Core Model and Configuration Updates (Week 1-2)
1. Update principle definitions in `models.py`
2. Create new data models for economics and preferences
3. Extend configuration schema for income distributions
4. Update YAML configuration validation

### Phase B: Service Layer Development (Week 2-3)  
1. Implement new service classes (economics, preference, validation, voting)
2. Update existing services to remove veil of ignorance concepts
3. Integrate economic logic with principle application
4. Add validation mechanisms for principle choices

### Phase C: Agent and Flow Updates (Week 3-4)
1. Update agent instructions and remove veil of ignorance language
2. Implement new experiment flow with Phase 1 and Phase 2 structure
3. Add economic state tracking to agents
4. Integrate preference ranking collection

### Phase D: Data Systems and Testing (Week 4-5)
1. Update logging and export systems for new data types
2. Create comprehensive test suite for new functionality
3. Validate economic calculations and payout systems
4. Test end-to-end experiment flows

### Phase E: Configuration and Documentation (Week 5-6)
1. Create example configurations for new system
2. Update CLAUDE.md with new system documentation
3. Migrate existing configuration files to new format
4. Create validation scripts for configuration migration

## Migration Strategy

### Data Model Migration
- **Backward Compatibility**: No need to maintain support for reading old experiment results
- **Configuration Conversion**: Provide scripts to convert existing YAML files
- **Result Comparison**: Tools to compare old vs new system outputs for validation

### Testing Strategy
- **Unit Tests**: Individual component testing for new services
- **Integration Tests**: End-to-end experiment flow testing
- **Economic Logic Tests**: Validation of principle application and payout calculations
- **Configuration Tests**: YAML parsing and validation testing

### Rollout Plan
1. **Development Environment**: Implement and test new system in isolation
2. **Parallel Testing**: Run both old and new systems on same scenarios
3. **Gradual Migration**: Start with simple test configurations
4. **Full Replacement**: Complete transition once validation is complete

## Risk Mitigation

### Technical Risks
- **Breaking Changes**: Maintain clear separation between old and new system during development
- **Configuration Complexity**: Provide comprehensive examples and validation
- **Economic Logic Errors**: Implement extensive testing for calculation accuracy

### Research Continuity Risks
- **Data Compatibility**: Ensure research data remains comparable across system versions
- **Experimental Validity**: Validate that new system produces meaningful research results
- **Documentation Gaps**: Maintain comprehensive documentation throughout transition

## Configuration Examples

### Basic New Configuration
```yaml
experiment_id: "basic_new_game"

phase1:
  enable_detailed_examples: true
  repeated_applications: 4

phase2: 
  enable_secret_ballot: true

economics:
  payout_ratio: 0.0001
  starting_wealth: 0.0

income_distributions:
  - distribution_id: 1
    income_by_class:
      High: 32000
      Medium_high: 27000  
      Medium: 24000
      Medium_low: 13000
      Low: 12000

agents:
  - name: "Agent_1"
    model: "gpt-4.1-nano"
  - name: "Agent_2" 
    model: "gpt-4.1-nano"

defaults:
  personality: "You are participating in an economic decision-making experiment."
  model: "gpt-4.1-nano"
```

## Success Criteria

### Functional Requirements
- ✅ All agents can complete preference ranking with certainty levels
- ✅ Economic outcomes are calculated correctly based on principle choices
- ✅ Bank accounts track wealth accurately across rounds
- ✅ Principle choice validation works for constraints
- ✅ Secret ballot voting system functions properly
- ✅ Income distribution scenarios are configurable via YAML

### Research Requirements  
- ✅ New system produces consistent and meaningful experimental results
- ✅ Data export maintains research utility and analysis capabilities
- ✅ Economic incentives are properly aligned with experimental goals
- ✅ Agent behavior changes appropriately based on economic feedback

### Technical Requirements
- ✅ System maintains existing performance and reliability standards
- ✅ Configuration system remains flexible and user-friendly  
- ✅ Logging and export systems capture all relevant experimental data
- ✅ Backward compatibility with existing research data analysis tools

## Questions for Clarification

1. **Income Distribution Scenarios**: Should the system support multiple distribution sets per experiment, or one set per experiment configuration? 
-->both 

2. **Economic Realism**: Should the income amounts be realistic (e.g., $50,000-$150,000) or kept at the specified amounts ($12,000-$32,000)?
--> default current amount, but can be specified in configuration to be different 

3. **Constraint Parameter Bounds**: Are there minimum/maximum values for floor and range constraints that should be enforced?
--> no 

4. **Voting Privacy**: In the secret ballot, should vote details be logged for research purposes while keeping them hidden from other agents?
--> YES 

5. **Round Economy**: Should wealth carry over between different experiment runs, or reset for each new experiment?
Each run is independet! 

6. **Distribution Selection Logic**: How should the system handle cases where multiple distributions satisfy the same principle constraints?
--> This should not happen! Ensure that it wont 

