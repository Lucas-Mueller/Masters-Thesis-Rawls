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

from maai.core.models import (
    ExperimentConfig, AgentMemory, MemoryEntry, PrincipleChoice, AgentConfig, DefaultConfig,
    IncomeDistribution, EconomicOutcome, PreferenceRanking, IncomeClass, CertaintyLevel
)
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
        
        # Test configuration with new format (including new game logic fields)
        sample_distributions = [
            IncomeDistribution(
                distribution_id=1,
                name="Test Distribution",
                income_by_class={
                    IncomeClass.HIGH: 30000,
                    IncomeClass.MEDIUM: 20000,
                    IncomeClass.LOW: 10000
                }
            )
        ]
        
        config = ExperimentConfig(
            experiment_id="test_basic",
            max_rounds=2,
            agents=[
                AgentConfig(name="Agent_1", model="gpt-4.1-mini", personality="Test 1"),
                AgentConfig(name="Agent_2", model="gpt-4.1-mini", personality="Test 2"),
                AgentConfig(name="Agent_3", model="gpt-4.1-mini", personality="Test 3")
            ],
            defaults=DefaultConfig(),
            # New game logic fields
            income_distributions=sample_distributions,
            payout_ratio=0.0001,
            individual_rounds=2,
            enable_detailed_examples=True,
            enable_secret_ballot=True
        )
        print(f"   ✓ ExperimentConfig created: {config.experiment_id}")
        print(f"   ✓ Agent configuration - num_agents: {config.num_agents}")
        print(f"   ✓ Agent configuration - agents defined: {len(config.agents)}")
        print(f"   ✓ Agent configuration - defaults available: {config.defaults.model}")
        
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
        config = load_config_from_file("new_game_basic")
        print(f"   ✓ Loaded new_game_basic config: {config.experiment_id}")
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
    
    # Create minimal config with new format including required new game logic fields
    sample_distributions = [
        IncomeDistribution(
            distribution_id=1,
            name="Test Distribution 1",
            income_by_class={
                IncomeClass.HIGH: 30000,
                IncomeClass.MEDIUM_HIGH: 25000,
                IncomeClass.MEDIUM: 20000,
                IncomeClass.MEDIUM_LOW: 15000,
                IncomeClass.LOW: 10000
            }
        ),
        IncomeDistribution(
            distribution_id=2,
            name="Test Distribution 2",
            income_by_class={
                IncomeClass.HIGH: 35000,
                IncomeClass.MEDIUM_HIGH: 28000,
                IncomeClass.MEDIUM: 22000,
                IncomeClass.MEDIUM_LOW: 16000,
                IncomeClass.LOW: 12000
            }
        )
    ]
    
    config = ExperimentConfig(
        experiment_id=f"test_{uuid.uuid4().hex[:8]}",
        max_rounds=2,
        decision_rule="unanimity",
        timeout_seconds=120,
        agents=[
            AgentConfig(name="Economist", model="gpt-4.1-mini", personality="You are an economist focused on efficiency."),
            AgentConfig(name="Philosopher", model="gpt-4.1-mini", personality="You are a philosopher concerned with fairness."),
            AgentConfig(name="Pragmatist", model="gpt-4.1-mini", personality="You are a pragmatist focused on practical solutions.")
        ],
        defaults=DefaultConfig(),
        # New game logic fields
        income_distributions=sample_distributions,
        payout_ratio=0.0001,
        individual_rounds=2,
        enable_detailed_examples=True,
        enable_secret_ballot=True
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


async def test_new_game_logic():
    """Test new game logic components."""
    print("=== Testing New Game Logic ===\n")
    
    print("1. Testing new data models...")
    try:
        # Test PreferenceRanking
        ranking = PreferenceRanking(
            agent_id="test_agent",
            rankings=[1, 2, 3, 4],
            certainty_level=CertaintyLevel.SURE,
            reasoning="Test ranking reasoning",
            phase="initial"
        )
        print(f"   ✓ PreferenceRanking created for phase: {ranking.phase}")
        
        # Test EconomicOutcome
        outcome = EconomicOutcome(
            agent_id="test_agent",
            round_number=1,
            chosen_principle=2,
            assigned_income_class=IncomeClass.MEDIUM,
            actual_income=20000,
            payout_amount=2.0
        )
        print(f"   ✓ EconomicOutcome created: ${outcome.actual_income:,} -> ${outcome.payout_amount:.2f}")
        
        # Test enhanced PrincipleChoice
        choice = PrincipleChoice(
            principle_id=3,
            principle_name="MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT",
            reasoning="Test choice with constraint",
            floor_constraint=15000
        )
        print(f"   ✓ Enhanced PrincipleChoice with floor constraint: ${choice.floor_constraint:,}")
        
        print("\n2. Testing new services...")
        
        # Test economics service
        from maai.services import EconomicsService
        sample_dist = IncomeDistribution(
            distribution_id=1,
            name="Test Distribution",
            income_by_class={
                IncomeClass.HIGH: 30000,
                IncomeClass.MEDIUM: 20000,
                IncomeClass.LOW: 10000
            }
        )
        
        economics_service = EconomicsService([sample_dist], 0.0001)
        payout = economics_service.calculate_payout(20000)
        print(f"   ✓ EconomicsService: $20,000 -> ${payout:.2f} payout")
        
        # Test validation service
        from maai.services import ValidationService
        validation_service = ValidationService()
        
        valid_choice = PrincipleChoice(
            principle_id=1,
            principle_name="MAXIMIZING THE FLOOR INCOME",
            reasoning="Valid choice"
        )
        result = validation_service.validate_principle_choice(valid_choice)
        print(f"   ✓ ValidationService: Valid choice = {result['is_valid']}")
        
        invalid_choice = PrincipleChoice(
            principle_id=3,
            principle_name="MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT", 
            reasoning="Missing constraint"
        )
        result = validation_service.validate_principle_choice(invalid_choice)
        print(f"   ✓ ValidationService: Invalid choice detected = {not result['is_valid']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in new game logic test: {e}")
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
    
    # Test 3: New game logic
    result3 = await test_new_game_logic()
    test_results.append(("New Game Logic", result3))
    
    # Test 4: Small experiment (if API key available)
    result4 = await test_small_experiment()
    test_results.append(("Small Experiment", result4))
    
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