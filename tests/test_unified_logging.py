"""
Test suite for the new unified agent-centric logging system.
Tests the complete agent-centric JSON structure and data capture.
"""

import json
import tempfile
import asyncio
import warnings
from pathlib import Path
from datetime import datetime
import sys
import os

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.maai.core.models import ExperimentConfig, LoggingConfig, DefaultConfig, AgentConfig, ConsensusResult, PrincipleChoice, ExperimentResults, OutputConfig
from src.maai.services.experiment_logger import ExperimentLogger


class TestUnifiedLogging:
    """Test cases for the new unified agent-centric logging system."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = ExperimentConfig(
            experiment_id="test_unified_logging",
            max_rounds=3,
            agents=[
                AgentConfig(name="Agent_1", model="gpt-4.1-mini", personality="You are an economist."),
                AgentConfig(name="Agent_2", model="gpt-4.1", personality="You are a philosopher."),
                AgentConfig(name="Agent_3", model="gpt-4.1-mini", personality="You are a pragmatist.")
            ],
            defaults=DefaultConfig(
                model="gpt-4.1-mini",
                personality="You are an agent tasked to design a future society.",
                temperature=0.0
            ),
            global_temperature=0.0,
            logging=LoggingConfig(
                enabled=True,
                capture_raw_inputs=True,
                capture_raw_outputs=True,
                capture_memory_context=True,
                capture_memory_steps=True,
                include_processing_times=True
            ),
            output=OutputConfig(
                directory="test_results",
                formats=["json"]
            )
        )
        
        self.temp_dir = tempfile.mkdtemp()
        self.logger = ExperimentLogger(self.config.experiment_id, self.config)
    
    def test_logger_initialization_agent_centric(self):
        """Test logger initializes with agent-centric structure."""
        assert self.logger.experiment_id == "test_unified_logging"
        assert len(self.logger.agent_data) == 3
        
        # Check agent data structure
        assert "Agent_1" in self.logger.agent_data
        assert "Agent_2" in self.logger.agent_data
        assert "Agent_3" in self.logger.agent_data
        
        # Check overall data for each agent
        agent_1_data = self.logger.agent_data["Agent_1"]
        assert "overall" in agent_1_data
        assert agent_1_data["overall"]["model"] == "gpt-4.1-mini"
        assert agent_1_data["overall"]["persona"] == "You are an economist."
        assert agent_1_data["overall"]["temperature"] == 0.0
        
        agent_2_data = self.logger.agent_data["Agent_2"]
        assert agent_2_data["overall"]["model"] == "gpt-4.1"
        assert agent_2_data["overall"]["persona"] == "You are a philosopher."
        
        # Check experiment metadata
        metadata = self.logger.experiment_metadata
        assert metadata["experiment_id"] == "test_unified_logging"
        assert metadata["max_rounds"] == 3
        assert metadata["decision_rule"] == "unanimity"
    
    def test_initial_evaluation_logging(self):
        """Test round_0 (initial evaluation) logging."""
        # Log initial evaluation for Agent_1
        self.logger.log_initial_evaluation(
            agent_id="Agent_1",
            input_prompt="Please rate each distributive justice principle on a scale of 1-4...",
            raw_response="Based on economic principles, I would rate: Principle 1 - strongly agree...",
            rating_likert="strongly agree",
            rating_numeric=4
        )
        
        # Log initial evaluation for Agent_2
        self.logger.log_initial_evaluation(
            agent_id="Agent_2",
            input_prompt="Please rate each distributive justice principle on a scale of 1-4...",
            raw_response="From a philosophical perspective, I believe: Principle 1 - agree...",
            rating_likert="agree",
            rating_numeric=3
        )
        
        # Check round_0 data
        agent_1_data = self.logger.agent_data["Agent_1"]
        assert "round_0" in agent_1_data
        round_0_data = agent_1_data["round_0"]
        assert round_0_data["input"] == "Please rate each distributive justice principle on a scale of 1-4..."
        assert round_0_data["output"] == "Based on economic principles, I would rate: Principle 1 - strongly agree..."
        assert round_0_data["rating_likert"] == "strongly agree"
        assert round_0_data["rating_numeric"] == 4
        
        agent_2_data = self.logger.agent_data["Agent_2"]
        assert "round_0" in agent_2_data
        assert agent_2_data["round_0"]["rating_numeric"] == 3
    
    def test_round_deliberation_logging(self):
        """Test round_1+ deliberation logging."""
        # Log round start for Agent_1
        self.logger.log_round_start(
            agent_id="Agent_1",
            round_num=1,
            speaking_order=1,
            public_history="No previous speakers in this round."
        )
        
        # Log memory generation
        self.logger.log_memory_generation(
            agent_id="Agent_1",
            round_num=1,
            memory_content="I recall from round 0 that Agent_2 emphasized fairness concerns...",
            strategy="Focus on economic efficiency while addressing fairness concerns"
        )
        
        # Log agent interactions (sequence of inputs/outputs)
        self.logger.log_agent_interaction(
            agent_id="Agent_1",
            round_num=1,
            interaction_type="memory",
            input_prompt="Generate your private memory for this round...",
            raw_response="I recall from round 0 that Agent_2 emphasized fairness concerns...",
            sequence_num=0
        )
        
        self.logger.log_agent_interaction(
            agent_id="Agent_1",
            round_num=1,
            interaction_type="communication",
            input_prompt="Based on the conversation history, what is your public communication?",
            raw_response="I believe we should prioritize economic efficiency while ensuring basic needs are met...",
            sequence_num=1
        )
        
        self.logger.log_agent_interaction(
            agent_id="Agent_1",
            round_num=1,
            interaction_type="choice",
            input_prompt="What distributive justice principle do you choose?",
            raw_response="Maximize the Average Income",
            sequence_num=2
        )
        
        # Log communication and choice
        self.logger.log_communication(
            agent_id="Agent_1",
            round_num=1,
            communication="I believe we should prioritize economic efficiency while ensuring basic needs are met...",
            choice="Maximize the Average Income"
        )
        
        # Check round_1 data structure
        agent_1_data = self.logger.agent_data["Agent_1"]
        assert "round_1" in agent_1_data
        round_1_data = agent_1_data["round_1"]
        
        # Check all required fields
        assert round_1_data["speaking_order"] == 1
        assert round_1_data["public_history"] == "No previous speakers in this round."
        assert round_1_data["memory"] == "I recall from round 0 that Agent_2 emphasized fairness concerns..."
        assert round_1_data["strategy"] == "Focus on economic efficiency while addressing fairness concerns"
        assert round_1_data["communication"] == "I believe we should prioritize economic efficiency while ensuring basic needs are met..."
        assert round_1_data["choice"] == "Maximize the Average Income"
        
        # Check input_dict and output_dict
        assert "input_dict" in round_1_data
        assert "output_dict" in round_1_data
        assert "0" in round_1_data["input_dict"]
        assert "1" in round_1_data["input_dict"]
        assert "2" in round_1_data["input_dict"]
        assert "0" in round_1_data["output_dict"]
        assert "1" in round_1_data["output_dict"]
        assert "2" in round_1_data["output_dict"]
        
        assert round_1_data["input_dict"]["0"] == "Generate your private memory for this round..."
        assert round_1_data["output_dict"]["1"] == "I believe we should prioritize economic efficiency while ensuring basic needs are met..."
    
    def test_final_consensus_logging(self):
        """Test final consensus logging for each agent."""
        # Log final consensus for each agent
        self.logger.log_final_consensus(
            agent_id="Agent_1",
            agreement_reached=True,
            agreement_choice="Maximize the Minimum Income",
            num_rounds=2,
            satisfaction=3
        )
        
        self.logger.log_final_consensus(
            agent_id="Agent_2",
            agreement_reached=True,
            agreement_choice="Maximize the Minimum Income",
            num_rounds=2,
            satisfaction=4
        )
        
        self.logger.log_final_consensus(
            agent_id="Agent_3",
            agreement_reached=True,
            agreement_choice="Maximize the Minimum Income",
            num_rounds=2,
            satisfaction=3
        )
        
        # Check final data for each agent
        for agent_id in ["Agent_1", "Agent_2", "Agent_3"]:
            agent_data = self.logger.agent_data[agent_id]
            assert "final" in agent_data
            final_data = agent_data["final"]
            assert final_data["agreement_reached"] == True
            assert final_data["agreement_choice"] == "Maximize the Minimum Income"
            assert final_data["num_rounds"] == 2
            assert final_data["satisfaction"] in [3, 4]
    
    def test_experiment_completion_logging(self):
        """Test experiment completion metadata logging."""
        consensus_result = ConsensusResult(
            unanimous=True,
            agreed_principle=PrincipleChoice(
                principle_id=1,
                principle_name="Maximize the Minimum Income",
                reasoning="Best balance of fairness and efficiency"
            ),
            dissenting_agents=[],
            rounds_to_consensus=2,
            total_messages=9
        )
        
        self.logger.log_experiment_completion(
            consensus_result=consensus_result,
            total_rounds=2
        )
        
        # Check experiment metadata
        metadata = self.logger.experiment_metadata
        assert metadata["end_time"] is not None
        assert metadata["total_duration_seconds"] is not None
        assert metadata["final_consensus"] is not None
        
        final_consensus = metadata["final_consensus"]
        assert final_consensus["agreement_reached"] == True
        assert final_consensus["agreed_principle"] == "Maximize the Minimum Income"
        assert final_consensus["num_rounds"] == 2
        assert final_consensus["total_messages"] == 9
    
    def test_unified_json_export(self):
        """Test complete unified JSON export with agent-centric structure."""
        # Set up complete experiment data
        self._setup_complete_experiment_data()
        
        # Export unified JSON
        json_file = self.logger.export_unified_json(self.temp_dir)
        
        # Verify file was created
        assert Path(json_file).exists()
        
        # Load and verify JSON structure
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Check top-level structure
        assert "experiment_metadata" in data
        assert "Agent_1" in data
        assert "Agent_2" in data
        assert "Agent_3" in data
        
        # Check experiment metadata
        metadata = data["experiment_metadata"]
        assert metadata["experiment_id"] == "test_unified_logging"
        assert "start_time" in metadata
        assert "end_time" in metadata
        assert "total_duration_seconds" in metadata
        assert "max_rounds" in metadata
        assert "decision_rule" in metadata
        assert "final_consensus" in metadata
        
        # Check agent structure
        agent_1_data = data["Agent_1"]
        assert "overall" in agent_1_data
        assert "round_0" in agent_1_data
        assert "round_1" in agent_1_data
        assert "final" in agent_1_data
        
        # Check overall data
        overall = agent_1_data["overall"]
        assert overall["model"] == "gpt-4.1-mini"
        assert overall["persona"] == "You are an economist."
        assert overall["temperature"] == 0.0
        assert "instruction" in overall
        
        # Check round_0 structure
        round_0 = agent_1_data["round_0"]
        assert "input" in round_0
        assert "output" in round_0
        assert "rating_likert" in round_0
        assert "rating_numeric" in round_0
        
        # Check round_1 structure
        round_1 = agent_1_data["round_1"]
        assert "speaking_order" in round_1
        assert "public_history" in round_1
        assert "memory" in round_1
        assert "strategy" in round_1
        assert "communication" in round_1
        assert "choice" in round_1
        assert "input_dict" in round_1
        assert "output_dict" in round_1
        
        # Check input_dict and output_dict have string keys
        assert isinstance(list(round_1["input_dict"].keys())[0], str)
        assert isinstance(list(round_1["output_dict"].keys())[0], str)
        
        # Check final structure
        final = agent_1_data["final"]
        assert "agreement_reached" in final
        assert "agreement_choice" in final
        assert "num_rounds" in final
        assert "satisfaction" in final
    
    def test_legacy_compatibility(self):
        """Test legacy method compatibility."""
        # Test that legacy export method still works
        json_file = self.logger.export_complete_json(self.temp_dir)
        assert Path(json_file).exists()
        
        # Load and verify it has the same structure as unified export
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        assert "experiment_metadata" in data
        assert "Agent_1" in data
        assert "Agent_2" in data
        assert "Agent_3" in data
    
    def test_output_directory_configuration(self):
        """Test that output directory configuration works correctly."""
        # Test that config has output directory
        assert hasattr(self.config, 'output')
        assert self.config.output.directory == "test_results"
        
        # Test that logger uses config output directory
        test_path = self.logger.export_unified_json()
        assert "test_results" in test_path
        
        # Test override functionality
        override_path = self.logger.export_unified_json("custom_output")
        assert "custom_output" in override_path
    
    def test_get_experiment_summary(self):
        """Test experiment summary functionality."""
        # Add some test data
        self.logger.log_initial_evaluation("Agent_1", "test input", "test output", "agree", 3)
        self.logger.log_round_start("Agent_1", 1, 1, "test history")
        self.logger.log_agent_interaction("Agent_1", 1, "test", "input", "output", 0)
        self.logger.log_final_consensus("Agent_1", True, "test principle", 2, 3)
        
        summary = self.logger.get_experiment_summary()
        
        assert summary["experiment_id"] == "test_unified_logging"
        assert summary["total_agents"] == 3
        assert summary["total_rounds"] == 1  # Only deliberation rounds (round_1), not round_0
        assert summary["total_interactions"] == 1
        assert summary["experiment_completed"] == False
        assert summary["consensus_recorded"] == False
        
        # Complete experiment
        self.logger.log_experiment_completion()
        summary = self.logger.get_experiment_summary()
        assert summary["experiment_completed"] == True
    
    def test_multiple_rounds_logging(self):
        """Test logging multiple rounds of deliberation."""
        # Test multiple rounds for multiple agents
        for round_num in range(1, 4):  # Rounds 1, 2, 3
            for agent_id in ["Agent_1", "Agent_2", "Agent_3"]:
                self.logger.log_round_start(
                    agent_id=agent_id,
                    round_num=round_num,
                    speaking_order=1,
                    public_history=f"Round {round_num} history"
                )
                
                self.logger.log_memory_generation(
                    agent_id=agent_id,
                    round_num=round_num,
                    memory_content=f"Round {round_num} memory",
                    strategy=f"Round {round_num} strategy"
                )
                
                self.logger.log_communication(
                    agent_id=agent_id,
                    round_num=round_num,
                    communication=f"Round {round_num} communication",
                    choice=f"Principle {round_num}"
                )
        
        # Check that all rounds are present for all agents
        for agent_id in ["Agent_1", "Agent_2", "Agent_3"]:
            agent_data = self.logger.agent_data[agent_id]
            assert "round_1" in agent_data
            assert "round_2" in agent_data
            assert "round_3" in agent_data
            
            assert agent_data["round_1"]["memory"] == "Round 1 memory"
            assert agent_data["round_2"]["strategy"] == "Round 2 strategy"
            assert agent_data["round_3"]["communication"] == "Round 3 communication"
    
    def _setup_complete_experiment_data(self):
        """Set up complete experiment data for testing."""
        # Initial evaluations
        for agent_id in ["Agent_1", "Agent_2", "Agent_3"]:
            self.logger.log_initial_evaluation(
                agent_id=agent_id,
                input_prompt=f"Rate principles for {agent_id}",
                raw_response=f"Response from {agent_id}",
                rating_likert="agree",
                rating_numeric=3
            )
        
        # Round 1 deliberation
        for i, agent_id in enumerate(["Agent_1", "Agent_2", "Agent_3"]):
            self.logger.log_round_start(
                agent_id=agent_id,
                round_num=1,
                speaking_order=i+1,
                public_history=f"Round 1 history for {agent_id}"
            )
            
            self.logger.log_memory_generation(
                agent_id=agent_id,
                round_num=1,
                memory_content=f"Round 1 memory for {agent_id}",
                strategy=f"Round 1 strategy for {agent_id}"
            )
            
            self.logger.log_agent_interaction(
                agent_id=agent_id,
                round_num=1,
                interaction_type="memory",
                input_prompt=f"Memory input for {agent_id}",
                raw_response=f"Memory output for {agent_id}",
                sequence_num=0
            )
            
            self.logger.log_agent_interaction(
                agent_id=agent_id,
                round_num=1,
                interaction_type="communication",
                input_prompt=f"Communication input for {agent_id}",
                raw_response=f"Communication output for {agent_id}",
                sequence_num=1
            )
            
            self.logger.log_communication(
                agent_id=agent_id,
                round_num=1,
                communication=f"Communication from {agent_id}",
                choice="Maximize the Minimum Income"
            )
        
        # Final consensus
        for agent_id in ["Agent_1", "Agent_2", "Agent_3"]:
            self.logger.log_final_consensus(
                agent_id=agent_id,
                agreement_reached=True,
                agreement_choice="Maximize the Minimum Income",
                num_rounds=1,
                satisfaction=3
            )
        
        # Experiment completion
        consensus_result = ConsensusResult(
            unanimous=True,
            agreed_principle=PrincipleChoice(
                principle_id=1,
                principle_name="Maximize the Minimum Income",
                reasoning="Test reasoning"
            ),
            dissenting_agents=[],
            rounds_to_consensus=1,
            total_messages=3
        )
        
        self.logger.log_experiment_completion(
            consensus_result=consensus_result,
            total_rounds=1
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])