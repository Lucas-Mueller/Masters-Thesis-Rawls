"""
Test script for Phase 2 feedback collection functionality.
"""

import asyncio
import os
import uuid
from datetime import datetime

from models import ExperimentConfig, FeedbackResponse
from deliberation_manager import run_single_experiment


async def test_feedback_collection():
    """Test the post-experiment feedback collection system."""
    print("=== Testing Feedback Collection System ===\n")
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        return False
    
    # Create a small experiment to test feedback
    config = ExperimentConfig(
        experiment_id=f"feedback_test_{uuid.uuid4().hex[:8]}",
        num_agents=3,
        max_rounds=2,
        decision_rule="unanimity",
        timeout_seconds=120,
        models=["gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini"]
    )
    
    print(f"Running experiment: {config.experiment_id}")
    print(f"Testing with {config.num_agents} agents")
    
    try:
        # Run the experiment
        results = await run_single_experiment(config)
        
        print(f"\n--- Experiment Results ---")
        print(f"Consensus reached: {results.consensus_result.unanimous}")
        print(f"Total rounds: {results.consensus_result.rounds_to_consensus}")
        print(f"Duration: {results.performance_metrics.total_duration_seconds:.1f}s")
        
        # Test feedback collection
        print(f"\n--- Feedback Collection Results ---")
        print(f"Feedback responses collected: {len(results.feedback_responses)}")
        
        if len(results.feedback_responses) == 0:
            print("❌ No feedback responses collected!")
            return False
        
        # Validate feedback structure
        for feedback in results.feedback_responses:
            print(f"\n🤖 {feedback.agent_name}:")
            print(f"   Satisfaction: {feedback.satisfaction_rating}/10")
            print(f"   Fairness: {feedback.fairness_rating}/10")
            print(f"   Would choose again: {feedback.would_choose_again}")
            print(f"   Alternative preference: {feedback.alternative_preference}")
            print(f"   Confidence: {feedback.confidence_in_feedback:.1%}")
            print(f"   Reasoning: {feedback.reasoning[:100]}...")
            
            # Validate data types and ranges
            assert isinstance(feedback.satisfaction_rating, int)
            assert 1 <= feedback.satisfaction_rating <= 10
            assert isinstance(feedback.fairness_rating, int)
            assert 1 <= feedback.fairness_rating <= 10
            assert isinstance(feedback.would_choose_again, bool)
            assert isinstance(feedback.confidence_in_feedback, float)
            assert 0.0 <= feedback.confidence_in_feedback <= 1.0
            
            if feedback.alternative_preference is not None:
                assert 1 <= feedback.alternative_preference <= 4
        
        print(f"\n✅ Feedback collection test passed!")
        print(f"   Collected {len(results.feedback_responses)} valid feedback responses")
        print(f"   All data validation checks passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Feedback collection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_feedback_data_structure():
    """Test the FeedbackResponse data structure."""
    print("\n=== Testing Feedback Data Structure ===\n")
    
    try:
        # Test valid feedback response
        feedback = FeedbackResponse(
            agent_id="test_agent",
            agent_name="Test Agent",
            satisfaction_rating=8,
            fairness_rating=7,
            would_choose_again=True,
            alternative_preference=2,
            reasoning="This principle seems most fair because...",
            confidence_in_feedback=0.85
        )
        
        print("✅ Valid feedback response created successfully")
        print(f"   Agent: {feedback.agent_name}")
        print(f"   Satisfaction: {feedback.satisfaction_rating}/10")
        print(f"   Fairness: {feedback.fairness_rating}/10")
        print(f"   Would choose again: {feedback.would_choose_again}")
        print(f"   Alternative: Principle {feedback.alternative_preference}")
        print(f"   Confidence: {feedback.confidence_in_feedback:.1%}")
        
        # Test validation - satisfaction out of range
        try:
            invalid_feedback = FeedbackResponse(
                agent_id="test_agent",
                agent_name="Test Agent",
                satisfaction_rating=15,  # Invalid - should be 1-10
                fairness_rating=7,
                would_choose_again=True,
                reasoning="Test reasoning",
                confidence_in_feedback=0.8
            )
            print("❌ Validation failed - should have rejected rating > 10")
            return False
        except Exception:
            print("✅ Validation correctly rejected satisfaction rating > 10")
        
        # Test validation - confidence out of range
        try:
            invalid_feedback = FeedbackResponse(
                agent_id="test_agent", 
                agent_name="Test Agent",
                satisfaction_rating=8,
                fairness_rating=7,
                would_choose_again=True,
                reasoning="Test reasoning",
                confidence_in_feedback=1.5  # Invalid - should be 0-1
            )
            print("❌ Validation failed - should have rejected confidence > 1.0")
            return False
        except Exception:
            print("✅ Validation correctly rejected confidence > 1.0")
        
        print("\n✅ Feedback data structure tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Feedback data structure test failed: {e}")
        return False


async def main():
    """Run all Phase 2 feedback tests."""
    print("Phase 2 Feedback Collection Testing Suite")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Data structure validation
    print("Test 1: Data Structure Validation")
    result1 = await test_feedback_data_structure()
    test_results.append(("Data Structure", result1))
    
    # Test 2: Feedback collection integration
    if os.environ.get("OPENAI_API_KEY"):
        print("\nTest 2: Feedback Collection Integration")
        result2 = await test_feedback_collection()
        test_results.append(("Feedback Collection", result2))
    else:
        print("\n⚠️  Skipping feedback collection test (no API key)")
        test_results.append(("Feedback Collection", None))
    
    # Summary
    print("\n" + "=" * 60)
    print("PHASE 2 FEEDBACK TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in test_results:
        if result is True:
            print(f"✅ {test_name}: PASSED")
        elif result is False:
            print(f"❌ {test_name}: FAILED")
        else:
            print(f"⚠️  {test_name}: SKIPPED")
    
    passed = sum(1 for _, result in test_results if result is True)
    total = len([r for r in test_results if r[1] is not None])
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 2 feedback tests passed!")
    else:
        print("🔧 Some tests failed. Please review the errors above.")


if __name__ == "__main__":
    asyncio.run(main())