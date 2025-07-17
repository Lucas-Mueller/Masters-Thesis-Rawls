"""
Test suite for the new ExperimentLogger system.
Tests single JSON file logging with all required data points.
"""

import json
import tempfile
import asyncio
from pathlib import Path
from datetime import datetime
import sys
import os

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.maai.core.models import ExperimentConfig, LoggingConfig, DefaultConfig, AgentConfig, ConsensusResult, PrincipleChoice
from src.maai.services.experiment_logger import ExperimentLogger


class TestExperimentLogger:
    """Test cases for ExperimentLogger functionality."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = ExperimentConfig(
            experiment_id="test_logging",
            max_rounds=2,
            agents=[
                AgentConfig(name="Agent_1", model="gpt-4.1-nano"),
                AgentConfig(name="Agent_2", model="gpt-4.1")
            ],
            defaults=DefaultConfig(),
            logging=LoggingConfig(
                enabled=True,
                capture_raw_inputs=True,
                capture_raw_outputs=True,
                capture_memory_context=True,
                capture_memory_steps=True,
                include_processing_times=True
            )
        )
        
        self.temp_dir = tempfile.mkdtemp()
        self.logger = ExperimentLogger(self.config.experiment_id, self.config)
    
    def test_logger_initialization(self):
        """Test logger initializes with correct configuration."""
        assert self.logger.experiment_id == "test_logging"
        assert self.logger.capture_raw_inputs == True
        assert self.logger.capture_raw_outputs == True
        assert self.logger.capture_memory_context == True
        assert self.logger.capture_memory_steps == True
        assert self.logger.include_processing_times == True
        
        # Check data structures are initialized
        assert self.logger.agent_interactions == []
        assert self.logger.memory_events == []
        assert self.logger.round_events == []
        assert self.logger.evaluation_data == {"initial": [], "final": []}
    
    def test_agent_interaction_logging(self):
        """Test logging of agent interactions."""
        # Test logging input prompt
        self.logger.log_agent_interaction(
            agent_id="agent_1",
            agent_name="Agent_1",
            round_num=1,
            speaking_position=1,
            input_prompt="You are behind a veil of ignorance...",
            model_used="gpt-4.1-nano",
            temperature=0.7
        )
        
        # Test logging raw response
        self.logger.log_agent_interaction(
            agent_id="agent_1",
            agent_name="Agent_1",
            round_num=1,
            speaking_position=1,
            raw_llm_response="I choose principle 3 because...",
            processing_time_ms=3400
        )
        
        # Test logging parsed response
        self.logger.log_agent_interaction(
            agent_id="agent_1",
            agent_name="Agent_1",
            round_num=1,
            speaking_position=1,
            parsed_response={
                "principle_id": 3,
                "principle_name": "Maximize Average with Floor",
                "reasoning": "This provides balance...",
                "public_message": "I believe principle 3..."
            }
        )
        
        assert len(self.logger.agent_interactions) == 3
        
        # Check first interaction (input prompt)
        interaction_1 = self.logger.agent_interactions[0]
        assert interaction_1["agent_id"] == "agent_1"
        assert interaction_1["agent_name"] == "Agent_1"
        assert interaction_1["round"] == 1
        assert interaction_1["speaking_position"] == 1
        assert "input_prompt" in interaction_1
        assert interaction_1["model_used"] == "gpt-4.1-nano"
        assert interaction_1["temperature"] == 0.7
        
        # Check second interaction (raw response)
        interaction_2 = self.logger.agent_interactions[1]
        assert "raw_llm_response" in interaction_2
        assert interaction_2["processing_time_ms"] == 3400
        
        # Check third interaction (parsed response)
        interaction_3 = self.logger.agent_interactions[2]
        assert "parsed_response" in interaction_3
        assert interaction_3["parsed_response"]["principle_id"] == 3
    
    def test_memory_event_logging(self):
        """Test logging of memory events."""
        # Test basic memory context logging
        self.logger.log_memory_event(
            agent_id="agent_1",
            round_num=1,
            memory_context="PREVIOUS CONVERSATION:\nRound 0 - Agent_2 chose principle 4...",
            memory_strategy="decomposed"
        )
        
        # Test decomposed memory steps logging
        decomposed_steps = [
            {
                "step": "factual_recap",
                "prompt": "Briefly summarize what just happened...",
                "response": "Agent_2 chose principle 4 and emphasized range constraints.",
                "processing_time_ms": 1200
            },
            {
                "step": "agent_analysis",
                "prompt": "Focus on Agent_2's behavior...",
                "response": "Agent_2 is consistent in their preference for equality.",
                "processing_time_ms": 1800
            },
            {
                "step": "strategic_action",
                "prompt": "What is ONE specific thing...",
                "response": "I should address Agent_2's concerns about inequality.",
                "processing_time_ms": 1500
            }
        ]
        
        self.logger.log_memory_event(
            agent_id="agent_1",
            round_num=1,
            decomposed_steps=decomposed_steps
        )
        
        # Test final memory entry logging
        self.logger.log_memory_event(
            agent_id="agent_1",
            round_num=1,
            final_memory_entry={
                "situation_assessment": "Agent_2 is advocating for principle 4...",
                "other_agents_analysis": "Agent_2 is focused on equality...",
                "strategy_update": "I should emphasize the benefits of principle 3...",
                "speaking_position": 1
            }
        )
        
        assert len(self.logger.memory_events) == 3
        
        # Check memory context logging
        memory_event_1 = self.logger.memory_events[0]
        assert memory_event_1["agent_id"] == "agent_1"
        assert memory_event_1["round"] == 1
        assert "memory_context_provided" in memory_event_1
        assert memory_event_1["memory_strategy"] == "decomposed"
        assert memory_event_1["context_length_chars"] > 0
        
        # Check decomposed steps logging
        memory_event_2 = self.logger.memory_events[1]
        assert "decomposed_steps" in memory_event_2
        assert len(memory_event_2["decomposed_steps"]) == 3
        assert memory_event_2["decomposed_steps"][0]["step"] == "factual_recap"
        assert memory_event_2["decomposed_steps"][1]["step"] == "agent_analysis"
        assert memory_event_2["decomposed_steps"][2]["step"] == "strategic_action"
        
        # Check final memory entry logging
        memory_event_3 = self.logger.memory_events[2]
        assert "final_memory_entry" in memory_event_3
        assert memory_event_3["final_memory_entry"]["speaking_position"] == 1
    
    def test_round_event_logging(self):
        """Test logging of round events."""
        start_time = datetime.now()
        end_time = datetime.now()
        
        self.logger.log_round_event(
            round_num=1,
            start_time=start_time,
            end_time=end_time,
            speaking_order=["agent_1", "agent_2"],
            agent_choices_start=[3, 4],
            agent_choices_end=[3, 3],
            consensus_check_result={"unanimous": True, "dissenting_agents": []}
        )
        
        assert len(self.logger.round_events) == 1
        
        round_event = self.logger.round_events[0]
        assert round_event["round"] == 1
        assert "start_time" in round_event
        assert "end_time" in round_event
        assert "duration_ms" in round_event
        assert round_event["speaking_order"] == ["agent_1", "agent_2"]
        assert round_event["agent_choices_start"] == [3, 4]
        assert round_event["agent_choices_end"] == [3, 3]
        assert round_event["consensus_check_result"]["unanimous"] == True
    
    def test_evaluation_logging(self):
        """Test logging of Likert scale evaluations."""
        principle_ratings = [
            {"principle_id": 1, "rating": "disagree", "reasoning": "Too focused on minimum..."},
            {"principle_id": 2, "rating": "strongly_disagree", "reasoning": "Ignores inequality..."},
            {"principle_id": 3, "rating": "strongly_agree", "reasoning": "Best balance of concerns..."},
            {"principle_id": 4, "rating": "agree", "reasoning": "Good but complex to implement..."}
        ]
        
        # Test initial evaluation
        self.logger.log_evaluation(
            evaluation_type="initial",
            agent_id="agent_1",
            agent_name="Agent_1",
            principle_ratings=principle_ratings,
            evaluation_duration_ms=8500,
            overall_reasoning="Behind the veil of ignorance, I prioritize..."
        )
        
        # Test final evaluation
        self.logger.log_evaluation(
            evaluation_type="final",
            agent_id="agent_1",
            agent_name="Agent_1",
            principle_ratings=principle_ratings,
            evaluation_duration_ms=7200
        )
        
        assert len(self.logger.evaluation_data["initial"]) == 1
        assert len(self.logger.evaluation_data["final"]) == 1
        
        initial_eval = self.logger.evaluation_data["initial"][0]
        assert initial_eval["agent_id"] == "agent_1"
        assert len(initial_eval["principle_ratings"]) == 4
        assert initial_eval["evaluation_duration_ms"] == 8500
        assert "overall_reasoning" in initial_eval
        
        final_eval = self.logger.evaluation_data["final"][0]
        assert final_eval["evaluation_duration_ms"] == 7200
    
    def test_consensus_and_performance_logging(self):
        """Test logging of consensus results and performance metrics."""
        # Test consensus result logging
        consensus_result = ConsensusResult(
            unanimous=True,
            agreed_principle=PrincipleChoice(
                principle_id=3,
                principle_name="Maximize Average with Floor",
                reasoning="Best balance of fairness and efficiency"
            ),
            dissenting_agents=[],
            rounds_to_consensus=2,
            total_messages=6
        )
        
        self.logger.log_consensus_result(consensus_result)
        assert self.logger.consensus_result == consensus_result
        
        # Test performance metrics logging
        self.logger.log_performance_metrics(
            total_duration_seconds=120.5,
            average_round_duration=60.25,
            total_agent_interactions=6,
            total_memory_generations=4,
            errors_encountered=0
        )
        
        assert self.logger.performance_metrics["total_duration_seconds"] == 120.5
        assert self.logger.performance_metrics["average_round_duration"] == 60.25
        assert self.logger.performance_metrics["total_agent_interactions"] == 6
        assert self.logger.performance_metrics["total_memory_generations"] == 4
        assert self.logger.performance_metrics["errors_encountered"] == 0
    
    def test_json_export(self):
        """Test complete JSON export functionality."""
        # Add some sample data
        self.logger.log_agent_interaction(
            agent_id="agent_1",
            agent_name="Agent_1",
            round_num=1,
            speaking_position=1,
            input_prompt="Test prompt",
            raw_llm_response="Test response",
            processing_time_ms=1000
        )
        
        self.logger.log_memory_event(
            agent_id="agent_1",
            round_num=1,
            memory_context="Test context",
            memory_strategy="decomposed"
        )
        
        self.logger.log_evaluation(
            evaluation_type="initial",
            agent_id="agent_1",
            agent_name="Agent_1",
            principle_ratings=[{"principle_id": 1, "rating": "agree", "reasoning": "Test"}]
        )
        
        consensus_result = ConsensusResult(
            unanimous=True,
            agreed_principle=PrincipleChoice(
                principle_id=3,
                principle_name="Test Principle",
                reasoning="Test reasoning"
            ),
            dissenting_agents=[],
            rounds_to_consensus=1,
            total_messages=1
        )
        self.logger.log_consensus_result(consensus_result)
        
        self.logger.log_performance_metrics(
            total_duration_seconds=60.0,
            errors_encountered=0
        )
        
        # Export to JSON
        json_file = self.logger.export_complete_json(self.temp_dir)
        
        # Verify file was created
        assert Path(json_file).exists()
        
        # Load and verify JSON structure
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Check top-level structure
        assert "experiment_metadata" in data
        assert "agent_interactions" in data
        assert "memory_events" in data
        assert "round_events" in data
        assert "evaluations" in data
        assert "consensus_result" in data
        assert "performance_metrics" in data
        
        # Check experiment metadata
        metadata = data["experiment_metadata"]
        assert metadata["experiment_id"] == "test_logging"
        assert "start_time" in metadata
        assert "end_time" in metadata
        assert "total_duration_ms" in metadata
        assert "configuration" in metadata
        
        # Check configuration is properly serialized
        config_data = metadata["configuration"]
        assert config_data["experiment_id"] == "test_logging"
        assert config_data["max_rounds"] == 2
        assert len(config_data["agents"]) == 2
        assert "logging" in config_data
        
        # Check agent interactions
        assert len(data["agent_interactions"]) == 1
        interaction = data["agent_interactions"][0]
        assert interaction["agent_id"] == "agent_1"
        assert "timestamp" in interaction
        
        # Check memory events
        assert len(data["memory_events"]) == 1
        memory_event = data["memory_events"][0]
        assert memory_event["agent_id"] == "agent_1"
        
        # Check evaluations
        evaluations = data["evaluations"]
        assert "initial_likert_assessments" in evaluations
        assert "final_likert_assessments" in evaluations
        assert len(evaluations["initial_likert_assessments"]) == 1
        
        # Check consensus result
        consensus_data = data["consensus_result"]
        assert consensus_data["unanimous"] == True
        assert consensus_data["agreed_principle"]["principle_id"] == 3
        
        # Check performance metrics
        performance = data["performance_metrics"]
        assert performance["total_duration_seconds"] == 60.0
        assert performance["errors_encountered"] == 0
    
    def test_logging_configuration_control(self):
        """Test that logging configuration controls what gets logged."""
        # Create logger with selective logging disabled
        selective_config = ExperimentConfig(
            experiment_id="test_selective",
            agents=[AgentConfig(name="Agent_1")],
            defaults=DefaultConfig(),
            logging=LoggingConfig(
                enabled=True,
                capture_raw_inputs=False,
                capture_raw_outputs=False,
                capture_memory_context=False,
                include_processing_times=False
            )
        )
        
        selective_logger = ExperimentLogger(selective_config.experiment_id, selective_config)
        
        # Log interaction with all data
        selective_logger.log_agent_interaction(
            agent_id="agent_1",
            agent_name="Agent_1",
            round_num=1,
            speaking_position=1,
            input_prompt="Should not be logged",
            raw_llm_response="Should not be logged",
            processing_time_ms=1000
        )
        
        # Log memory event
        selective_logger.log_memory_event(
            agent_id="agent_1",
            round_num=1,
            memory_context="Should not be logged"
        )
        
        # Check that disabled data is not included
        interaction = selective_logger.agent_interactions[0]
        assert "input_prompt" not in interaction
        assert "raw_llm_response" not in interaction
        assert "processing_time_ms" not in interaction
        
        memory_event = selective_logger.memory_events[0]
        assert "memory_context_provided" not in memory_event
    
    def test_get_experiment_summary(self):
        """Test experiment summary functionality."""
        # Add some data
        self.logger.log_agent_interaction(
            agent_id="agent_1", agent_name="Agent_1", round_num=1, speaking_position=1
        )
        self.logger.log_memory_event(agent_id="agent_1", round_num=1)
        self.logger.log_evaluation("initial", "agent_1", "Agent_1", [])
        
        summary = self.logger.get_experiment_summary()
        
        assert summary["experiment_id"] == "test_logging"
        assert summary["agent_interactions_count"] == 1
        assert summary["memory_events_count"] == 1
        assert summary["initial_evaluations_count"] == 1
        assert summary["final_evaluations_count"] == 0
        assert summary["consensus_result_available"] == False
        assert summary["performance_metrics_available"] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])