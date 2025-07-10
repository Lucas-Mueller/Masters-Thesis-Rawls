#!/usr/bin/env python3
"""
Test runner script for validating the MAAI framework installation.
"""

import sys
import os
import subprocess

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_test_file(test_file):
    """Run a specific test file and return success status."""
    try:
        print(f"\n{'='*60}")
        print(f"Running {test_file}")
        print('='*60)
        
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=False, 
                              cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print(f"✅ {test_file}: PASSED")
            return True
        else:
            print(f"❌ {test_file}: FAILED")
            return False
    except Exception as e:
        print(f"❌ {test_file}: ERROR - {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 MAAI Framework Test Suite")
    print("=" * 60)
    
    # Define test files
    test_files = [
        "tests/test_core.py"
    ]
    
    # Check if API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set.")
        print("   Some tests will be skipped.")
        print("   Set your API key: export OPENAI_API_KEY='your-key-here'")
    
    # Run tests
    results = []
    for test_file in test_files:
        if os.path.exists(test_file):
            success = run_test_file(test_file)
            results.append((test_file, success))
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results.append((test_file, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_file, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_file}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your installation is working correctly.")
        return 0
    else:
        print("🔧 Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())