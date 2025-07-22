"""
Simple test for temperature configuration functionality.
Tests that temperature settings work correctly with the experiment system.
"""

import asyncio
import sys
import os
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maai.config.manager import load_config_from_file
from maai.services.experiment_orchestrator import ExperimentOrchestrator
from maai.agents.enhanced import create_deliberation_agents
from maai.core.models import ExperimentConfig, AgentConfig, DefaultConfig


def test_temperature_configuration_loading():
    """Test that temperature settings load correctly from models."""
    # Test agent config with temperature
    agent_config = AgentConfig(
        name="Test Agent",
        model="gpt-4.1-mini",
        temperature=0.0
    )
    assert agent_config.temperature == 0.0
    
    # Test default config with temperature
    default_config = DefaultConfig(
        personality="Test personality",
        model="gpt-4.1-mini",
        temperature=0.5
    )
    assert default_config.temperature == 0.5
    
    # Test experiment config with global temperature
    experiment_config = ExperimentConfig(
        experiment_id="test",
        agents=[agent_config],
        defaults=default_config,
        global_temperature=1.0
    )
    assert experiment_config.global_temperature == 1.0


def test_agent_creation_with_temperature():
    """Test that agents are created correctly with temperature settings."""
    # Create configs
    agent_configs = [
        AgentConfig(name="Agent1", temperature=0.0),
        AgentConfig(name="Agent2")  # No temperature specified
    ]
    
    defaults = DefaultConfig(temperature=0.5)
    global_temperature = 0.2
    
    # Create agents
    agents = create_deliberation_agents(
        agent_configs=agent_configs,
        defaults=defaults,
        global_temperature=global_temperature
    )
    
    # Verify agents were created
    assert len(agents) == 2
    assert agents[0].name == "Agent1"
    assert agents[1].name == "Agent2"
    
    # Verify model settings were applied (agents should always have model_settings)
    # Agent1 should have temperature=0.0 (agent-specific)
    assert agents[0].model_settings is not None
    assert agents[0].model_settings.temperature == 0.0
    
    # Agent2 should have temperature=0.5 (default)
    assert agents[1].model_settings is not None
    assert agents[1].model_settings.temperature == 0.5


def test_temperature_priority():
    """Test temperature priority: agent > default > global."""
    agent_configs = [
        AgentConfig(name="Agent1", temperature=0.1),  # Agent-specific
        AgentConfig(name="Agent2"),                   # Uses default
        AgentConfig(name="Agent3")                    # Uses default
    ]
    
    defaults = DefaultConfig(temperature=0.2)  # Default
    global_temperature = 0.3                   # Global (lowest priority)
    
    agents = create_deliberation_agents(
        agent_configs=agent_configs,
        defaults=defaults,
        global_temperature=global_temperature
    )
    
    # Agent1: agent-specific temperature
    assert agents[0].model_settings is not None
    assert agents[0].model_settings.temperature == 0.1
    
    # Agent2 & Agent3: default temperature (not global)
    assert agents[1].model_settings is not None
    assert agents[1].model_settings.temperature == 0.2
    
    assert agents[2].model_settings is not None
    assert agents[2].model_settings.temperature == 0.2


async def test_temperature_with_experiment():
    """Simple integration test that temperature settings work in experiments."""
    # Create a minimal test config with temperature
    config = ExperimentConfig(
        experiment_id="temperature_test",
        max_rounds=1,  # Minimal rounds for quick test
        agents=[
            AgentConfig(name="Agent1", model="gpt-4.1-mini", temperature=0.0),
            AgentConfig(name="Agent2", model="gpt-4.1-mini", temperature=0.0)
        ],
        defaults=DefaultConfig(model="gpt-4.1-mini"),
        global_temperature=0.0
    )
    
    # This test just verifies the experiment can run with temperature settings
    # We don't need to check output determinism - just that it doesn't crash
    try:
        orchestrator = ExperimentOrchestrator()
        result = await orchestrator.run_experiment(config)
        assert result is not None
        assert result.experiment_id == "temperature_test"
        print("✅ Temperature configuration works with experiments")
    except Exception as e:
        pytest.fail(f"Experiment failed with temperature settings: {e}")


if __name__ == "__main__":
    # Run basic tests
    print("Testing temperature configuration...")
    
    test_temperature_configuration_loading()
    print("✅ Configuration loading test passed")
    
    test_agent_creation_with_temperature()
    print("✅ Agent creation test passed")
    
    test_temperature_priority()
    print("✅ Temperature priority test passed")
    
    # Run async test
    try:
        asyncio.run(test_temperature_with_experiment())
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
    
    print("🎉 All temperature tests completed!")