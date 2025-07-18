"""
Unit tests for DecomposedMemoryStrategy
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Add src to path for testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maai.services.memory_service import (
    DecomposedMemoryStrategy, 
    create_memory_strategy,
    FullMemoryStrategy,
    RecentMemoryStrategy
)
from maai.core.models import MemoryEntry, DeliberationResponse, PrincipleChoice
from maai.agents.enhanced import DeliberationAgent


class TestDecomposedMemoryStrategy:
    """Test suite for DecomposedMemoryStrategy"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.strategy = DecomposedMemoryStrategy()
        self.mock_agent = Mock(spec=DeliberationAgent)
        self.mock_agent.name = "TestAgent"
        
        # Mock transcript data
        self.sample_transcript = [
            DeliberationResponse(
                agent_id="agent_1",
                agent_name="Agent_1", 
                public_message="I believe we should choose principle 1 for fairness.",
                updated_choice=PrincipleChoice(
                    principle_id=1, 
                    principle_name="Maximize the Minimum Income",
                    reasoning="Fairness is key"
                ),
                round_number=1,
                timestamp=datetime.now(),
                speaking_position=1
            ),
            DeliberationResponse(
                agent_id="agent_2",
                agent_name="Agent_2",
                public_message="I prefer principle 2 for efficiency reasons.",
                updated_choice=PrincipleChoice(
                    principle_id=2, 
                    principle_name="Maximize the Average Income",
                    reasoning="Efficiency matters"
                ),
                round_number=1,
                timestamp=datetime.now(),
                speaking_position=2
            )
        ]
    
    def test_strategy_interface_compliance(self):
        """Test that DecomposedMemoryStrategy implements the MemoryStrategy interface"""
        # Test required abstract methods
        assert hasattr(self.strategy, 'should_include_memory')
        assert hasattr(self.strategy, 'get_memory_context_limit')
        assert hasattr(self.strategy, 'generate_memory_entry')
        
        # Test basic method calls
        mock_entry = Mock(spec=MemoryEntry)
        assert self.strategy.should_include_memory(mock_entry, 1) == True
        assert isinstance(self.strategy.get_memory_context_limit(), int)
    
    def test_agent_selection_logic(self):
        """Test the agent selection logic for focused analysis"""
        target = self.strategy._select_analysis_target(self.mock_agent, self.sample_transcript, 2)
        
        # Should return the most recent speaker who isn't the current agent
        assert target in ["Agent_1", "Agent_2"]
    
    def test_agent_selection_excludes_self(self):
        """Test that agent selection excludes the current agent"""
        self.mock_agent.name = "Agent_1"
        target = self.strategy._select_analysis_target(self.mock_agent, self.sample_transcript, 2)
        
        # Should not return Agent_1 since that's the current agent
        assert target != "Agent_1"
        assert target == "Agent_2"  # Should be Agent_2
    
    def test_agent_selection_empty_transcript(self):
        """Test agent selection with empty transcript"""
        target = self.strategy._select_analysis_target(self.mock_agent, [], 1)
        assert target is None
    
    @pytest.mark.asyncio
    async def test_factual_recap_generation(self):
        """Test the factual recap generation step"""
        with patch('maai.services.memory_service.Runner.run') as mock_runner:
            with patch('maai.services.memory_service.ItemHelpers.text_message_outputs') as mock_item_helpers:
                # Mock the LLM response
                mock_item_helpers.return_value = "Agent_1 chose principle 1, Agent_2 chose principle 2"
                
                result = await self.strategy._generate_factual_recap(
                    self.mock_agent, 2, self.sample_transcript
                )
                
                # Verify method was called and returned expected result
                mock_runner.assert_called_once()
                assert result == "Agent_1 chose principle 1, Agent_2 chose principle 2"
    
    @pytest.mark.asyncio
    async def test_agent_analysis_generation(self):
        """Test the agent analysis generation step"""
        with patch('maai.services.memory_service.Runner.run') as mock_runner:
            with patch('maai.services.memory_service.ItemHelpers.text_message_outputs') as mock_item_helpers:
                mock_item_helpers.return_value = "Agent_1 shows consistent preference for fairness"
                
                factual_recap = "Test facts"
                result = await self.strategy._generate_agent_analysis(
                    self.mock_agent, 2, self.sample_transcript, factual_recap
                )
                
                mock_runner.assert_called_once()
                assert result == "Agent_1 shows consistent preference for fairness"
    
    @pytest.mark.asyncio 
    async def test_strategic_action_generation(self):
        """Test the strategic action generation step"""
        with patch('maai.services.memory_service.Runner.run') as mock_runner:
            with patch('maai.services.memory_service.ItemHelpers.text_message_outputs') as mock_item_helpers:
                mock_item_helpers.return_value = "Focus on efficiency concerns to persuade Agent_2"
                
                result = await self.strategy._generate_strategic_action(
                    self.mock_agent, 2, "Test facts", "Test analysis"
                )
                
                mock_runner.assert_called_once()
                assert result == "Focus on efficiency concerns to persuade Agent_2"
    
    @pytest.mark.asyncio
    async def test_complete_memory_generation(self):
        """Test the complete memory entry generation process"""
        with patch.object(self.strategy, '_generate_factual_recap') as mock_facts:
            with patch.object(self.strategy, '_generate_agent_analysis') as mock_analysis:
                with patch.object(self.strategy, '_generate_strategic_action') as mock_strategy:
                    
                    # Mock the three steps
                    mock_facts.return_value = "Test factual recap"
                    mock_analysis.return_value = "Test agent analysis"
                    mock_strategy.return_value = "Test strategic action"
                    
                    memory_entry = await self.strategy.generate_memory_entry(
                        self.mock_agent, 2, 1, self.sample_transcript, "context"
                    )
                    
                    # Verify all steps were called
                    mock_facts.assert_called_once()
                    mock_analysis.assert_called_once()
                    mock_strategy.assert_called_once()
                    
                    # Verify memory entry structure
                    assert isinstance(memory_entry, MemoryEntry)
                    assert memory_entry.round_number == 2
                    assert memory_entry.speaking_position == 1
                    assert memory_entry.situation_assessment == "Test factual recap"
                    assert memory_entry.other_agents_analysis == "Test agent analysis"
                    assert memory_entry.strategy_update == "Test strategic action"


class TestMemoryStrategyFactory:
    """Test suite for memory strategy factory function"""
    
    def test_create_full_strategy(self):
        """Test creating full memory strategy"""
        strategy = create_memory_strategy("full")
        assert isinstance(strategy, FullMemoryStrategy)
    
    def test_create_recent_strategy(self):
        """Test creating recent memory strategy"""
        strategy = create_memory_strategy("recent")
        assert isinstance(strategy, RecentMemoryStrategy)
    
    
    def test_create_decomposed_strategy(self):
        """Test creating decomposed memory strategy"""
        strategy = create_memory_strategy("decomposed")
        assert isinstance(strategy, DecomposedMemoryStrategy)
    
    def test_invalid_strategy_name(self):
        """Test error handling for invalid strategy names"""
        with pytest.raises(ValueError) as exc_info:
            create_memory_strategy("invalid_strategy")
        
        assert "Unknown memory strategy: invalid_strategy" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])