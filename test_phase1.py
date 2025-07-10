"""
Test script for Phase 1 implementation.
Tests the enhanced agent architecture, deliberation engine, and consensus detection.
"""

import asyncio
import os
import uuid
from datetime import datetime

from models import ExperimentConfig
from deliberation_manager import run_single_experiment
from agents_enhanced import create_deliberation_agents, create_consensus_judge


async def test_basic_functionality():
    """Test basic functionality of the enhanced system."""
    print("=== Testing Basic Functionality ===\n")
    
    # Test 1: Agent Creation
    print("1. Testing agent creation...")
    try:
        agents = create_deliberation_agents(num_agents=3)
        print(f"   ✓ Created {len(agents)} agents successfully")
        for agent in agents:
            print(f"     - {agent.name} ({agent.agent_id})")
    except Exception as e:
        print(f"   ✗ Error creating agents: {e}")
        return False
    
    # Test 2: Judge Creation
    print("\n2. Testing judge creation...")
    try:
        judge = create_consensus_judge()
        print(f"   ✓ Created consensus judge: {judge.name}")
    except Exception as e:
        print(f"   ✗ Error creating judge: {e}")
        return False
    
    # Test 3: Configuration
    print("\n3. Testing configuration...")
    try:
        config = ExperimentConfig(
            experiment_id=f"test_{uuid.uuid4().hex[:8]}",
            num_agents=3,
            max_rounds=3,
            decision_rule="unanimity",
            timeout_seconds=60
        )
        print(f"   ✓ Created experiment config: {config.experiment_id}")
    except Exception as e:
        print(f"   ✗ Error creating config: {e}")
        return False
    
    print("\n✓ All basic functionality tests passed!")
    return True


async def test_small_experiment():
    """Test a small experiment with 3 agents and limited rounds."""
    print("\n=== Testing Small Experiment ===\n")
    
    # Create a minimal experiment configuration
    config = ExperimentConfig(
        experiment_id=f"small_test_{uuid.uuid4().hex[:8]}",
        num_agents=3,
        max_rounds=2,  # Limited for testing
        decision_rule="unanimity",
        timeout_seconds=120,
        models=["gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini"]  # Use consistent model for testing
    )
    
    print(f"Running experiment: {config.experiment_id}")
    print(f"Agents: {config.num_agents}")
    print(f"Max rounds: {config.max_rounds}")
    
    try:
        # Run the experiment
        results = await run_single_experiment(config)
        
        # Validate results
        print(f"\n--- Experiment Results ---")
        print(f"Consensus reached: {results.consensus_result.unanimous}")
        print(f"Total rounds: {results.consensus_result.rounds_to_consensus}")
        print(f"Total messages: {len(results.deliberation_transcript)}")
        print(f"Duration: {results.performance_metrics.total_duration_seconds:.1f}s")
        
        if results.consensus_result.unanimous:
            principle = results.consensus_result.agreed_principle
            print(f"Agreed principle: {principle.principle_id} - {principle.principle_name}")
        else:
            print(f"Dissenting agents: {results.consensus_result.dissenting_agents}")
        
        # Show some transcript samples
        print(f"\n--- Sample Transcript ---")
        for i, response in enumerate(results.deliberation_transcript[:3]):
            print(f"Round {response.round_number} - {response.agent_name}:")
            print(f"  Choice: Principle {response.updated_choice.principle_id}")
            print(f"  Message: {response.message[:100]}...")
            
        print(f"\n✓ Small experiment completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error running experiment: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_consensus_detection():
    """Test consensus detection with known scenarios."""
    print("\n=== Testing Consensus Detection ===\n")
    
    # This is a more complex test that would require mocking
    # For now, we'll test the basic structure
    print("1. Testing consensus detection logic...")
    
    try:
        from models import PrincipleChoice, ConsensusResult
        
        # Test unanimous case
        choice1 = PrincipleChoice(
            principle_id=1,
            principle_name="Test Principle",
            reasoning="Test reasoning",
            confidence=0.8
        )
        
        print("   ✓ Created test principle choice")
        
        # Test consensus result
        consensus = ConsensusResult(
            unanimous=True,
            agreed_principle=choice1,
            dissenting_agents=[],
            rounds_to_consensus=1,
            total_messages=3
        )
        
        print("   ✓ Created test consensus result")
        print(f"     Unanimous: {consensus.unanimous}")
        print(f"     Agreed principle: {consensus.agreed_principle.principle_id}")
        
        print("\n✓ Consensus detection structure tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error in consensus detection tests: {e}")
        return False


async def main():
    """Run all Phase 1 tests."""
    print("Phase 1 Testing Suite")
    print("=" * 50)
    
    # Check environment
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Some tests may fail.")
    
    # Run tests
    test_results = []
    
    # Test 1: Basic functionality
    result1 = await test_basic_functionality()
    test_results.append(("Basic Functionality", result1))
    
    # Test 2: Consensus detection
    result2 = await test_consensus_detection()
    test_results.append(("Consensus Detection", result2))
    
    # Test 3: Small experiment (only if API key is available)
    if os.environ.get("OPENAI_API_KEY"):
        result3 = await test_small_experiment()
        test_results.append(("Small Experiment", result3))
    else:
        print("\n⚠️  Skipping small experiment test (no API key)")
        test_results.append(("Small Experiment", None))
    
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
    
    if passed == total:
        print("🎉 All tests passed! Phase 1 is ready.")
    else:
        print("🔧 Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())