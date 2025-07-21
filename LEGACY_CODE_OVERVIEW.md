# Legacy Code Overview

This document provides a comprehensive analysis of legacy code components that are no longer actively used in the current implementation of the Multi-Agent Distributive Justice Experiment framework.

## Executive Summary

The codebase has evolved from a simple deliberation system to a sophisticated two-phase economic experiment framework. During this evolution, several components have become legacy while being maintained for backward compatibility.

## 🏛️ **Legacy Architecture Components**

### 1. **DeliberationManager (Legacy Facade)**

**Location**: `src/maai/core/deliberation_manager.py`
**Status**: 🔶 **LEGACY but maintained for compatibility**

```python
class DeliberationManager:
    """FACADE PATTERN: Legacy interface for complex operations."""
```

**Why it's legacy**:
- The `DeliberationManager` now serves purely as a wrapper around `ExperimentOrchestrator`
- All real functionality has been moved to `ExperimentOrchestrator`
- Maintained only for backward compatibility with older scripts

**Current usage**:
- Used by `run_single_experiment()` function
- Immediately delegates to `ExperimentOrchestrator`

**Migration path**: Direct use of `ExperimentOrchestrator` is preferred for new code.

---

### 2. **Legacy Export System**

**Location**: `src/maai/export/`
**Status**: 🔴 **COMPLETELY REMOVED**

```python
# Legacy data export system has been removed
# All export functionality is now handled by ExperimentLogger.export_unified_json()
```

**What was removed**:
- Separate CSV, JSON, and text file exporters
- Multi-file output system
- Complex export configuration options
- Data transformation and formatting utilities

**Replaced by**: 
- Single unified JSON export via `ExperimentLogger.export_unified_json()`
- Agent-centric data organization
- Complete experiment data in one file

---

### 3. **Legacy Feedback System**

**Location**: `src/maai/core/models.py` (FeedbackResponse)
**Status**: 🔶 **LEGACY but included in exports**

```python
class FeedbackResponse(BaseModel):
    """Individual agent feedback after experiment completion."""
    # ... legacy feedback fields
```

**Why it's legacy**:
- Original post-experiment feedback collection is simplified
- New game logic focuses on preference rankings instead
- Automated feedback generation based on choices

**Current usage**:
- Still collected automatically in `ExperimentOrchestrator._collect_feedback()`
- Included in `ExperimentResults` for compatibility
- Marked as `"Post-experiment feedback (legacy)"` in models

---

### 4. **Legacy Runner Scripts**

**Location**: Root directory
**Status**: 🔶 **DEPRECATED wrappers maintained for compatibility**

**Files**:
- `run_experiment.py` - "DEPRECATED: Backward compatibility wrapper"
- `run_batch.py` - "DEPRECATED: Backward compatibility wrapper"

**Current implementation**: All functionality moved to `src/maai/runners/`

---

### 5. **SummaryAgent (Unused)**

**Location**: `src/maai/agents/summary_agent.py`
**Status**: 🔶 **IMPLEMENTED but not actively used**

```python
class SummaryAgent(Agent):
    """Specialized agent for generating structured summaries of deliberation rounds."""
```

**Why it's unused**:
- Summary generation is handled by `PublicHistoryService`
- SummaryAgent was designed for older deliberation patterns
- Current system uses direct conversation logging

**Configuration**: Still configurable via `SummaryAgentConfig` but not instantiated.

---

## 🧩 **Legacy Model Components**

### 1. **AgentMemory vs EnhancedAgentMemory**

**Legacy**: `AgentMemory` (src/maai/core/models.py:179)
**Current**: `EnhancedAgentMemory` (src/maai/core/models.py:263)

**Differences**:
```python
# Legacy - Simple Phase 2 only
class AgentMemory(BaseModel):
    memory_entries: List[MemoryEntry] = Field(default_factory=list)

# Current - Supports both phases + consolidation
class EnhancedAgentMemory(BaseModel):
    memory_entries: List[MemoryEntry] = Field(default_factory=list)  # Phase 2
    individual_memories: List[IndividualMemoryEntry] = Field(default_factory=list)  # Phase 1
    consolidated_memory: Optional[ConsolidatedMemory] = Field(None)  # Bridge
```

### 2. **Legacy Configuration Fields**

Several configuration options exist but are no longer used:

```yaml
# Legacy fields that still exist for compatibility
summary_agent:          # SummaryAgent config (unused)
  model: "gpt-4.1-mini"
  temperature: 0.1
  max_tokens: 1000

public_history_mode: "full"  # Simplified (was complex enum)
```

---

## 📊 **Legacy vs Current Architecture**

### **Legacy Flow** (Pre-ExperimentOrchestrator):
```
DeliberationManager → Services → Export System → Multiple Files
```

### **Current Flow**:
```
ExperimentOrchestrator → Integrated Services → ExperimentLogger → Single JSON
```

### **Key Changes**:

| **Aspect** | **Legacy** | **Current** |
|------------|------------|-------------|
| **Entry Point** | `DeliberationManager` | `ExperimentOrchestrator` |
| **Export** | Multiple files (CSV, JSON, TXT) | Single unified JSON |
| **Memory** | Simple round-based | Phase-aware with consolidation |
| **Game Logic** | Simple deliberation | Two-phase economic experiment |
| **Earnings** | Not tracked | Complete earnings tracking system |
| **Feedback** | Manual collection | Automated generation |
| **Services** | Loosely coupled | Tightly integrated |

---

## 🚨 **Unused Code Sections**

### 1. **Unused Methods in ExperimentOrchestrator**

```python
# These methods exist but are not called in current flow:
def _collect_feedback(self, consensus_result):
    """Legacy feedback collection - auto-generated now"""
    # Still implemented but generates basic feedback automatically
```

### 2. **Unused Model Classes**

```python
# These models are defined but rarely used:
class SummaryAgentConfig(BaseModel):  # SummaryAgent not instantiated
class PublicHistoryMode(str, Enum):   # Simplified to boolean logic
```

### 3. **Legacy Test Configurations**

**Location**: `tests/configs/default.yaml`
**Status**: Uses old configuration format without new game logic fields

---

## 🔄 **Backward Compatibility Layers**

### 1. **Import Compatibility**

```python
# src/maai/core/__init__.py - Still exports legacy components
from .deliberation_manager import DeliberationManager, run_single_experiment

# Root level wrappers still work
from maai.runners import run_experiment  # New way
# vs
python run_experiment.py config_name     # Legacy way (still works)
```

### 2. **Configuration Compatibility**

- Old YAML configs still load successfully
- Missing fields get default values
- Legacy field names are supported

### 3. **Data Model Compatibility**

- `ExperimentResults` includes both legacy and new fields
- Legacy fields marked with "(legacy)" in descriptions
- Full backward compatibility in JSON exports

---

## 📈 **Migration Recommendations**

### **Immediate Actions** (Low Risk):
1. ✅ Remove `src/maai/export/` directory (already done)
2. ✅ Mark root scripts as deprecated (already done)
3. Update documentation to reference new entry points

### **Future Cleanup** (Requires careful testing):
1. **Phase out DeliberationManager**: Direct ExperimentOrchestrator usage
2. **Remove SummaryAgent**: Not needed with current architecture  
3. **Simplify model hierarchy**: Merge legacy/current memory models
4. **Clean up unused configuration options**

### **Major Refactor** (Breaking changes):
1. **Remove FeedbackResponse**: Replace with automated analysis
2. **Eliminate legacy compatibility layers**
3. **Restructure import hierarchy**

---

## 🏷️ **Code Markers and Comments**

The codebase uses these markers to identify legacy code:

```python
# "DEPRECATED:" - Wrapper maintained for compatibility
# "Legacy" - Old system still supported
# "(legacy)" - Field descriptions for old data
# "FACADE PATTERN" - Wrapper around newer implementation
```

**Search command**: `grep -r "DEPRECATED\|legacy\|Legacy" --include="*.py" src/`

---

## 🎯 **Current Active Architecture**

### **Core Flow** (Non-Legacy):
```
runners/single.py
  ↓
deliberation_manager.run_single_experiment()  [Compatibility layer]
  ↓  
DeliberationManager.run_experiment()  [Legacy facade]
  ↓
ExperimentOrchestrator.run_experiment()  [Real implementation]
  ↓
Phase 1: Individual + Phase 2: Group
  ↓
ExperimentLogger.export_unified_json()  [Single file output]
```

### **Active Services**:
- ✅ `ExperimentOrchestrator` - Main coordinator
- ✅ `EarningsTrackingService` - New earnings system  
- ✅ `ExperimentLogger` - Unified logging
- ✅ `EconomicsService` - Income distributions
- ✅ `ConsensusService` - Agreement detection
- ✅ `MemoryService` - Phase-aware memories
- ✅ `PreferenceService` - Rankings collection
- ✅ `ValidationService` - Input validation
- ✅ `DetailedExamplesService` - Concrete examples

### **Legacy/Unused Services**:
- 🔶 `DeliberationManager` - Compatibility facade only
- 🔶 `SummaryAgent` - Implemented but unused
- 🔴 `Export system` - Completely removed

---

## 💡 **Benefits of Current Architecture**

1. **Unified Data Model**: Single JSON export with all experiment data
2. **Economic Realism**: Complete earnings tracking with real payouts
3. **Phase Awareness**: Proper individual → group transition
4. **Service Integration**: Tightly coupled services for reliability
5. **Research Focus**: Agent-centric data organization
6. **Backward Compatibility**: Legacy systems still work

---

## 📝 **Conclusion**

The legacy code represents the evolution of the system from a simple deliberation framework to a sophisticated economic experiment platform. While legacy components are maintained for compatibility, the current active architecture provides:

- **Better research validity** through economic incentives
- **Richer data collection** through comprehensive logging  
- **More realistic agent behavior** through phase-based learning
- **Easier analysis** through unified data export

The legacy components should be gradually phased out in future versions while maintaining the research capabilities that make this framework valuable for distributive justice experiments.

---

*Generated on: $(date)*
*Framework Version: Two-Phase Economic Incentive-Based Game Logic*
*Total Legacy Components Identified: 12*
*Backward Compatibility: Maintained*