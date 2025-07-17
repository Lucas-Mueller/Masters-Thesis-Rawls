import random
import yaml
import os
from typing import Dict, List, Any
from datetime import datetime
import uuid


class ProbabilisticConfigGenerator:
    """
    Generates configuration files based on probabilistic inputs.
    
    This module creates valid YAML configuration files that match the existing
    format used in the codebase, using probabilistic selection for various
    parameters.
    """
    
    def __init__(self, 
                 agent_count_probabilities: Dict[int, float],
                 personality_probabilities: Dict[str, float], 
                 rounds_probabilities: Dict[int, float],
                 model_probabilities: Dict[str, float],
                 output_folder: str):
        """
        Initialize the probabilistic configuration generator.
        
        Args:
            agent_count_probabilities: Mapping of agent counts to their probabilities
            personality_probabilities: Mapping of personality prompts to their probabilities
            rounds_probabilities: Mapping of round counts to their probabilities
            model_probabilities: Mapping of model identifiers to their probabilities
            output_folder: Folder where generated config files will be saved
        """
        self.agent_count_probabilities = agent_count_probabilities
        self.personality_probabilities = personality_probabilities
        self.rounds_probabilities = rounds_probabilities
        self.model_probabilities = model_probabilities
        self.output_folder = output_folder
        
        # Validate probabilities sum to 1.0 (with tolerance for floating point)
        self._validate_probabilities()
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
    
    def _validate_probabilities(self):
        """Validate that all probability distributions sum to approximately 1.0."""
        tolerance = 1e-6
        
        for name, probs in [
            ("agent_count", self.agent_count_probabilities),
            ("personality", self.personality_probabilities),
            ("rounds", self.rounds_probabilities),
            ("model", self.model_probabilities)
        ]:
            prob_sum = sum(probs.values())
            if abs(prob_sum - 1.0) > tolerance:
                raise ValueError(f"{name} probabilities sum to {prob_sum}, expected 1.0")
    
    def _weighted_choice(self, probabilities: Dict[Any, float]) -> Any:
        """Select an item based on weighted probabilities."""
        rand_val = random.random()
        cumulative = 0.0
        
        for item, prob in probabilities.items():
            cumulative += prob
            if rand_val <= cumulative:
                return item
        
        # Fallback to last item if floating point precision issues
        return list(probabilities.keys())[-1]
    
    def _generate_agent_configs(self, num_agents: int) -> List[Dict[str, Any]]:
        """Generate agent configurations for the specified number of agents."""
        agents = []
        
        for i in range(num_agents):
            agent_name = f"Agent_{i + 1}"
            personality = self._weighted_choice(self.personality_probabilities)
            model = self._weighted_choice(self.model_probabilities)
            
            agent_config = {
                "name": agent_name,
                "personality": personality,
                "model": model
            }
            
            agents.append(agent_config)
        
        return agents
    
    def generate_config(self, experiment_id: str = None) -> Dict[str, Any]:
        """
        Generate a single configuration based on probabilistic inputs.
        
        Args:
            experiment_id: Custom experiment ID, or None to generate one
            
        Returns:
            Dictionary containing the generated configuration
        """
        # Generate experiment ID if not provided
        if experiment_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_id = f"prob_gen_{timestamp}_{str(uuid.uuid4())[:8]}"
        
        # Select values based on probabilities
        num_agents = self._weighted_choice(self.agent_count_probabilities)
        max_rounds = self._weighted_choice(self.rounds_probabilities)
        
        # Generate agent configurations
        agents = self._generate_agent_configs(num_agents)
        
        # Select default model for fallback
        default_model = self._weighted_choice(self.model_probabilities)
        default_personality = self._weighted_choice(self.personality_probabilities)
        
        # Build configuration structure matching existing format
        config = {
            "experiment_id": experiment_id,
            "global_temperature": 0.0,  # Default for reproducibility
            "experiment": {
                "max_rounds": max_rounds,
                "decision_rule": "unanimity",
                "timeout_seconds": 300
            },
            "agents": agents,
            "defaults": {
                "personality": default_personality,
                "model": default_model
            },
            "output": {
                "directory": "experiment_results",
                "formats": ["json", "csv", "txt"],
                "include_feedback": True,
                "include_transcript": True
            },
            "performance": {
                "debug_mode": False,
                "parallel_feedback": True,
                "trace_enabled": True
            }
        }
        
        return config
    
    def generate_and_save_config(self, filename: str = None, experiment_id: str = None) -> str:
        """
        Generate a configuration and save it to a YAML file.
        
        Args:
            filename: Custom filename, or None to generate one
            experiment_id: Custom experiment ID, or None to generate one
            
        Returns:
            Path to the saved configuration file
        """
        config = self.generate_config(experiment_id)
        
        # Generate filename if not provided
        if filename is None:
            filename = f"{config['experiment_id']}.yaml"
        
        # Ensure .yaml extension
        if not filename.endswith('.yaml'):
            filename += '.yaml'
        
        file_path = os.path.join(self.output_folder, filename)
        
        # Save configuration to YAML file
        with open(file_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        return file_path
    
    def generate_batch_configs(self, count: int, prefix: str = "batch") -> List[str]:
        """
        Generate multiple configuration files.
        
        Args:
            count: Number of configurations to generate
            prefix: Prefix for the generated filenames
            
        Returns:
            List of paths to the generated configuration files
        """
        file_paths = []
        
        for i in range(count):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_id = f"{prefix}_{i+1:03d}_{timestamp}"
            filename = f"{experiment_id}.yaml"
            
            file_path = self.generate_and_save_config(filename, experiment_id)
            file_paths.append(file_path)
        
        return file_paths


def create_test_generator() -> ProbabilisticConfigGenerator:
    """
    Create a test-focused probabilistic configuration generator for testing.
    
    Returns:
        Configured ProbabilisticConfigGenerator instance for testing
    """
    # Test probability distributions (simpler for testing)
    agent_count_probs = {
        2: 0.7,
        3: 0.3
    }
    
    personality_probs = {
        "You are an agent tasked to design a future society.": 1.0
    }
    
    rounds_probs = {
        2: 0.7,
        3: 0.3
    }
    
    model_probs = {
        "gpt-4.1-nano": 1.0
    }
    
    return ProbabilisticConfigGenerator(
        agent_count_probabilities=agent_count_probs,
        personality_probabilities=personality_probs,
        rounds_probabilities=rounds_probs,
        model_probabilities=model_probs,
        output_folder="configs"
    )


def create_example_generator() -> ProbabilisticConfigGenerator:
    """
    Create an example probabilistic configuration generator with diverse inputs.
    
    Returns:
        Configured ProbabilisticConfigGenerator instance
    """
    # Example probability distributions
    agent_count_probs = {
        2: 0.1,
        3: 0.3,
        4: 0.4,
        5: 0.2
    }
    
    personality_probs = {
        "You are an economist focused on efficiency and optimal resource allocation.": 0.25,
        "You are a philosopher concerned with justice and fairness for all members of society.": 0.25,
        "You are a pragmatist who focuses on what works in practice rather than theory.": 0.25,
        "You are an agent tasked to design a future society.": 0.25
    }
    
    rounds_probs = {
        3: 0.2,
        5: 0.5,
        7: 0.2,
        10: 0.1
    }
    
    model_probs = {
        "gpt-4.1-mini": 0.4,
        "gpt-4.1-nano": 0.3,
        "gpt-4.1": 0.2,
        "claude-3-5-sonnet-20241022": 0.1
    }
    
    return ProbabilisticConfigGenerator(
        agent_count_probabilities=agent_count_probs,
        personality_probabilities=personality_probs,
        rounds_probabilities=rounds_probs,
        model_probabilities=model_probs,
        output_folder="configs"
    )


if __name__ == "__main__":
    # CLI interface for probabilistic configuration generation
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate probabilistic test configurations")
    parser.add_argument("--count", type=int, default=3, help="Number of configurations to generate")
    parser.add_argument("--output-dir", default="configs", help="Output directory")
    parser.add_argument("--prefix", default="test", help="Configuration name prefix")
    parser.add_argument("--example", action="store_true", help="Use example generator with diverse options")
    
    args = parser.parse_args()
    
    if args.example:
        # Use example generator with diverse options
        generator = create_example_generator()
        generator.output_folder = args.output_dir
        config_paths = generator.generate_batch_configs(args.count, args.prefix)
        print(f"✅ Generated {len(config_paths)} diverse probabilistic configurations in {args.output_dir}")
    else:
        # Use test generator (simpler for testing)
        generator = create_test_generator()
        generator.output_folder = args.output_dir
        config_paths = generator.generate_batch_configs(args.count, args.prefix)
        print(f"✅ Generated {len(config_paths)} test configurations in {args.output_dir}")
    
    # List generated files
    for i, path in enumerate(config_paths, 1):
        print(f"   {i}. {path}")