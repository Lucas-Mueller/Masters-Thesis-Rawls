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
import glob

from ..core.models import ExperimentConfig, AgentConfig, DefaultConfig


class ConfigManager:
    """
    Manages experiment configurations with support for YAML files,
    environment variables, and validation.
    """
    
    def __init__(self, config_dir: str = "configs", results_dir: str = "experiment_results"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Create default config file if it doesn't exist
        self.default_config_path = self.config_dir / "default.yaml"
        if not self.default_config_path.exists():
            self._create_default_config()
    
    def _create_default_config(self):
        """Create a default configuration file."""
        default_config = {
            "experiment_id": "default_experiment",
            "experiment": {
                "max_rounds": 5,
                "decision_rule": "unanimity",
                "timeout_seconds": 300
            },
            "agents": [
                {"name": "Agent_1", "model": "gpt-4.1-mini"},
                {"name": "Agent_2", "model": "gpt-4.1-mini"},
                {"name": "Agent_3", "model": "gpt-4.1-mini"},
                {"name": "Agent_4", "model": "gpt-4.1-mini"}
            ],
            "defaults": {
                "personality": "You are an agent tasked to design a future society.",
                "model": "gpt-4.1-mini"
            },
            # Example temperature configurations (uncomment to use)
            # "global_temperature": 0.0,  # Global temperature for all agents (for reproducible results)
            # "defaults": {
            #     "personality": "You are an agent tasked to design a future society.",
            #     "model": "gpt-4.1-mini",
            #     "temperature": 0.2  # Default temperature for agents
            # },
            # "agents": [
            #     {"name": "Agent_1", "model": "gpt-4.1-mini", "temperature": 0.0},  # Agent-specific temperature
            #     {"name": "Agent_2", "model": "gpt-4.1-mini"},  # Uses default temperature
            # ],
            "output": {
                "directory": "experiment_results",
                "formats": ["json", "csv", "txt"],
                "include_feedback": True,
                "include_transcript": True
            },
            "performance": {
                "parallel_feedback": True,
                "trace_enabled": True,
                "debug_mode": False
            }
        }
        
        with open(self.default_config_path, 'w') as f:
            yaml.dump(default_config, f, indent=2, default_flow_style=False)
    
    def _generate_unique_experiment_id(self, base_id: str) -> str:
        """
        Generate a unique experiment ID by checking existing results files.
        If base_id exists, try base_id 1, base_id 2, etc.
        
        Args:
            base_id: The desired experiment ID from the config
            
        Returns:
            Unique experiment ID that doesn't conflict with existing results
        """
        # Check if base_id already exists
        if not self._experiment_id_exists(base_id):
            return base_id
        
        # Try incrementing numbers
        counter = 1
        while True:
            candidate_id = f"{base_id} {counter}"
            if not self._experiment_id_exists(candidate_id):
                return candidate_id
            counter += 1
    
    def _experiment_id_exists(self, experiment_id: str) -> bool:
        """
        Check if an experiment ID already exists in the results directory.
        
        Args:
            experiment_id: The experiment ID to check
            
        Returns:
            True if files with this experiment ID exist, False otherwise
        """
        # Look for any files that start with the experiment ID
        pattern = f"{experiment_id}_*"
        existing_files = list(self.results_dir.glob(pattern))
        return len(existing_files) > 0
    
    def load_config(self, config_name: str = "default") -> ExperimentConfig:
        """
        Load configuration from YAML file with environment variable overrides.
        
        Args:
            config_name: Name of config file (without .yaml extension)
            
        Returns:
            ExperimentConfig object
            
        Raises:
            FileNotFoundError: If the specified config file doesn't exist
        """
        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            # No fallback behavior - fail fast with clear error message
            available_configs = [f.stem for f in self.config_dir.glob("*.yaml")]
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Available configurations: {available_configs}\n"
                f"To create a new config, use ConfigManager.create_config_template('{config_name}')"
            )
        
        # Load YAML config
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file {config_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to read config file {config_path}: {e}")
        
        # Apply environment variable overrides
        config_data = self._apply_env_overrides(config_data)
        
        # Validate required structure
        if "experiment" not in config_data:
            raise ValueError(f"Config file {config_path} missing required 'experiment' section")
        
        if "agents" not in config_data:
            raise ValueError(f"Config file {config_path} missing required 'agents' section")
        
        required_experiment_fields = ["max_rounds"]
        for field in required_experiment_fields:
            if field not in config_data["experiment"]:
                raise ValueError(f"Config file {config_path} missing required field 'experiment.{field}'")
        
        # Generate experiment ID if not provided
        experiment_id = config_data.get("experiment_id")
        if not experiment_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_id = f"exp_{timestamp}"
        
        # Make sure the experiment ID is unique
        experiment_id = self._generate_unique_experiment_id(experiment_id)
        
        # Parse defaults
        defaults_data = config_data.get("defaults", {})
        defaults = DefaultConfig(**defaults_data)
        
        # Parse agent configurations
        agents_data = config_data["agents"]
        if not agents_data:
            raise ValueError(f"Config file {config_path} has empty 'agents' section")
        
        agents = []
        for i, agent_data in enumerate(agents_data):
            # Ensure agent_data is a dict
            if agent_data is None:
                agent_data = {}
            
            # Generate name if not provided
            if "name" not in agent_data or not agent_data["name"]:
                agent_data["name"] = f"Agent_{i+1}"
            
            agent = AgentConfig(**agent_data)
            agents.append(agent)
        
        print(f"Loaded {len(agents)} agents:")
        for agent in agents:
            model = agent.model or defaults.model
            has_custom_personality = agent.personality is not None
            print(f"  - {agent.name}: {model}" + (" (custom personality)" if has_custom_personality else " (default personality)"))
        
        # Create ExperimentConfig object with validation
        try:
            experiment_config = ExperimentConfig(
                experiment_id=experiment_id,
                max_rounds=config_data["experiment"]["max_rounds"],
                decision_rule=config_data["experiment"].get("decision_rule", "unanimity"),
                timeout_seconds=config_data["experiment"].get("timeout_seconds", 300),
                agents=agents,
                defaults=defaults,
                global_temperature=config_data.get("global_temperature"),
                memory_strategy=config_data.get("memory_strategy", "full")
            )
        except Exception as e:
            raise ValueError(f"Failed to create valid ExperimentConfig from {config_path}: {e}")
        
        return experiment_config
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to config data."""
        
        # Define environment variable mappings
        env_mappings = {
            "MAAI_MAX_ROUNDS": ("experiment", "max_rounds", int),
            "MAAI_DECISION_RULE": ("experiment", "decision_rule", str),
            "MAAI_TIMEOUT": ("experiment", "timeout_seconds", int),
            "MAAI_DEFAULT_MODEL": ("defaults", "model", str),
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
                "max_rounds": config.max_rounds,
                "decision_rule": config.decision_rule,
                "timeout_seconds": config.timeout_seconds
            },
            "agents": [agent.dict(exclude_none=True) for agent in config.agents],
            "defaults": config.defaults.dict(),
        }
        
        # Include global_temperature if specified
        if config.global_temperature is not None:
            config_data["global_temperature"] = config.global_temperature
        
        config_data.update({
            "output": {
                "directory": "experiment_results",
                "formats": ["json", "csv", "txt"],
                "include_feedback": True,
                "include_transcript": True
            },
            "performance": {
                "parallel_feedback": True,
                "trace_enabled": True,
                "debug_mode": False
            }
        })
        
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



def load_config_from_file(config_file: str, results_dir: str = "experiment_results") -> ExperimentConfig:
    """
    Convenience function to load configuration from a file.
    
    Args:
        config_file: Path to YAML config file or config name
        results_dir: Directory where experiment results are stored
        
    Returns:
        ExperimentConfig object
    """
    manager = ConfigManager(results_dir=results_dir)
    
    # If it's a path, extract the name
    if "/" in config_file or "\\" in config_file:
        config_name = Path(config_file).stem
    else:
        config_name = config_file
    
    return manager.load_config(config_name)


