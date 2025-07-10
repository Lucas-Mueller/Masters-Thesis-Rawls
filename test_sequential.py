#!/usr/bin/env python3
"""
Quick test of the sequential deliberation system with memory updates.
"""

import asyncio
from src.maai.core.models import ExperimentConfig
from src.maai.core.deliberation_manager import run_single_experiment

async def test_sequential_system():
    """Test the sequential system with a minimal configuration."""
    
    # Create minimal test configuration
    config = ExperimentConfig(
        experiment_id="sequential_test",
        num_agents=3,  # Minimal number of agents
        max_rounds=2,  # Just 2 rounds to test quickly  
        decision_rule="unanimity",
        timeout_seconds=60,  # Shorter timeout
        models=["anthropic", "gpt-4o", "deepseek"],
        personalities=[
            "You are an economist focused on efficiency.",
            "You are a philosopher concerned with fairness.", 
            "You are a pragmatist focused on practical solutions."
        ]
    )
    
    print("Starting sequential system test...")
    print(f"Config: {config.num_agents} agents, {config.max_rounds} rounds")
    
    try:
        # Run the experiment
        results = await run_single_experiment(config)
        print(f"✅ Test completed successfully!")
        print(f"Consensus reached: {results.consensus_result.unanimous}")
        print(f"Total rounds: {results.consensus_result.rounds_to_consensus}")
        print(f"Agent memories collected: {len(results.agent_memories)}")
        print(f"Speaking orders recorded: {len(results.speaking_orders)}")
        
        # Check that memories were created
        for memory in results.agent_memories:
            print(f"Agent {memory.agent_id}: {len(memory.memory_entries)} memory entries")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sequential_system())
    if success:
        print("\n🎉 Sequential system test PASSED!")
    else:
        print("\n💥 Sequential system test FAILED!")