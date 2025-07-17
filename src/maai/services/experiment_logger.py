"""
ExperimentLogger for comprehensive single-file experiment data collection.
Collects all experiment data in memory and exports single JSON file at completion.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..core.models import ExperimentConfig, ConsensusResult, PrincipleChoice


class ExperimentLogger:
    """
    Simple in-memory data collector that exports single comprehensive JSON file.
    Replaces the multi-file export system with single-file solution.
    """
    
    def __init__(self, experiment_id: str, config: ExperimentConfig):
        self.experiment_id = experiment_id
        self.config = config
        self.start_time = datetime.now()
        
        # In-memory data collection
        self.agent_interactions: List[Dict[str, Any]] = []
        self.memory_events: List[Dict[str, Any]] = []
        self.round_events: List[Dict[str, Any]] = []
        self.evaluation_data = {"initial": [], "final": []}
        self.consensus_result: Optional[ConsensusResult] = None
        self.performance_metrics: Dict[str, Any] = {}
        
        # Logging configuration
        self.logging_config = config.logging
        self.capture_raw_inputs = self.logging_config.capture_raw_inputs
        self.capture_raw_outputs = self.logging_config.capture_raw_outputs
        self.capture_memory_context = self.logging_config.capture_memory_context
        self.capture_memory_steps = self.logging_config.capture_memory_steps
        self.include_processing_times = self.logging_config.include_processing_times
    
    def log_agent_interaction(self, agent_id: str, agent_name: str, round_num: int, 
                             speaking_position: int, input_prompt: str = None, 
                             raw_llm_response: str = None, parsed_response: Dict = None,
                             processing_time_ms: float = None, model_used: str = None,
                             temperature: float = None):
        """Log agent interaction data (prompts, responses, timing)."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "agent_name": agent_name,
            "round": round_num,
            "speaking_position": speaking_position
        }
        
        if self.capture_raw_inputs and input_prompt:
            interaction["input_prompt"] = input_prompt
            
        if self.capture_raw_outputs and raw_llm_response:
            interaction["raw_llm_response"] = raw_llm_response
            
        if parsed_response:
            interaction["parsed_response"] = parsed_response
            
        if self.include_processing_times and processing_time_ms is not None:
            interaction["processing_time_ms"] = processing_time_ms
            
        if model_used:
            interaction["model_used"] = model_used
            
        if temperature is not None:
            interaction["temperature"] = temperature
            
        self.agent_interactions.append(interaction)
    
    def log_memory_event(self, agent_id: str, round_num: int, memory_context: str = None,
                        memory_strategy: str = None, decomposed_steps: List[Dict] = None,
                        final_memory_entry: Dict = None):
        """Log memory system events (context, decomposed steps, final entry)."""
        memory_event = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "round": round_num
        }
        
        if self.capture_memory_context and memory_context:
            memory_event["memory_context_provided"] = memory_context
            memory_event["context_length_chars"] = len(memory_context)
            
        if memory_strategy:
            memory_event["memory_strategy"] = memory_strategy
            
        if self.capture_memory_steps and decomposed_steps:
            memory_event["decomposed_steps"] = decomposed_steps
            
        if final_memory_entry:
            memory_event["final_memory_entry"] = final_memory_entry
            
        self.memory_events.append(memory_event)
    
    def log_round_event(self, round_num: int, start_time: datetime = None, 
                       end_time: datetime = None, speaking_order: List[str] = None,
                       agent_choices_start: List[int] = None, agent_choices_end: List[int] = None,
                       consensus_check_result: Dict = None):
        """Log round-level events (timing, choices, consensus)."""
        round_event = {
            "round": round_num
        }
        
        if start_time:
            round_event["start_time"] = start_time.isoformat()
            
        if end_time:
            round_event["end_time"] = end_time.isoformat()
            if start_time:
                duration_ms = (end_time - start_time).total_seconds() * 1000
                round_event["duration_ms"] = duration_ms
                
        if speaking_order:
            round_event["speaking_order"] = speaking_order
            
        if agent_choices_start:
            round_event["agent_choices_start"] = agent_choices_start
            
        if agent_choices_end:
            round_event["agent_choices_end"] = agent_choices_end
            
        if consensus_check_result:
            round_event["consensus_check_result"] = consensus_check_result
            
        self.round_events.append(round_event)
    
    def log_evaluation(self, evaluation_type: str, agent_id: str, agent_name: str,
                      principle_ratings: List[Dict], evaluation_duration_ms: float = None,
                      overall_reasoning: str = None):
        """Log Likert scale evaluations (initial or final)."""
        evaluation = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "agent_name": agent_name,
            "principle_ratings": principle_ratings
        }
        
        if self.include_processing_times and evaluation_duration_ms is not None:
            evaluation["evaluation_duration_ms"] = evaluation_duration_ms
            
        if overall_reasoning:
            evaluation["overall_reasoning"] = overall_reasoning
            
        self.evaluation_data[evaluation_type].append(evaluation)
    
    def log_consensus_result(self, consensus_result: ConsensusResult):
        """Log final consensus result."""
        self.consensus_result = consensus_result
    
    def log_performance_metrics(self, total_duration_seconds: float, 
                               average_round_duration: float = None,
                               total_agent_interactions: int = None,
                               total_memory_generations: int = None,
                               errors_encountered: int = 0):
        """Log performance and timing metrics."""
        self.performance_metrics = {
            "total_duration_seconds": total_duration_seconds,
            "errors_encountered": errors_encountered
        }
        
        if average_round_duration is not None:
            self.performance_metrics["average_round_duration"] = average_round_duration
            
        if total_agent_interactions is not None:
            self.performance_metrics["total_agent_interactions"] = total_agent_interactions
            
        if total_memory_generations is not None:
            self.performance_metrics["total_memory_generations"] = total_memory_generations
    
    def export_complete_json(self, output_dir: str = "experiment_results") -> str:
        """
        Export single comprehensive JSON file with all experiment data.
        
        Returns:
            Path to exported JSON file
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        end_time = datetime.now()
        total_duration_ms = (end_time - self.start_time).total_seconds() * 1000
        
        # Build complete experiment data structure
        experiment_data = {
            "experiment_metadata": {
                "experiment_id": self.experiment_id,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration_ms": total_duration_ms,
                "configuration": self.config.model_dump() if hasattr(self.config, 'model_dump') else self.config.dict()
            },
            "agent_interactions": self.agent_interactions,
            "memory_events": self.memory_events,
            "round_events": self.round_events,
            "evaluations": {
                "initial_likert_assessments": self.evaluation_data["initial"],
                "final_likert_assessments": self.evaluation_data["final"]
            },
            "consensus_result": (
                self.consensus_result.model_dump() if hasattr(self.consensus_result, 'model_dump') 
                else self.consensus_result.dict() if self.consensus_result else None
            ),
            "performance_metrics": self.performance_metrics
        }
        
        # Export to single JSON file
        json_file = output_path / f"{self.experiment_id}.json"
        
        # Custom JSON encoder for datetime objects and LitellmModel objects
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            # Handle LitellmModel objects by converting to string representation
            if hasattr(obj, '__class__') and 'LitellmModel' in str(type(obj)):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(experiment_data, f, indent=2, ensure_ascii=False, default=json_serializer)
        
        return str(json_file)
    
    def get_experiment_summary(self) -> Dict[str, Any]:
        """Get summary of collected data for debugging."""
        return {
            "experiment_id": self.experiment_id,
            "agent_interactions_count": len(self.agent_interactions),
            "memory_events_count": len(self.memory_events),
            "round_events_count": len(self.round_events),
            "initial_evaluations_count": len(self.evaluation_data["initial"]),
            "final_evaluations_count": len(self.evaluation_data["final"]),
            "consensus_result_available": self.consensus_result is not None,
            "performance_metrics_available": bool(self.performance_metrics)
        }