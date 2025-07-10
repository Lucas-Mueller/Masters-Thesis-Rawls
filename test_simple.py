#!/usr/bin/env python3
"""
Very simple test to check if basic components work.
"""

from src.maai.core.models import ExperimentConfig, AgentMemory, MemoryEntry
from src.maai.core.deliberation_manager import DeliberationManager
from datetime import datetime

def test_basic_components():
    """Test basic data model creation and manager initialization."""
    
    print("Testing basic components...")
    
    # Test AgentMemory creation
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
    
    print(f"✅ AgentMemory created with {len(memory.memory_entries)} entries")
    
    # Test ExperimentConfig creation
    config = ExperimentConfig(
        experiment_id="simple_test",
        num_agents=3,  # Minimum required is 3
        max_rounds=1,
        models=["anthropic", "gpt-4o", "deepseek"],
        personalities=["Test personality 1", "Test personality 2", "Test personality 3"]
    )
    
    print(f"✅ ExperimentConfig created: {config.experiment_id}")
    
    # Test DeliberationManager initialization
    manager = DeliberationManager(config)
    print(f"✅ DeliberationManager created with {len(manager.agents)} agents")
    print(f"✅ Agent memories initialized: {len(manager.agent_memories)}")
    
    return True

if __name__ == "__main__":
    try:
        success = test_basic_components()
        if success:
            print("\n🎉 Basic components test PASSED!")
        else:
            print("\n💥 Basic components test FAILED!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()