# Total Earnings Tracking Implementation Plan

## Problem Statement

Currently, agents receive individual payout information after each round but are never informed of their **cumulative total earnings** across all experiment phases. This creates an incomplete economic feedback loop where agents cannot evaluate their overall financial performance or make informed decisions based on their accumulated wealth.

**Current Gaps:**
- Agents see individual round payouts (e.g., "Round 1: $2.00", "Round 2: $3.50") 
- No running total or cumulative balance shown
- No final total earnings summary at experiment end
- Agents cannot assess their overall economic success
- Incomplete psychological impact of economic incentives

## Proposed Solution: Comprehensive Earnings Tracking System

### Core Features

1. **Running Balance Tracking**: Maintain cumulative earnings throughout the experiment
2. **Progressive Disclosure**: Show running total at strategic points
3. **Final Earnings Summary**: Complete financial overview at experiment end
4. **Phase-Based Reporting**: Separate tracking for Phase 1 vs Phase 2 earnings
5. **Comparative Context**: Show earnings relative to potential ranges

### Implementation Architecture

#### 1. **Enhanced Agent Earnings Tracking**

**New Data Models** (`src/maai/core/models.py`):
```python
class AgentEarnings(BaseModel):
    """Track cumulative earnings for an agent throughout the experiment."""
    agent_id: str
    phase1_earnings: float = 0.0
    phase2_earnings: float = 0.0
    individual_round_payouts: List[float] = Field(default_factory=list)
    total_earnings: float = 0.0
    earnings_history: List[EarningsUpdate] = Field(default_factory=list)

class EarningsUpdate(BaseModel):
    """Record of a single earnings update."""
    round_type: str  # "individual_round" | "group_outcome"
    round_number: Optional[int]
    payout_amount: float
    cumulative_total: float
    timestamp: datetime
    context: str  # Description of what earned this payout

class EarningsContext(BaseModel):
    """Context for earnings disclosure to agents."""
    agent_id: str
    current_total: float
    phase1_total: float
    phase2_total: float
    round_count: int
    potential_range: Dict[str, float]  # min/max possible earnings
    performance_percentile: Optional[float] = None
```

#### 2. **EarningsTrackingService**

**New Service** (`src/maai/services/earnings_tracking_service.py`):
```python
class EarningsTrackingService:
    """Service for tracking and reporting agent earnings throughout experiment."""
    
    def __init__(self, payout_ratio: float):
        self.agent_earnings: Dict[str, AgentEarnings] = {}
        self.payout_ratio = payout_ratio
    
    def initialize_agent_earnings(self, agent_id: str) -> None
    def add_individual_round_payout(self, agent_id: str, payout: float, round_num: int) -> AgentEarnings
    def add_group_payout(self, agent_id: str, payout: float) -> AgentEarnings
    def get_agent_total_earnings(self, agent_id: str) -> float
    def get_earnings_summary(self, agent_id: str) -> EarningsContext
    def calculate_potential_earnings_range(self, income_distributions: List[IncomeDistribution]) -> Dict[str, float]
    def get_performance_percentile(self, agent_id: str) -> float
    async def generate_earnings_disclosure(self, agent: DeliberationAgent, context: EarningsContext) -> str
```

#### 3. **Strategic Earnings Disclosure Points**

**Timing and Content Strategy:**

**Point 1: After Individual Round 2**
- Show running total to build awareness
- "So far, you have earned $X.XX from 2 individual rounds"
- Builds economic engagement without overwhelming initial experience

**Point 2: End of Phase 1**
- Complete Phase 1 summary before group deliberation
- "Phase 1 Total: $X.XX from 4 individual rounds (Range: $Y.YY - $Z.ZZ possible)"
- Sets context for Phase 2 decision-making

**Point 3: After Group Outcome**
- Group phase payout plus Phase 1 recap
- "Group Decision Payout: $X.XX | Phase 1 Total: $Y.YY | Grand Total: $Z.ZZ"

**Point 4: Final Experiment Summary**
- Comprehensive financial overview
- Performance context and comparative analysis
- Complete earnings breakdown with explanation

### Implementation Plan

#### Phase 1: Core Infrastructure (Week 1-2)

**Step 1.1: Data Models**
- Add `AgentEarnings`, `EarningsUpdate`, `EarningsContext` to `models.py`
- Integrate with existing `EconomicOutcome` model
- Add earnings fields to `ExperimentResults`

**Step 1.2: EarningsTrackingService**
- Create new service with core tracking functionality
- Implement earnings accumulation and summary methods
- Add potential range calculations

**Step 1.3: Service Integration**
- Integrate EarningsTrackingService with ExperimentOrchestrator
- Update economic outcome handling to include earnings tracking
- Modify economics service to provide range calculations

#### Phase 2: Strategic Disclosure Implementation (Week 2-3)

**Step 2.1: Disclosure Methods**
- Implement earnings disclosure generation with contextual messaging
- Create templates for different disclosure points
- Add psychological framing for earnings information

**Step 2.2: Integration Points**
- Add earnings disclosure after individual round 2
- Implement Phase 1 summary before group deliberation
- Add group outcome earnings context
- Create final experiment earnings summary

**Step 2.3: Agent Communication**
- Develop clear, motivating earnings messages
- Include comparative context (potential ranges, performance)
- Ensure messages align with experimental goals

#### Phase 3: Enhanced Features (Week 3-4)

**Step 3.1: Advanced Analytics**
- Performance percentile calculations
- Earnings optimization analysis
- Comparative performance metrics

**Step 3.2: Memory System Integration**
- Include earnings context in Phase 1 memory consolidation
- Add earnings awareness to Phase 2 memory generation
- Enhance phase-aware memory strategies with financial context

**Step 3.3: Configuration Options**
- Configurable disclosure timing and frequency
- Optional earnings disclosure modes
- Customizable messaging depth and style

#### Phase 4: Testing and Validation (Week 4)

**Step 4.1: Unit Testing**
- Test earnings tracking accuracy
- Validate disclosure message generation
- Test edge cases (zero earnings, maximum earnings)

**Step 4.2: Integration Testing**
- End-to-end earnings tracking through full experiment
- Validate earnings disclosure timing
- Test with different configuration options

**Step 4.3: Experimental Validation**
- Run test experiments with earnings tracking enabled
- Validate psychological impact and clarity of messaging
- Ensure no interference with core experimental objectives

### Expected Benefits

#### Research Benefits
1. **Complete Economic Feedback Loop**: Agents have full financial context for decision-making
2. **Enhanced Motivation**: Clear earnings progression increases engagement
3. **Better Data Quality**: More informed agent decisions based on comprehensive financial picture
4. **Comparative Analysis**: Ability to analyze earnings impact on subsequent decisions

#### Agent Experience Benefits
1. **Financial Awareness**: Clear understanding of cumulative economic performance
2. **Performance Context**: Relative performance awareness motivates optimal strategies
3. **Goal Orientation**: Clear financial targets and outcomes
4. **Satisfaction**: Complete closure on economic aspects of experiment

#### Experimental Validity Benefits
1. **Realistic Economic Behavior**: Mirrors real-world financial awareness
2. **Improved Incentive Alignment**: Agents fully understand economic stakes
3. **Enhanced Decision Quality**: Decisions informed by complete financial picture
4. **Reduced Experimental Artifacts**: Eliminates confusion about earnings

### Configuration Options

```yaml
# Earnings Tracking Configuration
earnings_tracking:
  enabled: true
  disclosure_points:
    - "after_round_2"      # Show running total after 2nd individual round
    - "end_phase1"         # Phase 1 summary before group deliberation
    - "after_group"        # Group outcome with running total
    - "experiment_end"     # Final comprehensive summary
  
  disclosure_style: "motivational"  # "minimal" | "standard" | "motivational" | "detailed"
  show_performance_context: true    # Include comparative performance information
  show_potential_ranges: true       # Show min/max possible earnings
  include_phase_breakdown: true     # Separate Phase 1 vs Phase 2 reporting
  
  messaging:
    congratulatory_threshold: 0.75  # Performance percentile for congratulatory messaging
    encouragement_threshold: 0.25   # Performance percentile for encouragement messaging
    
# Integration with existing systems
phase1_memory_integration:
  include_earnings_context: true    # Include earnings in Phase 1 memory consolidation
  
memory_strategy_enhancement:
  earnings_aware: true              # Phase-aware strategies consider earnings context
```

### Implementation Timeline

**Week 1**: Core data models and earnings tracking service
**Week 2**: Strategic disclosure implementation and integration points
**Week 3**: Advanced features and memory system integration
**Week 4**: Testing, validation, and configuration options

### Risk Mitigation

**Technical Risks**:
- Earnings calculation accuracy: Comprehensive unit testing
- Performance impact: Lightweight service design
- Integration complexity: Phased implementation approach

**Experimental Risks**:
- Altered agent behavior: Configurable disclosure levels
- Cognitive overload: Strategic timing and clear messaging
- Bias introduction: Neutral, factual reporting with optional context

**Data Quality Risks**:
- Logging completeness: Comprehensive earnings history tracking
- Export integration: Enhanced data export with earnings summaries
- Analysis impact: Preserved existing analysis capabilities

### Success Metrics

1. **Completeness**: 100% of agents receive accurate total earnings information
2. **Clarity**: Earnings messages are clear and motivating
3. **Integration**: Seamless integration with existing experiment flow
4. **Performance**: <5% increase in experiment runtime
5. **Research Value**: Enhanced data quality and agent decision-making

### Example Implementation

**After Individual Round 2:**
```
"You have now completed 2 individual rounds and earned $5.50 total so far. 
Your choices and economic outcomes are building your understanding of how 
different principles affect income distributions. Continue applying your 
developing strategy in the remaining rounds."
```

**End of Phase 1:**
```
"Phase 1 Complete! You earned $12.75 total from 4 individual rounds 
(possible range was $2.00 - $20.00). You're now ready to enter group 
deliberation with this experience. Your individual learning and earnings 
will inform your approach to reaching group consensus."
```

**Final Summary:**
```
"Experiment Complete! Your total earnings: $18.25
- Phase 1 (Individual): $12.75 (4 rounds)
- Phase 2 (Group): $5.50 (final outcome)

Performance: 73rd percentile (above average)
Thank you for your thoughtful participation in this distributive justice experiment."
```

## Conclusion

This implementation creates a complete economic feedback system that enhances agent engagement, improves decision quality, and provides richer research data while maintaining the core experimental integrity. The phased approach ensures reliable implementation with comprehensive testing and validation.

The system transforms the current piecemeal payout information into a coherent financial narrative that agents can understand and act upon, completing the economic incentive structure of the experiment.