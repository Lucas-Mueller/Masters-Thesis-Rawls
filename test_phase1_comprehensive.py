"""
Comprehensive test for Phase 1 implementation with more scenarios.
"""

import asyncio
import os
import uuid

from models import ExperimentConfig
from deliberation_manager import run_single_experiment


async def test_multi_round_experiment():
    """Test an experiment that requires multiple rounds."""
    print("=== Testing Multi-Round Experiment ===\n")
    
    # Create configuration with more agents to increase chance of disagreement
    config = ExperimentConfig(
        experiment_id=f"multi_round_test_{uuid.uuid4().hex[:8]}",
        num_agents=4,
        max_rounds=3,
        decision_rule="unanimity",
        timeout_seconds=180,
        models=["gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini"]
    )
    
    print(f"Running experiment: {config.experiment_id}")
    print(f"Agents: {config.num_agents}")
    print(f"Max rounds: {config.max_rounds}")
    
    try:
        results = await run_single_experiment(config)
        
        print(f"\n--- Results ---")
        print(f"Consensus reached: {results.consensus_result.unanimous}")
        print(f"Rounds completed: {results.consensus_result.rounds_to_consensus}")
        print(f"Total messages: {len(results.deliberation_transcript)}")
        print(f"Duration: {results.performance_metrics.total_duration_seconds:.1f}s")
        print(f"Avg round duration: {results.performance_metrics.average_round_duration:.1f}s")
        
        if results.consensus_result.unanimous:
            principle = results.consensus_result.agreed_principle
            print(f"Agreed principle: {principle.principle_id} - {principle.principle_name}")
        
        # Analyze transcript
        round_counts = {}
        for response in results.deliberation_transcript:
            round_counts[response.round_number] = round_counts.get(response.round_number, 0) + 1
        
        print(f"\n--- Transcript Analysis ---")
        for round_num, count in sorted(round_counts.items()):
            round_name = "Initial Evaluation" if round_num == 0 else f"Round {round_num}"
            print(f"{round_name}: {count} messages")
        
        # Show principle choices by round
        print(f"\n--- Choice Evolution ---")
        for round_num in sorted(round_counts.keys()):
            round_responses = [r for r in results.deliberation_transcript if r.round_number == round_num]
            choices = [r.updated_choice.principle_id for r in round_responses]
            round_name = "Initial" if round_num == 0 else f"Round {round_num}"
            print(f"{round_name}: {choices}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_timeout_scenario():
    """Test what happens when maximum rounds are reached."""
    print("\n=== Testing Timeout Scenario ===\n")
    
    # Create configuration with very limited rounds
    config = ExperimentConfig(
        experiment_id=f"timeout_test_{uuid.uuid4().hex[:8]}",
        num_agents=3,  # Minimum agents required
        max_rounds=1,  # Only 1 round after initial evaluation
        decision_rule="unanimity",
        timeout_seconds=60,
        models=["gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini"]
    )
    
    print(f"Running experiment: {config.experiment_id}")
    print(f"Max rounds: {config.max_rounds} (very limited)")
    
    try:
        results = await run_single_experiment(config)
        
        print(f"\n--- Results ---")
        print(f"Consensus reached: {results.consensus_result.unanimous}")
        print(f"Rounds completed: {results.consensus_result.rounds_to_consensus}")
        
        if not results.consensus_result.unanimous:
            print(f"✓ Successfully handled no consensus scenario")
            print(f"Dissenting agents: {results.consensus_result.dissenting_agents}")
        else:
            print(f"⚠️  Consensus reached despite limited rounds")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_data_integrity():
    """Test data integrity and structure."""
    print("\n=== Testing Data Integrity ===\n")
    
    config = ExperimentConfig(
        experiment_id=f"data_test_{uuid.uuid4().hex[:8]}",
        num_agents=3,
        max_rounds=2,
        decision_rule="unanimity",
        timeout_seconds=90
    )
    
    try:
        results = await run_single_experiment(config)
        
        # Test 1: Basic structure
        print("1. Testing basic structure...")
        assert hasattr(results, 'experiment_id')
        assert hasattr(results, 'deliberation_transcript')
        assert hasattr(results, 'consensus_result')
        assert hasattr(results, 'performance_metrics')
        print("   ✓ Basic structure OK")
        
        # Test 2: Transcript integrity
        print("2. Testing transcript integrity...")
        assert len(results.deliberation_transcript) > 0
        for response in results.deliberation_transcript:
            assert response.agent_id is not None
            assert response.agent_name is not None
            assert response.updated_choice is not None
            assert 1 <= response.updated_choice.principle_id <= 4
        print("   ✓ Transcript integrity OK")
        
        # Test 3: Consensus result
        print("3. Testing consensus result...")
        assert results.consensus_result.rounds_to_consensus >= 0
        assert results.consensus_result.total_messages >= 0
        if results.consensus_result.unanimous:
            assert results.consensus_result.agreed_principle is not None
        print("   ✓ Consensus result OK")
        
        # Test 4: Performance metrics
        print("4. Testing performance metrics...")
        assert results.performance_metrics.total_duration_seconds > 0
        assert results.performance_metrics.average_round_duration > 0
        print("   ✓ Performance metrics OK")
        
        print("\n✓ All data integrity tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Data integrity error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run comprehensive Phase 1 tests."""
    print("Comprehensive Phase 1 Testing Suite")
    print("=" * 60)
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Error: OPENAI_API_KEY required for comprehensive tests")
        return
    
    test_results = []
    
    # Test 1: Multi-round experiment
    print("Test 1: Multi-Round Deliberation")
    result1 = await test_multi_round_experiment()
    test_results.append(("Multi-Round Experiment", result1))
    
    # Test 2: Timeout scenario
    print("\nTest 2: Timeout Handling")
    result2 = await test_timeout_scenario()
    test_results.append(("Timeout Scenario", result2))
    
    # Test 3: Data integrity
    print("\nTest 3: Data Integrity")
    result3 = await test_data_integrity()
    test_results.append(("Data Integrity", result3))
    
    # Summary
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in test_results:
        if result:
            print(f"✓ {test_name}: PASSED")
        else:
            print(f"✗ {test_name}: FAILED")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All comprehensive tests passed! Phase 1 is robust and ready.")
    else:
        print("🔧 Some tests failed. Please review the errors above.")


if __name__ == "__main__":
    asyncio.run(main())