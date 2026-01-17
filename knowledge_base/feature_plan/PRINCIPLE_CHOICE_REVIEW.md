# Principle Choice Implementation Review

## Executive Summary

This document reviews the current implementation of principle choices in the Multi-Agent Distributive Justice Experiment framework against the specified instruction requirements. The analysis reveals **significant misalignment** between the current implementation and the provided specification.

## Specified Instruction Requirements

The exact wording provided for principle choice instructions:

> "You are to make a choice from among the four principles of justice which are mentioned above: (a) maximizing the floor, (b) maximizing the average, (c) maximizing the average with a floor constraint, and (d) maximizing the average with a range constraint. If you choose (c) or (d), you will have to tell us what that floor or range constraint is before you can be said to have made a well-defined choice."

## Current Implementation Analysis

### 1. Principle Definitions and Labels

**Location**: `src/maai/core/models.py:461-487`

**Current Implementation**:
```python
DISTRIBUTIVE_JUSTICE_PRINCIPLES = {
    1: {
        "name": "MAXIMIZING THE FLOOR INCOME",
        "description": "The most just distribution of income..."
    },
    2: {
        "name": "MAXIMIZING THE AVERAGE INCOME", 
        "description": "The most just distribution of income..."
    },
    3: {
        "name": "MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT",
        "description": "The most just distribution of income..."
    },
    4: {
        "name": "MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT",
        "description": "The most just distribution of income..."
    }
}
```

**Gap Analysis**:
- ❌ Uses numbers (1,2,3,4) instead of letters (a,b,c,d)
- ❌ Uses capitalized, expanded names vs. specified lowercase phrases
- ❌ "MAXIMIZING THE FLOOR INCOME" vs. "maximizing the floor"
- ❌ "MAXIMIZING THE AVERAGE INCOME" vs. "maximizing the average"

### 2. Choice Prompt Implementation

**Location**: `src/maai/services/experiment_orchestrator.py:593-608`

**Current Prompt**:
```
Please choose one of the four principles of distributive justice:
1. MAXIMIZING THE FLOOR INCOME
2. MAXIMIZING THE AVERAGE INCOME  
3. MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT (specify the floor amount in dollars)
4. MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT (specify the range amount in dollars)

Your choice will determine which income distribution is selected, and you will be randomly assigned to an income class.
You will receive actual economic rewards based on your assigned income.

Please state:
1. Your chosen principle (1, 2, 3, or 4)
2. If choosing principle 3 or 4, specify the constraint amount
3. Your reasoning for this choice

Format: "I choose principle [number] [with constraint $X if applicable] because [reasoning]"
```

**Gap Analysis**:
- ❌ Completely different structure and wording from specification
- ❌ Missing the exact required language about constraints
- ❌ Uses numbered format instead of lettered format
- ❌ Adds extra context about economic rewards (not in specification)
- ❌ Structures choice as numbered steps rather than direct choice

### 3. Constraint Requirement Enforcement

**Validation Service** (`src/maai/services/validation_service.py:42-57`):
```python
if choice.principle_id == 3 and choice.floor_constraint is None:
    return ValidationResult(
        is_valid=False,
        error_message="Principle 3 requires a floor constraint to be specified"
    )

if choice.principle_id == 4 and choice.range_constraint is None:
    return ValidationResult(
        is_valid=False,
        error_message="Principle 4 requires a range constraint to be specified"
    )
```

**Assessment**:
- ✅ **Strength**: Correctly validates constraint requirements
- ✅ **Strength**: Provides appropriate error messages
- ❌ **Gap**: Error messages don't use specified language about "well-defined choice"

**Consensus Service Default Handling** (`src/maai/services/consensus_service.py:70-89`):
```python
# Apply default constraints if not specified
if principle_choice.principle_id == 3 and principle_choice.floor_constraint is None:
    principle_choice.floor_constraint = 15000  # Default $15,000 floor
    
if principle_choice.principle_id == 4 and principle_choice.range_constraint is None:
    principle_choice.range_constraint = 20000  # Default $20,000 range
```

**Assessment**:
- ❌ **Critical Issue**: Provides default values, directly contradicting specification requirement
- ❌ **Critical Issue**: Undermines the "you will have to tell us" requirement
- ❌ **Critical Issue**: Makes choices "well-defined" without agent specification

### 4. Secret Ballot Implementation

**Location**: `src/maai/services/experiment_orchestrator.py:808-821`

**Current Implementation**:
```
Please cast your SECRET BALLOT vote for the principle you want the group to adopt.
Your vote will not be revealed to other agents.

The four principles are:
1. MAXIMIZING THE FLOOR INCOME
2. MAXIMIZING THE AVERAGE INCOME
3. MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT (specify constraint in dollars)
4. MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT (specify constraint in dollars)

Format your vote as: "I vote for principle [number] [with constraint $X if applicable]"
```

**Gap Analysis**:
- ❌ Same formatting issues as regular choice prompts
- ❌ Doesn't use specified instruction wording
- ❌ Uses numbers instead of letters

### 5. Preference Ranking Implementation

**Location**: `src/maai/services/preference_service.py:53-71`

**Current Implementation**:
Uses the same principle text with numbered format, perpetuating the same gaps identified above.

## Critical Issues Summary

### 1. **Fundamental Format Mismatch**
- **Issue**: Entire system uses numbered format (1,2,3,4) vs. specified lettered format (a,b,c,d)
- **Scope**: System-wide across all choice points
- **Impact**: Direct contradiction with specification

### 2. **Missing Required Language**
- **Issue**: Doesn't include the critical phrase about constraints being required "before you can be said to have made a well-defined choice"
- **Scope**: All choice prompts
- **Impact**: Weakens emphasis on constraint requirement

### 3. **Default Constraint Values Contradiction**
- **Issue**: System automatically provides default values when constraints aren't specified
- **Scope**: Consensus service and choice parsing
- **Impact**: **Directly violates** the specification requirement for explicit constraint provision

### 4. **Principle Name Variations**
- **Issue**: Uses expanded, capitalized names vs. specified concise lowercase phrases
- **Scope**: Core models and all prompts
- **Impact**: Inconsistent terminology with specification

### 5. **Choice Structure Mismatch**
- **Issue**: Uses structured, multi-step format vs. specified direct choice format
- **Scope**: All choice prompts
- **Impact**: Different user experience than specified

## Files Requiring Updates for Compliance

### Core Models and Definitions
- `src/maai/core/models.py` - Update principle definitions and choice models
- `src/maai/core/models.py:461-487` - DISTRIBUTIVE_JUSTICE_PRINCIPLES dictionary

### Service Layer
- `src/maai/services/experiment_orchestrator.py` - All choice prompts
- `src/maai/services/consensus_service.py` - Remove default constraint handling
- `src/maai/services/validation_service.py` - Update error messages
- `src/maai/services/preference_service.py` - Update preference prompts

### Configuration Files
- Any YAML configurations that reference principle IDs would need updates

## Recommendations for Alignment

### 1. **Update Core Principle Definitions**
```python
DISTRIBUTIVE_JUSTICE_PRINCIPLES = {
    'a': {
        "name": "maximizing the floor",
        "description": "..."
    },
    'b': {
        "name": "maximizing the average", 
        "description": "..."
    },
    'c': {
        "name": "maximizing the average with a floor constraint",
        "description": "..."
    },
    'd': {
        "name": "maximizing the average with a range constraint",
        "description": "..."
    }
}
```

### 2. **Implement Exact Specification Wording**
Replace all choice prompts with:
```
You are to make a choice from among the four principles of justice which are mentioned above: (a) maximizing the floor, (b) maximizing the average, (c) maximizing the average with a floor constraint, and (d) maximizing the average with a range constraint. If you choose (c) or (d), you will have to tell us what that floor or range constraint is before you can be said to have made a well-defined choice.
```

### 3. **Remove Default Constraint Handling**
- Eliminate automatic default values in consensus service
- Ensure validation failures when constraints are missing
- Require explicit re-prompting until valid constraints are provided

### 4. **Update All Choice Models**
- Change PrincipleChoice model to use lettered IDs
- Update all parsing logic to handle lettered format
- Update all database/export logic to use new format

### 5. **Update Validation Messages**
Incorporate the "well-defined choice" language:
```python
error_message="If you choose (c) or (d), you will have to tell us what that floor or range constraint is before you can be said to have made a well-defined choice"
```

## Implementation Priority

### High Priority (Critical for Compliance)
1. Remove default constraint handling - **CRITICAL VIOLATION**
2. Update choice prompt to exact specification wording
3. Change numbering system from (1,2,3,4) to (a,b,c,d)

### Medium Priority (Important for Accuracy)
1. Update principle names to match specification
2. Update validation error messages
3. Update all choice points (individual, ballot, preferences)

### Low Priority (Consistency)
1. Update configuration files
2. Update any documentation or examples
3. Update export/logging formats

## Conclusion

The current implementation has **substantial misalignment** with the specified instruction requirements. While the underlying constraint validation logic is functionally sound, the presentation format, exact wording, and constraint handling approach differ significantly from the specification.

**Most Critical Issue**: The automatic provision of default constraint values directly contradicts the specification requirement that agents must explicitly provide constraints for principles (c) and (d) to make a "well-defined choice."

To achieve full compliance, systematic updates across multiple files would be required, with the constraint default handling being the highest priority fix due to its direct violation of the specification requirements.