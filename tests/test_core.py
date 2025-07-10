"""
Consolidated test suite for the MAAI framework.
Tests core functionality, configuration, and basic experiments.
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maai.core.models import ExperimentConfig, AgentMemory, MemoryEntry, PrincipleChoice
from maai.core.deliberation_manager import run_single_experiment, DeliberationManager
from maai.config.manager import load_config_from_file


async def test_basic_functionality():
    """Test basic data models and manager initialization."""
    print("=== Testing Basic Functionality ===\n")
    
    print("1. Testing data models...")
    try:
        # Test memory models
        memory = AgentMemory(agent_id="test_agent")
        memory_entry = MemoryEntry(
            round_number=1,
            timestamp=datetime.now(),
            situation_assessment="Test situation",
            other_agents_analysis="Test analysis", 
            strategy_update="Test strategy",
            speaking_position=1
        )
        memory.add_memory(memory_entry)
        print(f"   ✓ AgentMemory created with {len(memory.memory_entries)} entries")
        
        # Test configuration
        config = ExperimentConfig(
            experiment_id="test_basic",
            num_agents=3,
            max_rounds=2,
            models=["gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini"],
            personalities=["Test 1", "Test 2", "Test 3"]
        )
        print(f"   ✓ ExperimentConfig created: {config.experiment_id}")
        
        # Test manager initialization
        manager = DeliberationManager(config)
        print(f"   ✓ DeliberationManager created")
        
    except Exception as e:
        print(f"   ✗ Error in basic functionality: {e}")
        return False
    
    print("✓ Basic functionality tests passed!")
    return True


async def test_configuration_loading():
    """Test configuration loading from YAML files."""
    print("\n=== Testing Configuration Loading ===\n")
    
    try:
        # Test loading default config
        config = load_config_from_file("quick_test")
        print(f"   ✓ Loaded quick_test config: {config.experiment_id}")
        print(f"     Agents: {config.num_agents}")
        print(f"     Max rounds: {config.max_rounds}")
        
        return True
    except Exception as e:
        print(f"   ✗ Error loading configuration: {e}")
        return False


async def test_small_experiment():
    """Test a minimal experiment with 3 agents."""
    print("\n=== Testing Small Experiment ===\n")
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Skipping experiment test (no API key)")
        return None
    
    # Create minimal config
    config = ExperimentConfig(
        experiment_id=f"test_{uuid.uuid4().hex[:8]}",
        num_agents=3,
        max_rounds=2,
        decision_rule="unanimity",
        timeout_seconds=120,
        models=["gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini"],
        personalities=[
            "You are an economist focused on efficiency.",
            "You are a philosopher concerned with fairness.",
            "You are a pragmatist focused on practical solutions."
        ]
    )
    
    print(f"Running experiment: {config.experiment_id}")
    
    try:
        results = await run_single_experiment(config)
        
        print(f"\n--- Results ---")
        print(f"Consensus reached: {results.consensus_result.unanimous}")
        print(f"Rounds: {results.consensus_result.rounds_to_consensus}")
        print(f"Messages: {len(results.deliberation_transcript)}")
        print(f"Duration: {results.performance_metrics.total_duration_seconds:.1f}s")
        print(f"Agent memories: {len(results.agent_memories)}")
        print(f"Speaking orders: {len(results.speaking_orders)}")
        
        if results.consensus_result.unanimous:
            principle = results.consensus_result.agreed_principle
            print(f"Agreed principle: {principle.principle_id} - {principle.principle_name}")
        
        print("✓ Small experiment completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error running experiment: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("MAAI Framework Test Suite")
    print("=" * 50)
    
    # Check environment
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Experiment tests will be skipped.")
    
    # Run tests
    test_results = []
    
    # Test 1: Basic functionality
    result1 = await test_basic_functionality()
    test_results.append(("Basic Functionality", result1))
    
    # Test 2: Configuration loading
    result2 = await test_configuration_loading()
    test_results.append(("Configuration Loading", result2))
    
    # Test 3: Small experiment (if API key available)
    result3 = await test_small_experiment()
    test_results.append(("Small Experiment", result3))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in test_results:
        if result is True:
            print(f"✓ {test_name}: PASSED")
        elif result is False:
            print(f"✗ {test_name}: FAILED")
        else:
            print(f"- {test_name}: SKIPPED")
    
    passed = sum(1 for _, result in test_results if result is True)
    total = len([r for r in test_results if r[1] is not None])
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total and total > 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("🔧 Some tests failed or were skipped.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)