#!/usr/bin/env python3
"""
Comprehensive test runner for the MAAI framework.
Runs all tests and provides detailed coverage reporting.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_test_file(test_file, verbose=False):
    """Run a specific test file and return detailed results."""
    start_time = time.time()
    
    try:
        print(f"\n{'='*60}")
        print(f"Running {test_file}")
        print('='*60)
        
        if verbose:
            result = subprocess.run([sys.executable, test_file], 
                                  capture_output=False, 
                                  cwd=os.path.dirname(__file__))
        else:
            result = subprocess.run([sys.executable, test_file], 
                                  capture_output=True, 
                                  cwd=os.path.dirname(__file__),
                                  text=True)
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_file}: PASSED ({duration:.2f}s)")
            return {
                'file': test_file,
                'status': 'PASSED',
                'duration': duration,
                'returncode': result.returncode,
                'stdout': result.stdout if not verbose else '',
                'stderr': result.stderr if not verbose else ''
            }
        else:
            print(f"❌ {test_file}: FAILED ({duration:.2f}s)")
            if not verbose and result.stderr:
                print(f"Error output: {result.stderr}")
            return {
                'file': test_file,
                'status': 'FAILED',
                'duration': duration,
                'returncode': result.returncode,
                'stdout': result.stdout if not verbose else '',
                'stderr': result.stderr if not verbose else ''
            }
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ {test_file}: ERROR - {e} ({duration:.2f}s)")
        return {
            'file': test_file,
            'status': 'ERROR',
            'duration': duration,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e)
        }

def discover_test_files():
    """Discover all test files in the tests directory."""
    test_dir = Path(__file__).parent
    test_files = []
    
    for file_path in test_dir.glob("test_*.py"):
        if file_path.name != "test_all.py":  # Skip this file itself
            test_files.append(file_path.name)
    
    return sorted(test_files)

def run_with_pytest():
    """Run tests using pytest if available."""
    try:
        import pytest
        print("🧪 Running tests with pytest...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            os.path.dirname(__file__), 
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print("PYTEST OUTPUT:")
        print(result.stdout)
        if result.stderr:
            print("PYTEST ERRORS:")
            print(result.stderr)
        
        return result.returncode == 0
    except ImportError:
        print("⚠️  pytest not available, falling back to direct execution")
        return False

def main():
    """Run all tests with comprehensive reporting."""
    print("🧪 MAAI Framework Comprehensive Test Suite")
    print("=" * 60)
    
    # Check if API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set.")
        print("   Some tests may be skipped or fail.")
        print("   Set your API key: export OPENAI_API_KEY='your-key-here'")
        print()
    
    # Parse command line arguments
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    use_pytest = "--pytest" in sys.argv
    
    if use_pytest:
        success = run_with_pytest()
        return 0 if success else 1
    
    # Discover test files
    test_files = discover_test_files()
    
    if not test_files:
        print("⚠️  No test files found!")
        return 1
    
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {test_file}")
    print()
    
    # Run tests
    results = []
    total_start_time = time.time()
    
    for test_file in test_files:
        if os.path.exists(test_file):
            result = run_test_file(test_file, verbose)
            results.append(result)
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results.append({
                'file': test_file,
                'status': 'NOT_FOUND',
                'duration': 0,
                'returncode': -1,
                'stdout': '',
                'stderr': f'File not found: {test_file}'
            })
    
    total_duration = time.time() - total_start_time
    
    # Generate detailed summary
    print(f"\n{'='*60}")
    print("COMPREHENSIVE TEST SUMMARY")
    print('='*60)
    
    passed_count = sum(1 for r in results if r['status'] == 'PASSED')
    failed_count = sum(1 for r in results if r['status'] == 'FAILED')
    error_count = sum(1 for r in results if r['status'] == 'ERROR')
    not_found_count = sum(1 for r in results if r['status'] == 'NOT_FOUND')
    
    print(f"Total tests: {len(results)}")
    print(f"✅ Passed: {passed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"💥 Errors: {error_count}")
    print(f"❓ Not found: {not_found_count}")
    print(f"⏱️  Total duration: {total_duration:.2f}s")
    print()
    
    # Detailed results
    for result in results:
        status_emoji = {
            'PASSED': '✅',
            'FAILED': '❌',
            'ERROR': '💥',
            'NOT_FOUND': '❓'
        }.get(result['status'], '❓')
        
        print(f"{status_emoji} {result['file']:<35} {result['status']:<10} ({result['duration']:.2f}s)")
        
        if result['status'] in ['FAILED', 'ERROR'] and result['stderr']:
            print(f"   Error: {result['stderr'][:100]}...")
    
    # Performance analysis
    if results:
        print(f"\n{'='*60}")
        print("PERFORMANCE ANALYSIS")
        print('='*60)
        
        slowest_tests = sorted(results, key=lambda x: x['duration'], reverse=True)[:3]
        print("Slowest tests:")
        for test in slowest_tests:
            print(f"  - {test['file']}: {test['duration']:.2f}s")
        
        avg_duration = sum(r['duration'] for r in results) / len(results)
        print(f"Average test duration: {avg_duration:.2f}s")
    
    # Coverage suggestions
    print(f"\n{'='*60}")
    print("COVERAGE RECOMMENDATIONS")
    print('='*60)
    
    expected_tests = [
        "test_consensus_service.py",
        "test_conversation_service.py", 
        "test_evaluation_service.py",
        "test_experiment_orchestrator.py",
        "test_data_export.py",
        "test_agents.py"
    ]
    
    missing_tests = [t for t in expected_tests if t not in test_files]
    if missing_tests:
        print("Missing critical test files:")
        for test in missing_tests:
            print(f"  - {test}")
    else:
        print("✅ All critical test files present!")
    
    # Final result
    print(f"\n{'='*60}")
    if passed_count == len(results) and len(results) > 0:
        print("🎉 ALL TESTS PASSED! Your framework is working correctly.")
        return 0
    else:
        print("🔧 Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())