"""
ExperimentLogger for unified agent-centric JSON logging system.
Replaces all legacy feedback and conversation tracking mechanisms.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..core.models import ExperimentConfig, ConsensusResult, PrincipleChoice


class ExperimentLogger:
    """
    Unified agent-centric logging system that captures all experiment data
    organized by agent ID with comprehensive round-by-round tracking.
    """
    
    def __init__(self, experiment_id: str, config: ExperimentConfig):
        self.experiment_id = experiment_id
        self.config = config
        self.start_time = datetime.now()
        
        # Agent-centric data structure
        self.agent_data: Dict[str, Dict[str, Any]] = {}
        
        # Experiment metadata
        self.experiment_metadata = {
            "experiment_id": experiment_id,
            "start_time": self.start_time.isoformat(),
            "end_time": None,
            "total_duration_seconds": None,
            "max_rounds": config.max_rounds,
            "decision_rule": config.decision_rule,
            "final_consensus": None
        }
        
        # Initialize agents
        self._initialize_agents()
        
        # Logging configuration
        self.logging_config = config.logging
        
    def _initialize_agents(self):
        """Initialize agent data structures."""
        # Get agent configurations
        agent_configs = self.config.agents
        defaults = self.config.defaults
        
        for i, agent_config in enumerate(agent_configs):
            # Use the agent's name from config as the key for JSON structure
            agent_name = agent_config.name or f"Agent_{i+1}"
            
            # Initialize agent overall data
            self.agent_data[agent_name] = {
                "overall": {
                    "model": agent_config.model or defaults.model,
                    "persona": agent_config.personality or defaults.personality,
                    "instruction": "You are participating in a multi-agent deliberation to choose a distributive justice principle.",
                    "temperature": self.config.global_temperature or agent_config.temperature or getattr(defaults, "temperature", None)
                }
            }
    
    def log_initial_evaluation(self, agent_id: str, input_prompt: str, 
                             raw_response: str, rating_likert: str = None, 
                             rating_numeric: int = None, principle_ratings: dict = None):
        """Log initial evaluation (round_0) for an agent."""
        if agent_id not in self.agent_data:
            self.agent_data[agent_id] = {"overall": {}}
            
        round_data = {
            "input": input_prompt,
            "output": raw_response,
            "rating_likert": rating_likert,
            "rating_numeric": rating_numeric
        }
        
        # Add structured principle ratings if provided
        if principle_ratings:
            round_data["principle_ratings"] = principle_ratings
            
        self.agent_data[agent_id]["round_0"] = round_data
    
    def log_round_start(self, agent_id: str, round_num: int, speaking_order: int = None,
                       public_history: str = None):
        """Initialize round data for an agent."""
        if agent_id not in self.agent_data:
            self.agent_data[agent_id] = {"overall": {}}
            
        round_key = f"round_{round_num}"
        if round_key not in self.agent_data[agent_id]:
            self.agent_data[agent_id][round_key] = {}
            
        if speaking_order is not None:
            self.agent_data[agent_id][round_key]["speaking_order"] = speaking_order
            
        if public_history:
            self.agent_data[agent_id][round_key]["public_history"] = public_history
    
    def log_memory_generation(self, agent_id: str, round_num: int, 
                            memory_content: str, strategy: str = None):
        """Log memory generation for an agent in a specific round."""
        round_key = f"round_{round_num}"
        if agent_id not in self.agent_data:
            self.agent_data[agent_id] = {"overall": {}}
        if round_key not in self.agent_data[agent_id]:
            self.agent_data[agent_id][round_key] = {}
            
        self.agent_data[agent_id][round_key]["memory"] = memory_content
        if strategy:
            self.agent_data[agent_id][round_key]["strategy"] = strategy
    
    def log_communication(self, agent_id: str, round_num: int, 
                         communication: str, choice: str = None):
        """Log public communication and choice for an agent."""
        round_key = f"round_{round_num}"
        if agent_id not in self.agent_data:
            self.agent_data[agent_id] = {"overall": {}}
        if round_key not in self.agent_data[agent_id]:
            self.agent_data[agent_id][round_key] = {}
            
        self.agent_data[agent_id][round_key]["communication"] = communication
        if choice:
            self.agent_data[agent_id][round_key]["choice"] = choice
    
    def log_agent_interaction(self, agent_id: str, round_num: int, 
                            interaction_type: str, input_prompt: str = None,
                            raw_response: str = None, sequence_num: int = 0):
        """Log individual agent interactions with sequence tracking."""
        round_key = f"round_{round_num}"
        if agent_id not in self.agent_data:
            self.agent_data[agent_id] = {"overall": {}}
        if round_key not in self.agent_data[agent_id]:
            self.agent_data[agent_id][round_key] = {}
            
        # Initialize input/output dicts if they don't exist
        if "input_dict" not in self.agent_data[agent_id][round_key]:
            self.agent_data[agent_id][round_key]["input_dict"] = {}
        if "output_dict" not in self.agent_data[agent_id][round_key]:
            self.agent_data[agent_id][round_key]["output_dict"] = {}
            
        # Store input/output with sequence number
        if input_prompt:
            self.agent_data[agent_id][round_key]["input_dict"][str(sequence_num)] = input_prompt
        if raw_response:
            self.agent_data[agent_id][round_key]["output_dict"][str(sequence_num)] = raw_response
    
    def log_final_consensus(self, agent_id: str, agreement_reached: bool,
                          agreement_choice: str = None, num_rounds: int = None,
                          satisfaction: int = None):
        """Log final consensus data for an agent."""
        if agent_id not in self.agent_data:
            self.agent_data[agent_id] = {"overall": {}}
            
        self.agent_data[agent_id]["final"] = {
            "agreement_reached": agreement_reached,
            "agreement_choice": agreement_choice,
            "num_rounds": num_rounds,
            "satisfaction": satisfaction
        }
    
    def log_experiment_completion(self, consensus_result: ConsensusResult = None,
                                total_rounds: int = None):
        """Log overall experiment completion data."""
        end_time = datetime.now()
        self.experiment_metadata["end_time"] = end_time.isoformat()
        self.experiment_metadata["total_duration_seconds"] = (end_time - self.start_time).total_seconds()
        
        if consensus_result:
            self.experiment_metadata["final_consensus"] = {
                "agreement_reached": consensus_result.unanimous,
                "agreed_principle": consensus_result.agreed_principle.principle_name if consensus_result.agreed_principle else None,
                "num_rounds": total_rounds or consensus_result.rounds_to_consensus,
                "total_messages": getattr(consensus_result, 'total_messages', 0)
            }
    
    def export_unified_json(self, output_dir: Optional[str] = None) -> str:
        """
        Export single unified JSON file with agent-centric structure.
        
        Args:
            output_dir: Optional output directory override. If None, uses config.output.directory
        
        Returns:
            Path to exported JSON file
        """
        if output_dir is None:
            output_dir = self.config.output.directory
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Build complete unified structure
        unified_data = {
            "experiment_metadata": self.experiment_metadata
        }
        
        # Add all agent data
        unified_data.update(self.agent_data)
        
        # Export to single JSON file
        json_file = output_path / f"{self.experiment_id}.json"
        
        # Custom JSON encoder for datetime objects and other types
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            # Handle LitellmModel objects by converting to string representation
            if hasattr(obj, '__class__') and 'LitellmModel' in str(type(obj)):
                return str(obj)
            # Handle Pydantic models by converting to dict
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, 'dict'):
                return obj.dict()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(unified_data, f, indent=2, ensure_ascii=False, default=json_serializer)
        
        return str(json_file)
    
    def get_experiment_summary(self) -> Dict[str, Any]:
        """Get summary of collected data for debugging."""
        total_rounds = 0
        total_interactions = 0
        
        for agent_id, agent_data in self.agent_data.items():
            # Count only deliberation rounds (round_1+), not initial evaluation (round_0)
            agent_rounds = len([k for k in agent_data.keys() if k.startswith("round_") and k != "round_0"])
            total_rounds = max(total_rounds, agent_rounds)
            
            for round_key, round_data in agent_data.items():
                if round_key.startswith("round_") and "input_dict" in round_data:
                    total_interactions += len(round_data["input_dict"])
        
        return {
            "experiment_id": self.experiment_id,
            "total_agents": len(self.agent_data),
            "total_rounds": total_rounds,
            "total_interactions": total_interactions,
            "experiment_completed": self.experiment_metadata["end_time"] is not None,
            "consensus_recorded": self.experiment_metadata["final_consensus"] is not None
        }
    
    # Legacy method compatibility (for gradual migration)
    def export_complete_json(self, output_dir: Optional[str] = None) -> str:
        """Legacy method name - delegates to new unified export."""
        return self.export_unified_json(output_dir)
    
