# New Logic Implementation Analysis & Plan

## Current State Analysis

### According to new_logic.md Specification:

**Phase 1: Familiarization with Principles individually**

1. **Step 1.1: Reading of Principles** → **First Assessment (Ranking)**
   - Participants read the four principles as text
   - Agents provide initial preference ranking (1-4) with certainty level

2. **Step 1.2: Detailed Examples** → **Second Assessment (Ranking)**
   - Agents see principle-to-distribution mapping examples
   - Shows exactly which distribution each principle would select
   - Agents provide second preference ranking after understanding mappings

3. **Step 1.3: Individual Application Rounds** → **Third Assessment (Ranking)**
   - Agent chooses a principle
   - Principle is applied to select a distribution  
   - Agent is randomly assigned an income class
   - Agent receives economic payout based on their class
   - **Repeated X times** (should be configurable parameter, currently fixed at 4)
   - Agents provide final preference ranking after experiencing outcomes

**Phase 2: Group Experiment**
- Group deliberation, voting, final economic outcomes, final ranking

### Current Implementation Analysis:

**✅ CORRECTLY IMPLEMENTED:**
1. **Phase 1.1: Initial Preference Ranking** - ✅ Working correctly
2. **Phase 1.2: Detailed Examples** - ✅ Working correctly (fixed in recent commit)
3. **Phase 1.3: Individual Application Rounds** - ✅ Basic structure exists
4. **Economic Outcomes** - ✅ Economic service working
5. **Logging System** - ✅ ExperimentLogger captures most data

**❌ MISSING/INCORRECT:**
1. **Missing Second Assessment** - No preference ranking after detailed examples
2. **Missing Third Assessment** - No preference ranking after individual rounds
3. **Fixed Individual Rounds** - Hardcoded to 4, should be configurable parameter
4. **Incomplete Logging** - Missing logs for the 3 assessment steps
5. **Assessment Structure** - Only captures initial + final rankings, missing intermediate ones

### Current Flow vs. Specification:

**Current Flow:**
```
Phase 1:
├── 1.1: Initial Preference Ranking ✅
├── 1.2: Detailed Examples ✅ 
├── 1.3: Individual Rounds (4x fixed) ❌
└── 1.4: Post-Individual Ranking ✅

Phase 2:
├── 2.1: Group Deliberation ✅
├── 2.2: Secret Ballot ✅
├── 2.3: Economic Outcomes ✅
└── 2.4: Final Ranking ✅
```

**Should Be:**
```
Phase 1:
├── 1.1: Read Principles → First Assessment ✅
├── 1.2: Detailed Examples → Second Assessment ❌ MISSING
├── 1.3: Individual Rounds (X configurable) → Third Assessment ❌ MISSING  
│   ├── Round 1: Choose→Apply→Outcome
│   ├── Round 2: Choose→Apply→Outcome
│   └── Round X: Choose→Apply→Outcome
└── → Third Assessment (Final Ranking) ❌ WRONG PLACEMENT

Phase 2: [Same as current] ✅
```

## Implementation Plan

### Task 1: Add Second Assessment (After Detailed Examples)
**Location:** `src/maai/services/experiment_orchestrator.py`

1. **Add new method:** `_collect_post_examples_preference_ranking()`
2. **Modify:** `_present_detailed_examples()` to call assessment method
3. **Update:** Data model to include "post_examples" phase rankings
4. **Add:** Logging for this assessment step

### Task 2: Fix Third Assessment (After Individual Rounds)
**Location:** `src/maai/services/experiment_orchestrator.py`

1. **Move:** `_collect_post_individual_preference_ranking()` to end of individual rounds
2. **Rename:** to `_collect_post_individual_rounds_preference_ranking()`
3. **Update:** Context to reflect "after experiencing individual outcomes"
4. **Add:** Logging for this assessment step

### Task 3: Make Individual Rounds Configurable
**Locations:** 
- `src/maai/core/models.py` (ExperimentConfig)
- `src/maai/services/experiment_orchestrator.py`

1. **Add:** `individual_rounds: int` parameter to ExperimentConfig
2. **Remove:** Hardcoded `range(1, 5)` in individual rounds loop
3. **Use:** `self.config.individual_rounds` for round count
4. **Update:** All related comments and documentation

### Task 4: Enhanced Logging for Assessment Steps
**Location:** `src/maai/services/experiment_logger.py`

1. **Add:** `log_first_assessment()` method
2. **Add:** `log_second_assessment()` method  
3. **Add:** `log_third_assessment()` method
4. **Add:** Assessment phase metadata to output JSON
5. **Update:** Export methods to include all assessment data

### Task 5: Update Configuration Schema
**Locations:**
- `configs/*.yaml` files
- Documentation

1. **Add:** `individual_rounds: X` parameter to YAML configs
2. **Update:** Default configurations to use reasonable values (4-6 rounds)
3. **Update:** Systematic analysis notebook to use configurable rounds

## Detailed Implementation Steps

### Step 1: Data Model Updates

```python
# In src/maai/core/models.py
class ExperimentConfig(BaseModel):
    # ... existing fields ...
    individual_rounds: int = Field(default=4, ge=1, description="Number of individual application rounds")
```

### Step 2: Add Missing Assessment Methods

```python
# In src/maai/services/experiment_orchestrator.py

async def _collect_post_examples_preference_ranking(self):
    """Collect preference rankings after detailed examples (Second Assessment)."""
    print("\n--- Phase 1.2.1: Second Assessment (After Detailed Examples) ---")
    
    post_examples_rankings = await self.preference_service.collect_batch_preference_rankings(
        self.agents, 
        "post_examples", 
        "Now that you have seen detailed examples of how each principle maps to specific income distributions, please rank the principles again."
    )
    
    # Store and log rankings
    for ranking in post_examples_rankings:
        self.logger.log_preference_ranking(ranking)
        self.logger.log_second_assessment(ranking)

async def _collect_post_individual_rounds_preference_ranking(self):
    """Collect preference rankings after individual rounds (Third Assessment)."""
    print("\n--- Phase 1.3.1: Third Assessment (After Individual Application) ---")
    
    context = f"""You have now completed {self.config.individual_rounds} individual rounds where you applied different principles and received economic outcomes.
    
Based on your actual experience with applying principles and receiving economic rewards, please rank the principles again."""
    
    post_individual_rankings = await self.preference_service.collect_batch_preference_rankings(
        self.agents,
        "post_individual", 
        context
    )
    
    # Store and log rankings  
    for ranking in post_individual_rankings:
        self.logger.log_preference_ranking(ranking)
        self.logger.log_third_assessment(ranking)
```

### Step 3: Update Main Flow

```python
async def _run_phase_1_individual_familiarization(self):
    """Phase 1: Individual Familiarization with proper assessment structure."""
    print("\n=== PHASE 1: Individual Familiarization ===")
    
    # 1.1: Read Principles → First Assessment
    await self._collect_initial_preference_ranking()
    
    # 1.2: Detailed Examples → Second Assessment  
    await self._present_detailed_examples()
    await self._collect_post_examples_preference_ranking()  # NEW
    
    # 1.3: Individual Rounds → Third Assessment
    await self._run_individual_application_rounds()
    await self._collect_post_individual_rounds_preference_ranking()  # MOVED HERE
```

### Step 4: Update Individual Rounds Loop

```python
async def _run_individual_application_rounds(self):
    """Run configurable number of individual principle application rounds."""
    rounds_count = self.config.individual_rounds
    print(f"\n--- Phase 1.3: Individual Application Rounds ({rounds_count} rounds) ---")
    
    for round_num in range(1, rounds_count + 1):  # Use configurable count
        print(f"\n  Round {round_num}/{rounds_count}")
        
        for agent in self.agents:
            await self._run_individual_round_for_agent(agent, round_num)
    
    print(f"Completed {rounds_count} individual rounds with {len(self.economic_outcomes)} total outcomes")
```

### Step 5: Enhanced Logging

```python
# In src/maai/services/experiment_logger.py

def log_first_assessment(self, ranking: PreferenceRanking):
    """Log first assessment (after reading principles)."""
    self._log_assessment_step("first", "after_reading_principles", ranking)

def log_second_assessment(self, ranking: PreferenceRanking):
    """Log second assessment (after detailed examples)."""
    self._log_assessment_step("second", "after_detailed_examples", ranking)

def log_third_assessment(self, ranking: PreferenceRanking):
    """Log third assessment (after individual rounds)."""
    self._log_assessment_step("third", "after_individual_rounds", ranking)

def _log_assessment_step(self, assessment_number: str, phase: str, ranking: PreferenceRanking):
    """Generic method to log assessment steps."""
    assessment_data = {
        "assessment_number": assessment_number,
        "phase": phase,
        "timestamp": datetime.now().isoformat(),
        "agent_id": ranking.agent_id,
        "rankings": ranking.rankings,
        "certainty_level": ranking.certainty_level,
        "reasoning": ranking.reasoning
    }
    
    agent_data = self.agent_data.setdefault(ranking.agent_id, {})
    assessments = agent_data.setdefault("assessments", [])
    assessments.append(assessment_data)
```

## Priority Implementation Order

1. **HIGH:** Add Second Assessment (missing critical step)
2. **HIGH:** Fix Third Assessment placement 
3. **MEDIUM:** Make individual rounds configurable
4. **MEDIUM:** Enhanced logging for assessments
5. **LOW:** Update configuration files and documentation

## Testing Plan

1. **Unit Tests:** Test each new assessment method independently
2. **Integration Test:** Run full experiment with 3 assessment points
3. **Configuration Test:** Test with different individual_rounds values (2, 4, 6)
4. **Logging Test:** Verify all 3 assessments appear in output JSON
5. **Systematic Test:** Update systematic analysis notebook and verify

## Risk Assessment

**LOW RISK:** These changes are additive and don't break existing functionality
**MITIGATION:** All changes maintain backward compatibility with existing configs

## Files to Modify

1. `src/maai/core/models.py` - Add individual_rounds parameter
2. `src/maai/services/experiment_orchestrator.py` - Main flow changes
3. `src/maai/services/experiment_logger.py` - Enhanced logging
4. `configs/*.yaml` - Add individual_rounds parameter
5. `Systematic_Analysis.ipynb` - Update configurations

## Expected Outcome

After implementation:
- ✅ Three distinct assessment points as per specification
- ✅ Configurable individual rounds parameter  
- ✅ Complete logging of all assessment steps
- ✅ Proper flow matching new_logic.md specification
- ✅ Backward compatibility maintained