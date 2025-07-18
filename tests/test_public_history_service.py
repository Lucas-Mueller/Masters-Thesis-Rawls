"""
Test cases for PublicHistoryService functionality.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.maai.core.models import (
    ExperimentConfig, 
    PublicHistoryMode, 
    SummaryAgentConfig, 
    DeliberationResponse, 
    PrincipleChoice,
    RoundSummary
)
from src.maai.services.public_history_service import PublicHistoryService


class TestPublicHistoryService:
    """Test cases for PublicHistoryService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create test configuration
        self.config = ExperimentConfig(
            experiment_id="test_public_history",
            agents=[],
            public_history_mode=PublicHistoryMode.FULL,
            summary_agent=SummaryAgentConfig(
                model="gpt-4.1-mini",
                temperature=0.1,
                max_tokens=1000
            )
        )
        
        # Create test responses
        self.test_responses = [
            DeliberationResponse(
                agent_id="agent_1",
                agent_name="Agent_1",
                public_message="I think we should focus on maximizing minimum income.",
                private_memory_entry=None,
                updated_choice=PrincipleChoice(
                    principle_id=1,
                    principle_name="Maximize the Minimum Income",
                    reasoning="Focus on worst-off"
                ),
                round_number=1,
                timestamp=datetime.now(),
                speaking_position=1
            ),
            DeliberationResponse(
                agent_id="agent_2",
                agent_name="Agent_2",
                public_message="I prefer maximizing average income for overall prosperity.",
                private_memory_entry=None,
                updated_choice=PrincipleChoice(
                    principle_id=2,
                    principle_name="Maximize the Average Income",
                    reasoning="Overall prosperity"
                ),
                round_number=1,
                timestamp=datetime.now(),
                speaking_position=2
            )
        ]
    
    def test_init_full_mode(self):
        """Test initialization with full history mode."""
        service = PublicHistoryService(self.config)
        assert service.mode == PublicHistoryMode.FULL
        assert service.config == self.config
        assert len(service.round_summaries) == 0
    
    def test_init_summarized_mode(self):
        """Test initialization with summarized history mode."""
        config = ExperimentConfig(
            experiment_id="test_summarized",
            agents=[],
            public_history_mode=PublicHistoryMode.SUMMARIZED
        )
        service = PublicHistoryService(config)
        assert service.mode == PublicHistoryMode.SUMMARIZED
        assert service.should_generate_summaries() == True
    
    @pytest.mark.asyncio
    async def test_build_full_public_context(self):
        """Test building full public context."""
        service = PublicHistoryService(self.config)
        
        # Test with previous and current round responses
        previous_responses = [self.test_responses[0]]
        current_responses = [self.test_responses[1]]
        
        context = await service.build_public_context(
            current_round=2,
            current_round_speakers=current_responses,
            all_previous_responses=previous_responses,
            agent_current_choice="Principle 1"
        )
        
        # Verify context includes previous rounds
        assert "PREVIOUS ROUNDS:" in context
        assert "Round 1" in context
        assert "Agent_1" in context
        assert "maximizing minimum income" in context
        
        # Verify current round is included
        assert "Current Round 2" in context
        assert "Agent_2" in context
        assert "maximizing average income" in context
        
        # Verify agent's current choice is included
        assert "Your current choice: Principle 1" in context
    
    @pytest.mark.asyncio
    async def test_build_summarized_public_context_empty(self):
        """Test building summarized public context with no summaries."""
        config = ExperimentConfig(
            experiment_id="test_summarized",
            agents=[],
            public_history_mode=PublicHistoryMode.SUMMARIZED
        )
        service = PublicHistoryService(config)
        
        context = await service.build_public_context(
            current_round=2,
            current_round_speakers=self.test_responses,
            all_previous_responses=[],
            agent_current_choice="Principle 1"
        )
        
        # Should only show current round (no previous summaries)
        assert "Current Round 2" in context
        assert "SPEAKERS IN THIS ROUND SO FAR:" in context
        assert "Your current choice: Principle 1" in context
        assert "PREVIOUS ROUNDS SUMMARY:" not in context
    
    @pytest.mark.asyncio
    async def test_build_summarized_public_context_with_summaries(self):
        """Test building summarized public context with existing summaries."""
        config = ExperimentConfig(
            experiment_id="test_summarized",
            agents=[],
            public_history_mode=PublicHistoryMode.SUMMARIZED
        )
        service = PublicHistoryService(config)
        
        # Add a test summary
        test_summary = RoundSummary(
            round_number=1,
            summary_text="Round 1 focused on principle preferences. Agent_1 supported minimum income focus.",
            key_arguments={"Agent_1": "Focus on worst-off"},
            principle_preferences={"Principle 1": ["Agent_1"]},
            consensus_status="No consensus",
            summary_agent_model="gpt-4.1-mini"
        )
        service.add_round_summary(test_summary)
        
        context = await service.build_public_context(
            current_round=2,
            current_round_speakers=self.test_responses,
            all_previous_responses=[],
            agent_current_choice="Principle 2"
        )
        
        # Should show previous summary and current round
        assert "PREVIOUS ROUNDS SUMMARY:" in context
        assert "Round 1 Summary" in context
        assert "Agent_1 supported minimum income focus" in context
        assert "Current Round 2" in context
        assert "Your current choice: Principle 2" in context
    
    @pytest.mark.asyncio
    async def test_generate_round_summary_empty(self):
        """Test generating summary for empty round."""
        config = ExperimentConfig(
            experiment_id="test_summarized",
            agents=[],
            public_history_mode=PublicHistoryMode.SUMMARIZED
        )
        service = PublicHistoryService(config)
        
        summary = await service.generate_round_summary(1, [])
        
        assert summary.round_number == 1
        assert "No discussion occurred" in summary.summary_text
        assert len(summary.key_arguments) == 0
        assert len(summary.principle_preferences) == 0
        assert summary.consensus_status == "No activity"
    
    @pytest.mark.asyncio
    async def test_generate_round_summary_with_mock_agent(self):
        """Test generating summary with mocked summary agent."""
        config = ExperimentConfig(
            experiment_id="test_summarized",
            agents=[],
            public_history_mode=PublicHistoryMode.SUMMARIZED
        )
        service = PublicHistoryService(config)
        
        # Mock the summary agent
        mock_agent = AsyncMock()
        mock_agent.generate_round_summary.return_value = {
            "summary_text": "## Round 1 Summary\n\nTest summary content",
            "key_arguments": {"Agent_1": "Test argument"},
            "principle_preferences": {"Principle 1": ["Agent_1"]},
            "consensus_status": "No consensus reached"
        }
        service._summary_agent = mock_agent
        
        summary = await service.generate_round_summary(1, self.test_responses)
        
        assert summary.round_number == 1
        assert "Test summary content" in summary.summary_text
        assert "Agent_1" in summary.key_arguments
        assert "Principle 1" in summary.principle_preferences
        assert summary.consensus_status == "No consensus reached"
        assert summary.summary_agent_model == "gpt-4.1-mini"
    
    def test_summary_management(self):
        """Test summary management methods."""
        service = PublicHistoryService(self.config)
        
        # Test empty state
        assert len(service.get_round_summaries()) == 0
        
        # Add a summary
        test_summary = RoundSummary(
            round_number=1,
            summary_text="Test summary",
            key_arguments={},
            principle_preferences={},
            consensus_status="Test",
            summary_agent_model="gpt-4.1-mini"
        )
        service.add_round_summary(test_summary)
        
        # Verify summary was added
        summaries = service.get_round_summaries()
        assert len(summaries) == 1
        assert summaries[0].round_number == 1
        assert summaries[0].summary_text == "Test summary"
        
        # Test clear
        service.clear_summaries()
        assert len(service.get_round_summaries()) == 0
    
    def test_mode_detection(self):
        """Test mode detection methods."""
        # Test full mode
        service = PublicHistoryService(self.config)
        assert service.get_mode() == PublicHistoryMode.FULL
        assert service.should_generate_summaries() == False
        
        # Test summarized mode
        config = ExperimentConfig(
            experiment_id="test_summarized",
            agents=[],
            public_history_mode=PublicHistoryMode.SUMMARIZED
        )
        service = PublicHistoryService(config)
        assert service.get_mode() == PublicHistoryMode.SUMMARIZED
        assert service.should_generate_summaries() == True


# Integration test
@pytest.mark.asyncio
async def test_public_history_integration():
    """Integration test for public history service."""
    config = ExperimentConfig(
        experiment_id="integration_test",
        agents=[],
        public_history_mode=PublicHistoryMode.FULL
    )
    
    service = PublicHistoryService(config)
    
    # Create test data
    responses = [
        DeliberationResponse(
            agent_id="agent_1",
            agent_name="Agent_1",
            public_message="Test message 1",
            private_memory_entry=None,
            updated_choice=PrincipleChoice(
                principle_id=1,
                principle_name="Test Principle",
                reasoning="Test reasoning"
            ),
            round_number=1,
            timestamp=datetime.now(),
            speaking_position=1
        )
    ]
    
    # Test full context building
    context = await service.build_public_context(
        current_round=2,
        current_round_speakers=[],
        all_previous_responses=responses,
        agent_current_choice="Principle 1"
    )
    
    assert "PREVIOUS ROUNDS:" in context
    assert "Round 1" in context
    assert "Agent_1" in context
    assert "Test message 1" in context
    assert "Your current choice: Principle 1" in context


if __name__ == "__main__":
    # Run a simple test
    asyncio.run(test_public_history_integration())
    print("Basic integration test passed!")