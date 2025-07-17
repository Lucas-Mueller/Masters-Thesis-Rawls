"""
Tests for config_generator.py
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config_generator import ProbabilisticConfigGenerator, create_test_generator


class TestConfigGenerator:
    
    def setup_method(self):
        """Setup test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir)
    
    def test_generate_configs_basic(self):
        """Test basic configuration generation."""
        
        # Create test generator
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        
        # Generate 3 test configurations
        config_paths = generator.generate_batch_configs(3, "test")
        
        # Check that 3 files were generated
        assert len(config_paths) == 3
        
        # Check that all files exist
        for path in config_paths:
            assert Path(path).exists()
        
        # Check that files follow naming pattern
        for i, path in enumerate(config_paths):
            filename = Path(path).name
            assert filename.startswith(f"test_{i+1:03d}_")
            assert filename.endswith(".yaml")
    
    def test_config_content_structure(self):
        """Test that generated configurations have correct structure."""
        
        # Create test generator
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        
        # Generate single config
        config_paths = generator.generate_batch_configs(1, "test")
        config_path = config_paths[0]
        
        # Load and verify structure
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required fields
        assert "experiment_id" in config
        assert "global_temperature" in config
        assert "experiment" in config
        assert "agents" in config
        assert "defaults" in config
        assert "output" in config
        assert "performance" in config
        
        # Check experiment section
        assert "max_rounds" in config["experiment"]
        assert "decision_rule" in config["experiment"]
        assert "timeout_seconds" in config["experiment"]
        
        # Check agents section - can be 2 or 3 agents based on probability
        assert len(config["agents"]) >= 2
        for agent in config["agents"]:
            assert "name" in agent
            assert "model" in agent
            assert "personality" in agent
            assert agent["model"] == "gpt-4.1-nano"
    
    def test_create_single_config(self):
        """Test creating a single configuration."""
        
        # Create test generator
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        
        # Generate single config
        config_path = generator.generate_and_save_config("test_minimal.yaml", "test_minimal")
        
        # Check file exists
        assert Path(config_path).exists()
        
        # Load and verify
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert config["experiment_id"] == "test_minimal"
        assert len(config["agents"]) >= 2
        assert config["experiment"]["max_rounds"] in [2, 3]
    
    def test_create_batch_configs(self):
        """Test creating multiple configurations for batch testing."""
        
        # Create test generator
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        
        # Create batch configs
        config_paths = generator.generate_batch_configs(3, "batch")
        
        # Check that 3 files were created
        assert len(config_paths) == 3
        
        # Check each file
        for i, path in enumerate(config_paths):
            assert Path(path).exists()
            
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
            
            assert config["experiment_id"].startswith(f"batch_{i+1:03d}_")
            assert len(config["agents"]) >= 2
            assert config["experiment"]["max_rounds"] in [2, 3]
    
    def test_config_variations(self):
        """Test that configurations have reasonable variations."""
        
        # Create test generator
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        
        # Generate multiple configs
        config_paths = generator.generate_batch_configs(5, "test")
        
        # Load all configs
        configs = []
        for path in config_paths:
            with open(path, 'r') as f:
                configs.append(yaml.safe_load(f))
        
        # Check that agent counts vary (probabilistic)
        agent_counts = [len(config["agents"]) for config in configs]
        assert all(count in [2, 3] for count in agent_counts)  # Should be 2 or 3
        
        # Check that max_rounds vary
        rounds = [config["experiment"]["max_rounds"] for config in configs]
        assert all(r in [2, 3] for r in rounds)  # Should be 2 or 3
        
        # Check that all use the same temperature (0.0 for reproducibility)
        temperatures = [config["global_temperature"] for config in configs]
        assert all(temp == 0.0 for temp in temperatures)
    
    def test_config_yaml_format(self):
        """Test that generated configs are valid YAML."""
        
        # Create test generator
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        
        # Generate configs
        config_paths = generator.generate_batch_configs(2, "test")
        
        for path in config_paths:
            # Should be able to load without errors
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Should be a dictionary
            assert isinstance(config, dict)
            
            # Should be able to dump back to YAML
            yaml_str = yaml.dump(config)
            assert isinstance(yaml_str, str)
            assert len(yaml_str) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])