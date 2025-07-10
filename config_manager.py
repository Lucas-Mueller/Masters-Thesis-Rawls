"""
Configuration management system for the Multi-Agent Distributive Justice Experiment.
Supports YAML configuration files and environment variable overrides.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from models import ExperimentConfig


class ConfigManager:
    """
    Manages experiment configurations with support for YAML files,
    environment variables, and validation.
    """
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Create default config file if it doesn't exist
        self.default_config_path = self.config_dir / "default.yaml"
        if not self.default_config_path.exists():
            self._create_default_config()
    
    def _create_default_config(self):
        """Create a default configuration file."""
        default_config = {
            "experiment": {
                "num_agents": 4,
                "max_rounds": 5,
                "decision_rule": "unanimity",
                "timeout_seconds": 300,
                "models": ["gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini"]
            },
            "output": {
                "directory": "experiment_results",
                "formats": ["json", "csv", "txt"],
                "include_feedback": True,
                "include_transcript": True
            },
            "agents": {
                "personality_variation": True,
                "confidence_threshold": 0.5,
                "enable_feedback_collection": True
            },
            "performance": {
                "parallel_feedback": True,
                "trace_enabled": True,
                "debug_mode": False
            }
        }
        
        with open(self.default_config_path, 'w') as f:
            yaml.dump(default_config, f, indent=2, default_flow_style=False)
    
    def load_config(self, config_name: str = "default") -> ExperimentConfig:
        """
        Load configuration from YAML file with environment variable overrides.
        
        Args:
            config_name: Name of config file (without .yaml extension)
            
        Returns:
            ExperimentConfig object
        """
        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            if config_name != "default":
                print(f"Warning: Config file {config_path} not found, using default")
                config_path = self.default_config_path
            else:
                raise FileNotFoundError(f"Default config file not found: {config_path}")
        
        # Load YAML config
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Apply environment variable overrides
        config_data = self._apply_env_overrides(config_data)
        
        # Generate experiment ID if not provided
        experiment_id = config_data.get("experiment_id")
        if not experiment_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_id = f"exp_{timestamp}"
        
        # Create ExperimentConfig object
        experiment_config = ExperimentConfig(
            experiment_id=experiment_id,
            num_agents=config_data["experiment"]["num_agents"],
            max_rounds=config_data["experiment"]["max_rounds"],
            decision_rule=config_data["experiment"]["decision_rule"],
            timeout_seconds=config_data["experiment"]["timeout_seconds"],
            models=config_data["experiment"]["models"]
        )
        
        return experiment_config
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to config data."""
        
        # Define environment variable mappings
        env_mappings = {
            "MAAI_NUM_AGENTS": ("experiment", "num_agents", int),
            "MAAI_MAX_ROUNDS": ("experiment", "max_rounds", int),
            "MAAI_DECISION_RULE": ("experiment", "decision_rule", str),
            "MAAI_TIMEOUT": ("experiment", "timeout_seconds", int),
            "MAAI_MODELS": ("experiment", "models", lambda x: x.split(",")),
            "MAAI_OUTPUT_DIR": ("output", "directory", str),
            "MAAI_DEBUG": ("performance", "debug_mode", lambda x: x.lower() == "true"),
            "MAAI_EXPERIMENT_ID": ("experiment_id", None, str)
        }
        
        for env_var, (section, key, converter) in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                try:
                    converted_value = converter(value)
                    if key is None:
                        # Top-level key
                        config_data[section] = converted_value
                    else:
                        # Nested key
                        if section not in config_data:
                            config_data[section] = {}
                        config_data[section][key] = converted_value
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid value for {env_var}: {value} ({e})")
        
        return config_data
    
    def save_config(self, config: ExperimentConfig, name: str):
        """Save an ExperimentConfig as a YAML file."""
        config_path = self.config_dir / f"{name}.yaml"
        
        # Convert to dict structure
        config_data = {
            "experiment_id": config.experiment_id,
            "experiment": {
                "num_agents": config.num_agents,
                "max_rounds": config.max_rounds,
                "decision_rule": config.decision_rule,
                "timeout_seconds": config.timeout_seconds,
                "models": config.models
            },
            "output": {
                "directory": "experiment_results",
                "formats": ["json", "csv", "txt"],
                "include_feedback": True,
                "include_transcript": True
            },
            "agents": {
                "personality_variation": True,
                "confidence_threshold": 0.5,
                "enable_feedback_collection": True
            },
            "performance": {
                "parallel_feedback": True,
                "trace_enabled": True,
                "debug_mode": False
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, indent=2, default_flow_style=False)
    
    def list_configs(self) -> List[str]:
        """List available configuration files."""
        config_files = list(self.config_dir.glob("*.yaml"))
        return [f.stem for f in config_files]
    
    def create_config_template(self, name: str, base_config: str = "default"):
        """Create a new config file based on an existing one."""
        base_path = self.config_dir / f"{base_config}.yaml"
        new_path = self.config_dir / f"{name}.yaml"
        
        if not base_path.exists():
            raise FileNotFoundError(f"Base config not found: {base_path}")
        
        if new_path.exists():
            raise FileExistsError(f"Config already exists: {new_path}")
        
        # Copy base config
        with open(base_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Update experiment ID
        config_data["experiment_id"] = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with open(new_path, 'w') as f:
            yaml.dump(config_data, f, indent=2, default_flow_style=False)
        
        return new_path
    
    def validate_config(self, config_name: str) -> Dict[str, Any]:
        """Validate a configuration file and return validation results."""
        try:
            config = self.load_config(config_name)
            return {
                "valid": True,
                "config": config,
                "errors": [],
                "warnings": []
            }
        except Exception as e:
            return {
                "valid": False,
                "config": None,
                "errors": [str(e)],
                "warnings": []
            }


# Preset configurations for common scenarios
class PresetConfigs:
    """Predefined configurations for common experimental scenarios."""
    
    @staticmethod
    def quick_test() -> ExperimentConfig:
        """Quick test configuration with minimal agents and rounds."""
        return ExperimentConfig(
            experiment_id="quick_test",
            num_agents=3,
            max_rounds=2,
            decision_rule="unanimity",
            timeout_seconds=60,
            models=["gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini"]
        )
    
    @staticmethod
    def standard_experiment() -> ExperimentConfig:
        """Standard experiment configuration."""
        return ExperimentConfig(
            experiment_id="standard_exp",
            num_agents=4,
            max_rounds=5,
            decision_rule="unanimity",
            timeout_seconds=300,
            models=["gpt-4.1-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1"]
        )
    
    @staticmethod
    def large_group() -> ExperimentConfig:
        """Large group experiment configuration."""
        return ExperimentConfig(
            experiment_id="large_group",
            num_agents=8,
            max_rounds=10,
            decision_rule="unanimity",
            timeout_seconds=600,
            models=["gpt-4.1-mini"] * 8
        )
    
    @staticmethod
    def stress_test() -> ExperimentConfig:
        """Stress test configuration with many agents."""
        return ExperimentConfig(
            experiment_id="stress_test",
            num_agents=15,
            max_rounds=15,
            decision_rule="unanimity",
            timeout_seconds=900,
            models=["gpt-4.1-mini"] * 15
        )


def load_config_from_file(config_file: str) -> ExperimentConfig:
    """
    Convenience function to load configuration from a file.
    
    Args:
        config_file: Path to YAML config file or config name
        
    Returns:
        ExperimentConfig object
    """
    manager = ConfigManager()
    
    # If it's a path, extract the name
    if "/" in config_file or "\\" in config_file:
        config_name = Path(config_file).stem
    else:
        config_name = config_file
    
    return manager.load_config(config_name)


def create_config_from_dict(config_dict: Dict[str, Any]) -> ExperimentConfig:
    """
    Create ExperimentConfig from a dictionary.
    
    Args:
        config_dict: Dictionary with configuration values
        
    Returns:
        ExperimentConfig object
    """
    return ExperimentConfig(**config_dict)