"""
Test script for Phase 2 configuration management functionality.
"""

import os
import yaml
import tempfile
from pathlib import Path

from config_manager import ConfigManager, PresetConfigs, load_config_from_file
from models import ExperimentConfig


def test_config_manager():
    """Test the ConfigManager class."""
    print("=== Testing ConfigManager ===\n")
    
    try:
        # Test 1: Create config manager
        print("1. Testing ConfigManager creation...")
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(temp_dir)
            print(f"   ✓ Created ConfigManager with directory: {temp_dir}")
            
            # Check default config was created
            default_path = Path(temp_dir) / "default.yaml"
            assert default_path.exists(), "Default config file not created"
            print("   ✓ Default config file created")
        
        # Test 2: Load default config
        print("\n2. Testing default config loading...")
        manager = ConfigManager()
        config = manager.load_config("default")
        assert isinstance(config, ExperimentConfig), "Config is not ExperimentConfig"
        assert config.num_agents >= 3, "Invalid number of agents"
        assert config.max_rounds >= 1, "Invalid max rounds"
        print(f"   ✓ Loaded default config: {config.num_agents} agents, {config.max_rounds} rounds")
        
        # Test 3: List configs
        print("\n3. Testing config listing...")
        configs = manager.list_configs()
        assert "default" in configs, "Default config not in list"
        print(f"   ✓ Found configs: {configs}")
        
        # Test 4: Save and load custom config
        print("\n4. Testing custom config save/load...")
        custom_config = ExperimentConfig(
            experiment_id="test_config",
            num_agents=5,
            max_rounds=3,
            decision_rule="unanimity",
            timeout_seconds=120
        )
        
        manager.save_config(custom_config, "test_custom")
        loaded_config = manager.load_config("test_custom")
        
        assert loaded_config.num_agents == 5, "Custom config not saved correctly"
        assert loaded_config.max_rounds == 3, "Custom config not saved correctly"
        print("   ✓ Custom config saved and loaded correctly")
        
        # Test 5: Environment variable override
        print("\n5. Testing environment variable overrides...")
        os.environ["MAAI_NUM_AGENTS"] = "7"
        os.environ["MAAI_MAX_ROUNDS"] = "8"
        
        env_config = manager.load_config("default")
        assert env_config.num_agents == 7, "Environment override failed"
        assert env_config.max_rounds == 8, "Environment override failed"
        print("   ✓ Environment variable overrides working")
        
        # Clean up environment
        del os.environ["MAAI_NUM_AGENTS"]
        del os.environ["MAAI_MAX_ROUNDS"]
        
        print("\n✅ All ConfigManager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ ConfigManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preset_configs():
    """Test preset configuration functions."""
    print("\n=== Testing Preset Configurations ===\n")
    
    try:
        # Test all preset configs
        presets = [
            ("Quick Test", PresetConfigs.quick_test),
            ("Standard Experiment", PresetConfigs.standard_experiment),
            ("Large Group", PresetConfigs.large_group),
            ("Stress Test", PresetConfigs.stress_test)
        ]
        
        for name, preset_func in presets:
            print(f"Testing {name}...")
            config = preset_func()
            
            assert isinstance(config, ExperimentConfig), f"{name} not ExperimentConfig"
            assert config.num_agents >= 3, f"{name} has invalid agent count"
            assert config.max_rounds >= 1, f"{name} has invalid round count"
            assert config.timeout_seconds > 0, f"{name} has invalid timeout"
            
            print(f"   ✓ {name}: {config.num_agents} agents, {config.max_rounds} rounds, {config.timeout_seconds}s timeout")
        
        print("\n✅ All preset configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Preset config test failed: {e}")
        return False


def test_yaml_config_files():
    """Test loading from YAML configuration files."""
    print("\n=== Testing YAML Configuration Files ===\n")
    
    try:
        config_files = ["quick_test", "multi_model", "large_group"]
        
        for config_name in config_files:
            print(f"Testing {config_name} config...")
            
            # Test if file exists
            config_path = Path("configs") / f"{config_name}.yaml"
            if not config_path.exists():
                print(f"   ⚠️  Config file not found: {config_path}")
                continue
            
            # Load and validate config
            try:
                config = load_config_from_file(config_name)
                assert isinstance(config, ExperimentConfig), f"{config_name} not ExperimentConfig"
                print(f"   ✓ {config_name}: {config.num_agents} agents, {config.max_rounds} rounds")
                
                # Validate specific configurations
                if config_name == "quick_test":
                    assert config.num_agents == 3, "Quick test should have 3 agents"
                    assert config.max_rounds == 2, "Quick test should have 2 rounds"
                elif config_name == "large_group":
                    assert config.num_agents == 8, "Large group should have 8 agents"
                    assert config.max_rounds == 10, "Large group should have 10 rounds"
                
            except Exception as e:
                print(f"   ❌ Failed to load {config_name}: {e}")
                return False
        
        print("\n✅ All YAML configuration file tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ YAML config test failed: {e}")
        return False


def test_config_validation():
    """Test configuration validation."""
    print("\n=== Testing Configuration Validation ===\n")
    
    try:
        manager = ConfigManager()
        
        # Test valid config
        print("1. Testing valid config validation...")
        validation = manager.validate_config("default")
        assert validation["valid"], "Default config should be valid"
        assert len(validation["errors"]) == 0, "Valid config should have no errors"
        print("   ✓ Valid config passed validation")
        
        # Test invalid config (create temp invalid config)
        print("\n2. Testing invalid config validation...")
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_config_path = Path(temp_dir) / "invalid.yaml"
            
            # Create invalid config (num_agents < 3)
            invalid_data = {
                "experiment": {
                    "num_agents": 2,  # Invalid - too few
                    "max_rounds": 5,
                    "decision_rule": "unanimity",
                    "timeout_seconds": 300,
                    "models": ["gpt-4.1-mini", "gpt-4.1-mini"]
                }
            }
            
            with open(invalid_config_path, 'w') as f:
                yaml.dump(invalid_data, f)
            
            # Create temporary manager for this test
            temp_manager = ConfigManager(temp_dir)
            temp_manager.config_dir = Path(temp_dir)
            
            validation = temp_manager.validate_config("invalid")
            assert not validation["valid"], "Invalid config should fail validation"
            assert len(validation["errors"]) > 0, "Invalid config should have errors"
            print(f"   ✓ Invalid config correctly failed validation: {validation['errors'][0]}")
        
        print("\n✅ All configuration validation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Config validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 2 configuration tests."""
    print("Phase 2 Configuration Management Testing Suite")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: ConfigManager functionality
    print("Test 1: ConfigManager Functionality")
    result1 = test_config_manager()
    test_results.append(("ConfigManager", result1))
    
    # Test 2: Preset configurations
    print("\nTest 2: Preset Configurations")
    result2 = test_preset_configs()
    test_results.append(("Preset Configs", result2))
    
    # Test 3: YAML configuration files
    print("\nTest 3: YAML Configuration Files")
    result3 = test_yaml_config_files()
    test_results.append(("YAML Configs", result3))
    
    # Test 4: Configuration validation
    print("\nTest 4: Configuration Validation")
    result4 = test_config_validation()
    test_results.append(("Config Validation", result4))
    
    # Summary
    print("\n" + "=" * 60)
    print("PHASE 2 CONFIG TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in test_results:
        if result:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 2 configuration tests passed!")
    else:
        print("🔧 Some tests failed. Please review the errors above.")


if __name__ == "__main__":
    main()