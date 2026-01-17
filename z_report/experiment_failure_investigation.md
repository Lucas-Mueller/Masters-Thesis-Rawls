# Experiment Failure Investigation Report

**Date:** July 24, 2025  
**Issue:** Experiment completes immediately in 0.0 seconds with no actual processing  
**Reporter:** Claude Code  

## Executive Summary

The experiment appears to complete successfully but actually fails silently during configuration loading. The runner catches the exception and returns a standardized error result that appears as a "successful" completion, masking the underlying configuration errors.

## Root Cause Analysis

### Primary Issue: Configuration Path Resolution
The `test.py` script passes `config_path="test_lucas/test"` to `run_experiment()`, but the config loading system expects:
- **Config name:** `test` 
- **Config directory:** `test_lucas`

However, the current implementation tries to load from the default `configs/` directory, causing a path resolution failure.

### Secondary Issue: Invalid IncomeClass Values
The `test.yaml` configuration uses uppercase income class keys (`HIGH`, `MEDIUM_HIGH`, etc.) but the `IncomeClass` enum expects proper case:
- ❌ `HIGH` → ✅ `"High"`
- ❌ `MEDIUM_HIGH` → ✅ `"Medium high"`
- ❌ `MEDIUM` → ✅ `"Medium"`
- ❌ `MEDIUM_LOW` → ✅ `"Medium low"`
- ❌ `LOW` → ✅ `"Low"`

### Tertiary Issue: Silent Error Handling
The `run_experiment()` function in `src/maai/runners/single.py` catches all exceptions and returns a "success" result via `create_error_result()`, which creates a false positive completion signal.

## Detailed Investigation

### Step 1: Config Loading Failure
```python
# This fails silently:
config = load_config_from_file('test_lucas/test', config_dir='configs')  # Wrong directory
```

**Error Message (hidden):**
```
Configuration file not found: test.yaml
Available configurations: []
```

### Step 2: IncomeClass Validation Failure  
```python
# Even if path was correct, this would fail:
income_distributions:
  - income_by_class:
      HIGH: 32000  # ❌ Invalid - should be "High"
```

**Error Message (hidden):**
```
'HIGH' is not a valid IncomeClass
```

### Step 3: Silent Error Masking
The exception handler in `single.py:82` calls `create_error_result()` which returns:
```python
{
    "success": False,  # But test.py doesn't check this field!
    "experiment_id": "test_lucas/test",
    "consensus_reached": False,
    "duration_seconds": 0.0,
    "output_path": None,
    # ... other default values
}
```

However, `test.py` doesn't check the `success` field, only looks for the presence of `experiment_id`.

## Evidence

### Test Output Analysis
```
Duration: 0.0 seconds          # ← Immediate completion
Experiment ID: test_lucas/test # ← Returns config path, not actual ID
Consensus Reached: False       # ← Default value from error result
Output Path: None              # ← No file created
```

### File System Evidence
```bash
$ ls -la experiment_results/
total 0  # ← No files created
```

### Configuration Validation
Direct config loading test confirms both path and validation errors:
```python
config = load_config_from_file('test_lucas/test', config_dir='.')
# FileNotFoundError: Configuration file not found

config = load_config_from_file('test_lucas/test', config_dir='test_lucas')  
# ValueError: 'HIGH' is not a valid IncomeClass
```

## Impact Assessment

### Functional Impact
- **High:** Experiment doesn't run at all
- **High:** No error indication to user
- **High:** False positive success reporting

### User Experience Impact
- **High:** Confusing output suggests success when failure occurred
- **Medium:** No clear guidance on what went wrong
- **Medium:** No actual experiment results or data generated

### Development Impact
- **High:** Silent failures make debugging difficult
- **Medium:** Multiple configuration issues compound the problem
- **Low:** Error handling masks root causes

## Recommended Fixes

### Fix 1: Correct Configuration Path Handling
**File:** `test.py`
```python
# Current (incorrect):
result = await run_experiment(
    config_path="test_lucas/test", 
    output_dir="experiment_results"
)

# Fixed:
result = await run_experiment(
    config_path="test", 
    output_dir="experiment_results",
    config_dir="test_lucas"  # Pass config directory explicitly
)
```

### Fix 2: Fix IncomeClass Values in Configuration
**File:** `test_lucas/test.yaml`
```yaml
# Current (incorrect):
income_by_class:
  HIGH: 32000
  MEDIUM_HIGH: 27000
  MEDIUM: 24000
  MEDIUM_LOW: 13000
  LOW: 12000

# Fixed:
income_by_class:
  High: 32000
  Medium high: 27000
  Medium: 24000
  Medium low: 13000
  Low: 12000
```

### Fix 3: Improve Error Detection in Test Script
**File:** `test.py`
```python
# Add success checking:
if not result.get("success", True):
    print(f"❌ Experiment failed: {result.get('error', 'Unknown error')}")
    return False

# Also check for None output_path:
if result.get("output_path") is None:
    print("⚠️  No output file generated - likely a configuration error")
```

### Fix 4: Improve Error Reporting in Runner
**File:** `src/maai/runners/single.py`
```python
# Add more detailed error logging before returning error result
except Exception as e:
    print(f"❌ Experiment failed: {str(e)}")
    return create_error_result(config_path, e)
```

## Verification Steps

### Step 1: Fix Configuration
1. Update income class values in `test.yaml`
2. Test config loading directly
3. Verify no validation errors

### Step 2: Fix Test Script
1. Update config path parameters
2. Add proper error checking
3. Test with corrected configuration

### Step 3: Verify End-to-End
1. Run complete experiment
2. Verify files are created
3. Confirm proper duration and results

## Prevention Measures

### Immediate
1. **Configuration validation:** Add pre-flight config validation
2. **Error visibility:** Make errors more visible in test scripts
3. **Documentation:** Update config examples with correct formats

### Long-term
1. **Schema validation:** Add JSON schema validation for YAML configs
2. **Config templates:** Generate config templates with correct enum values
3. **Error handling:** Improve error reporting throughout the system
4. **Testing:** Add integration tests for config loading and validation

## Conclusion

The experiment failure is caused by multiple configuration issues compounded by silent error handling. The fixes are straightforward but highlight the need for better error visibility and configuration validation in the system.

**Priority:** High - Prevents any experiments from running  
**Complexity:** Low - Simple configuration and path fixes  
**Risk:** Low - Changes are isolated and well-defined  

---
*Investigation completed successfully. Recommended fixes should resolve all identified issues.*