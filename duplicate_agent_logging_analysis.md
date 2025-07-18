# Duplicate Agent Logging Analysis

## Executive Summary

The experiment logs show duplicate agent entries (e.g., both `Agent_1` and `agent_1`) despite only 2 agents being configured. This analysis identifies the root cause as inconsistent agent identifier usage across multiple services, resulting in the same logical agent being logged under different keys.

## Problem Statement

**Expected**: 2 agents (`Agent_1`, `Agent_2`) as configured
**Actual**: 4 entries in logs (`Agent_1`, `Agent_2`, `agent_1`, `agent_2`)

The duplicate entries contain different types of data:
- **Capitalized entries** (`Agent_1`, `Agent_2`): Complete experiment data including initial evaluations, communications, and agent interactions
- **Lowercase entries** (`agent_1`, `agent_2`): Only memory generation data with empty `overall` sections

## Root Cause Analysis

### 1. Agent Creation Logic
**File**: `src/maai/agents/enhanced.py` (lines 333-334)
```python
agent_id = f"agent_{i+1}"           # Creates: agent_1, agent_2, agent_3
agent_name = agent_config.name or f"Agent {i+1}"  # Creates: Agent_1, Agent_2, Agent_3
```

Each agent object has two identifiers:
- `agent.agent_id`: Internal identifier in lowercase format (`agent_1`, `agent_2`)
- `agent.name`: Display name from config in proper case format (`Agent_1`, `Agent_2`)

### 2. Logger Initialization
**File**: `src/maai/services/experiment_logger.py` (lines 54-57)
```python
# Use the agent's name from config as the key for JSON structure
agent_name = agent_config.name or f"Agent_{i+1}"

# Initialize agent overall data
self.agent_data[agent_name] = {
```

The logger correctly initializes with agent names (`Agent_1`, `Agent_2`) as keys.

### 3. Memory Service Logging Calls
**File**: `src/maai/services/memory_service.py`

**Three separate logging calls using `agent.agent_id`**:

1. **Lines 194-199**: Memory context logging
```python
self.logger.log_memory_generation(
    agent_id=agent.agent_id,  # Uses agent_1, agent_2, agent_3
    round_num=round_number,
    memory_content=memory_context,
    strategy=type(self.memory_strategy).__name__
)
```

2. **Lines 215-220**: Memory entry logging
```python
self.logger.log_memory_generation(
    agent_id=agent.agent_id,  # Uses agent_1, agent_2, agent_3
    round_num=round_number,
    memory_content=memory_content,
    strategy=memory_entry.strategy_update
)
```

3. **Lines 362-367**: Decomposed strategy logging
```python
self.logger.log_memory_generation(
    agent_id=agent.agent_id,  # Uses agent_1, agent_2, agent_3
    round_num=round_number,
    memory_content=memory_content,
    strategy="decomposed"
)
```

### 4. Conversation Service Logging Call
**File**: `src/maai/services/conversation_service.py` (lines 402-407)
```python
self.logger.log_memory_generation(
    agent_id=agent.name,  # Uses Agent_1, Agent_2, Agent_3
    round_num=round_context.round_number,
    memory_content=private_memory_entry.situation_assessment,
    strategy=private_memory_entry.strategy_update
)
```

### 5. Logger Behavior
**File**: `src/maai/services/experiment_logger.py` (lines 102-113)
```python
def log_memory_generation(self, agent_id: str, round_num: int, 
                         memory_content: str, strategy: str = None):
    """Log memory generation for an agent."""
    if agent_id not in self.agent_data:
        self.agent_data[agent_id] = {"overall": {}}  # Creates new entry if not found
```

When the memory service calls `log_memory_generation()` with `agent.agent_id` (`agent_1`), but the logger was initialized with `agent.name` (`Agent_1`), the logger creates a new entry for the unrecognized key.

## Data Flow Analysis

### Per Round, Per Agent:
1. **Memory Service**: 3 logging calls using `agent.agent_id` → Creates/populates `agent_1`, `agent_2`
2. **Conversation Service**: 1 logging call using `agent.name` → Populates `Agent_1`, `Agent_2`

### Result:
- **4 total memory logging calls per agent per round**
- **2 different identifier formats creating separate log entries**
- **Appearance of 4 agents when only 2 are actually running**

## Evidence from Log Analysis

### Configuration File
```yaml
agents:
- name: Agent_1
  personality: You are a philosopher.
  model: gpt-4.1-nano
- name: Agent_2
  personality: You are a philosopher.
  model: Llama-4
```

### Log File Structure
```json
{
  "experiment_metadata": {...},
  "Agent_1": {
    "overall": {
      "model": "gpt-4.1-nano",
      "persona": "You are a philosopher.",
      "instruction": "...",
      "temperature": 0.5
    },
    "round_0": {...},
    "round_1": {...}
  },
  "Agent_2": {
    "overall": {
      "model": "Llama-4",
      "persona": "You are a philosopher.",
      "instruction": "...",
      "temperature": 0.5
    },
    "round_0": {...},
    "round_1": {...}
  },
  "agent_1": {
    "overall": {},
    "round_1": {"memory": "...", "strategy": "..."},
    "round_2": {"memory": "...", "strategy": "..."},
    "round_3": {"memory": "...", "strategy": "..."}
  },
  "agent_2": {
    "overall": {},
    "round_1": {"memory": "...", "strategy": "..."},
    "round_2": {"memory": "...", "strategy": "..."},
    "round_3": {"memory": "...", "strategy": "..."}
  }
}
```

### Conversation Pattern Evidence
The conversation data in `Agent_2` shows only 2 agents talking:
```json
"public_history": "SPEAKERS IN THIS ROUND SO FAR:\nAgent_1: ...\n\nYour current choice: Principle 3"
```

### Message Count Evidence
```json
"final_consensus": {
  "total_messages": 6
}
```
6 messages = 2 agents × 3 rounds, confirming only 2 agents are participating.

## Impact Assessment

### Functional Impact
- **No functional impact**: Only 2 agents are actually running and deliberating
- **Experiment results are valid**: The decision-making process involves the correct number of agents

### Data Quality Impact
- **Duplicate data**: Memory generation data is logged 4 times per agent per round
- **Inconsistent structure**: Capitalized entries have complete data, lowercase entries have only memory data
- **Analysis complications**: Data analysis tools may count 4 agents instead of 2

### Performance Impact
- **Minimal**: Extra logging calls add negligible overhead
- **Storage**: Log files are larger due to duplicate entries

## Recommended Solutions

### Solution 1: Standardize on Agent Names (Recommended)
Update all memory service logging calls to use `agent.name` instead of `agent.agent_id`:

```python
# In memory_service.py
self.logger.log_memory_generation(
    agent_id=agent.name,  # Change from agent.agent_id
    round_num=round_number,
    memory_content=memory_context,
    strategy=type(self.memory_strategy).__name__
)
```

### Solution 2: Consolidate Memory Logging
Reduce the number of memory logging calls by combining related data into single calls.

### Solution 3: Logger Validation
Add validation in the logger to prevent creation of new entries for unrecognized agent IDs.

## Files Requiring Changes

1. **`src/maai/services/memory_service.py`**: Update all logging calls to use `agent.name`
   - Line 194: `agent_id=agent.agent_id` → `agent_id=agent.name`
   - Line 215: `agent_id=agent.agent_id` → `agent_id=agent.name`
   - Line 362: `agent_id=agent.agent_id` → `agent_id=agent.name`

2. **Test files**: Update any tests that expect the current behavior

## Implementation and Resolution

### Fix Applied (Date: 2025-07-18)

**Problem**: Inconsistent agent identifier usage across services caused duplicate logging entries.

**Solution**: Updated all memory service logging calls to use `agent.name` instead of `agent.agent_id`.

#### Changes Made:

1. **File**: `src/maai/services/memory_service.py`
   - **Line 195**: Changed `agent_id=agent.agent_id` → `agent_id=agent.name`
   - **Line 216**: Changed `agent_id=agent.agent_id` → `agent_id=agent.name`  
   - **Line 363**: Changed `agent_id=agent.agent_id` → `agent_id=agent.name`

#### Before Fix:
```python
# Memory service logging calls
self.logger.log_memory_generation(
    agent_id=agent.agent_id,  # Used lowercase format: agent_1, agent_2
    round_num=round_number,
    memory_content=memory_context,
    strategy=type(self.memory_strategy).__name__
)
```

#### After Fix:
```python
# Memory service logging calls
self.logger.log_memory_generation(
    agent_id=agent.name,  # Now uses proper case format: Agent_1, Agent_2
    round_num=round_number,
    memory_content=memory_context,
    strategy=type(self.memory_strategy).__name__
)
```

### Verification Results

**Test Experiment**: `test_logging_fixes` configuration
- **Agents Configured**: 2 (`Agent_1`, `Agent_2`)
- **Log Entries Found**: 2 (`Agent_1`, `Agent_2`)
- **Duplicate Entries**: 0 ✅
- **Test Status**: PASSED

**Log File Structure After Fix**:
```json
{
  "experiment_metadata": {...},
  "Agent_1": {
    "overall": {...},
    "round_0": {...},
    "round_1": {...},
    "round_2": {...}
  },
  "Agent_2": {
    "overall": {...},
    "round_0": {...},
    "round_1": {...},
    "round_2": {...}
  }
}
```

### Impact Assessment

#### Before Fix:
- **4 agent entries** per experiment (2 real + 2 duplicates)
- **Inconsistent data structure** (capitalized vs lowercase keys)
- **Duplicate memory logging** (4 calls per agent per round)
- **Potential analysis errors** (counting wrong number of agents)

#### After Fix:
- **2 agent entries** per experiment (correct count)
- **Consistent data structure** (all use proper case agent names)
- **Consolidated memory logging** (all data under correct agent keys)
- **Accurate analysis** (correct agent count and data organization)

### Tests Passed
- ✅ `test_unified_logging.py` (10/10 tests)
- ✅ `test_decomposed_memory.py` (12/12 tests)
- ✅ `test_core.py` (3/3 tests)
- ✅ Verification test (no duplicate entries found)

## Conclusion

The duplicate agent entries issue has been **successfully resolved**. The fix involved standardizing on using `agent.name` consistently across all logging calls in the memory service, eliminating the inconsistent identifier usage that was causing duplicate entries.

**Key Outcomes**:
- ✅ Eliminated duplicate agent entries in log files
- ✅ Maintained all existing functionality
- ✅ Improved data consistency and accuracy
- ✅ Fixed without breaking any existing tests
- ✅ Verified through comprehensive testing

The logging system now correctly represents the actual experiment structure with the proper number of agents and consistent data organization.