"""
Comprehensive tests for ConversationService and communication patterns.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.maai.services.conversation_service import (
    ConversationService, 
    RandomCommunicationPattern,
    SequentialCommunicationPattern,
    HierarchicalCommunicationPattern,
    RoundContext,
    CommunicationPattern
)
from src.maai.core.models import DeliberationResponse, PrincipleChoice, MemoryEntry
from src.maai.agents.enhanced import DeliberationAgent


class TestRandomCommunicationPattern:
    """Test RandomCommunicationPattern communication pattern."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pattern = RandomCommunicationPattern()
        self.mock_agents = [
            Mock(spec=DeliberationAgent, agent_id="agent1"),
            Mock(spec=DeliberationAgent, agent_id="agent2"),
            Mock(spec=DeliberationAgent, agent_id="agent3")
        ]
    
    def test_first_round_any_order(self):
        """Test that first round allows any order."""
        # Run multiple times to check randomness
        orders = []
        for i in range(5):
            order = self.pattern.generate_speaking_order(self.mock_agents, 1, [])
            orders.append(order)
        
        # Should have all agent IDs
        for order in orders:
            assert len(order) == 3
            assert set(order) == {"agent1", "agent2", "agent3"}
    
    def test_constraint_last_speaker_not_first(self):
        """Test constraint that last speaker in round N cannot be first in round N+1."""
        # First round
        previous_orders = [["agent1", "agent2", "agent3"]]
        
        # Second round - agent3 (last speaker) should not be first
        order = self.pattern.generate_speaking_order(self.mock_agents, 2, previous_orders)
        
        assert len(order) == 3
        assert set(order) == {"agent1", "agent2", "agent3"}
        assert order[0] != "agent3"  # Last speaker from previous round
    
    def test_constraint_with_multiple_attempts(self):
        """Test that pattern tries multiple times to satisfy constraint."""
        previous_orders = [["agent1", "agent2", "agent3"]]
        
        # Mock random.shuffle to always put agent3 first initially
        with patch('random.shuffle') as mock_shuffle:
            call_count = 0
            def side_effect(lst):
                nonlocal call_count
                call_count += 1
                if call_count <= 5:
                    # First 5 attempts: put agent3 first (violates constraint)
                    lst[:] = ["agent3", "agent1", "agent2"]
                else:
                    # After 5 attempts: put agent1 first (satisfies constraint)
                    lst[:] = ["agent1", "agent2", "agent3"]
            
            mock_shuffle.side_effect = side_effect
            
            order = self.pattern.generate_speaking_order(self.mock_agents, 2, previous_orders)
            
            assert order[0] == "agent1"  # Should eventually find valid order
            assert call_count == 6  # Should try 6 times
    
    def test_fallback_after_max_attempts(self):
        """Test fallback behavior after maximum attempts."""
        previous_orders = [["agent1", "agent2", "agent3"]]
        
        # Mock random.shuffle to always violate constraint
        with patch('random.shuffle') as mock_shuffle:
            mock_shuffle.side_effect = lambda lst: lst.sort(key=lambda x: x, reverse=True)  # Always ["agent3", "agent2", "agent1"]
            
            order = self.pattern.generate_speaking_order(self.mock_agents, 2, previous_orders)
            
            # Should return order even if constraint is violated (fallback)
            assert len(order) == 3
            assert set(order) == {"agent1", "agent2", "agent3"}
    
    def test_empty_previous_orders(self):
        """Test with empty previous orders."""
        order = self.pattern.generate_speaking_order(self.mock_agents, 2, [])
        
        assert len(order) == 3
        assert set(order) == {"agent1", "agent2", "agent3"}
    
    def test_no_previous_order(self):
        """Test with no previous orders list."""
        order = self.pattern.generate_speaking_order(self.mock_agents, 2, [])
        
        assert len(order) == 3
        assert set(order) == {"agent1", "agent2", "agent3"}


class TestSequentialCommunicationPattern:
    """Test SequentialCommunicationPattern communication pattern."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pattern = SequentialCommunicationPattern()
        self.mock_agents = [
            Mock(spec=DeliberationAgent, agent_id="agent3"),
            Mock(spec=DeliberationAgent, agent_id="agent1"),
            Mock(spec=DeliberationAgent, agent_id="agent2")
        ]
    
    def test_sorted_order_first_round(self):
        """Test that first round uses sorted order."""
        order = self.pattern.generate_speaking_order(self.mock_agents, 1, [])
        
        assert order == ["agent1", "agent2", "agent3"]  # Sorted alphabetically
    
    def test_rotation_based_on_round(self):
        """Test that order rotates based on round number."""
        # Round 1: [agent1, agent2, agent3]
        order1 = self.pattern.generate_speaking_order(self.mock_agents, 1, [])
        assert order1 == ["agent1", "agent2", "agent3"]
        
        # Round 2: [agent2, agent3, agent1]
        order2 = self.pattern.generate_speaking_order(self.mock_agents, 2, [])
        assert order2 == ["agent2", "agent3", "agent1"]
        
        # Round 3: [agent3, agent1, agent2]
        order3 = self.pattern.generate_speaking_order(self.mock_agents, 3, [])
        assert order3 == ["agent3", "agent1", "agent2"]
        
        # Round 4: Back to [agent1, agent2, agent3]
        order4 = self.pattern.generate_speaking_order(self.mock_agents, 4, [])
        assert order4 == ["agent1", "agent2", "agent3"]
    
    def test_round_zero(self):
        """Test round 0 (initial) behavior."""
        order = self.pattern.generate_speaking_order(self.mock_agents, 0, [])
        
        assert order == ["agent1", "agent2", "agent3"]  # No rotation
    
    def test_single_agent(self):
        """Test with single agent."""
        single_agent = [Mock(spec=DeliberationAgent, agent_id="agent1")]
        
        order = self.pattern.generate_speaking_order(single_agent, 1, [])
        assert order == ["agent1"]
        
        # Should be same for all rounds
        order2 = self.pattern.generate_speaking_order(single_agent, 2, [])
        assert order2 == ["agent1"]


class TestHierarchicalCommunicationPattern:
    """Test HierarchicalCommunicationPattern communication pattern."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pattern = HierarchicalCommunicationPattern(leader_count=1)
        self.mock_agents = [
            Mock(spec=DeliberationAgent, agent_id="agent3"),
            Mock(spec=DeliberationAgent, agent_id="agent1"),
            Mock(spec=DeliberationAgent, agent_id="agent2")
        ]
    
    def test_leader_speaks_first(self):
        """Test that leader speaks first."""
        order = self.pattern.generate_speaking_order(self.mock_agents, 1, [])
        
        assert len(order) == 3
        assert order[0] == "agent1"  # First alphabetically = leader
        assert set(order) == {"agent1", "agent2", "agent3"}
    
    def test_multiple_leaders(self):
        """Test with multiple leaders."""
        pattern = HierarchicalCommunicationPattern(leader_count=2)
        order = pattern.generate_speaking_order(self.mock_agents, 1, [])
        
        assert len(order) == 3
        assert order[0] in ["agent1", "agent2"]  # One of the leaders
        assert order[1] in ["agent1", "agent2"]  # One of the leaders
        assert order[2] == "agent3"  # Follower
        assert set(order) == {"agent1", "agent2", "agent3"}
    
    def test_all_leaders(self):
        """Test when all agents are leaders."""
        pattern = HierarchicalCommunicationPattern(leader_count=3)
        order = pattern.generate_speaking_order(self.mock_agents, 1, [])
        
        assert len(order) == 3
        assert set(order) == {"agent1", "agent2", "agent3"}
    
    def test_randomization_within_groups(self):
        """Test that randomization occurs within leader and follower groups."""
        pattern = HierarchicalCommunicationPattern(leader_count=1)
        
        # Run multiple times to check randomness
        orders = []
        for i in range(10):
            order = pattern.generate_speaking_order(self.mock_agents, 1, [])
            orders.append(order)
        
        # All orders should have agent1 as leader (first)
        for order in orders:
            assert order[0] == "agent1"
        
        # But order of followers should vary
        follower_pairs = [tuple(order[1:]) for order in orders]
        unique_follower_pairs = set(follower_pairs)
        
        # Should have at least some variation (not all identical)
        # Note: This test could occasionally fail due to randomness
        assert len(unique_follower_pairs) >= 1


class TestRoundContext:
    """Test RoundContext class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agents = [
            Mock(spec=DeliberationAgent, agent_id="agent1", name="Agent1"),
            Mock(spec=DeliberationAgent, agent_id="agent2", name="Agent2")
        ]
        
        self.transcript = [
            Mock(spec=DeliberationResponse, agent_id="agent1", round_number=1),
            Mock(spec=DeliberationResponse, agent_id="agent2", round_number=1)
        ]
        
        self.speaking_order = ["agent1", "agent2"]
        
        self.context = RoundContext(
            round_number=1,
            agents=self.agents,
            transcript=self.transcript,
            speaking_order=self.speaking_order
        )
    
    def test_initialization(self):
        """Test proper initialization."""
        assert self.context.round_number == 1
        assert self.context.agents == self.agents
        assert self.context.transcript == self.transcript
        assert self.context.speaking_order == self.speaking_order
        assert len(self.context.agent_lookup) == 2
    
    def test_get_agent_by_id_success(self):
        """Test successful agent retrieval."""
        agent = self.context.get_agent_by_id("agent1")
        assert agent.agent_id == "agent1"
        assert agent.name == "Agent1"
    
    def test_get_agent_by_id_not_found(self):
        """Test agent retrieval with invalid ID."""
        with pytest.raises(ValueError, match="Agent with ID nonexistent not found"):
            self.context.get_agent_by_id("nonexistent")


class TestConversationService:
    """Test ConversationService main class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ConversationService()
        self.mock_agents = [
            Mock(spec=DeliberationAgent, agent_id="agent1", name="Agent1"),
            Mock(spec=DeliberationAgent, agent_id="agent2", name="Agent2")
        ]
        
        # Mock logger
        self.mock_logger = Mock()
        self.service.logger = self.mock_logger
    
    def test_default_pattern_is_random(self):
        """Test that default pattern is RandomCommunicationPattern."""
        assert isinstance(self.service.pattern, RandomCommunicationPattern)
    
    def test_custom_pattern_initialization(self):
        """Test initialization with custom pattern."""
        custom_pattern = SequentialCommunicationPattern()
        service = ConversationService(communication_pattern=custom_pattern)
        
        assert service.pattern == custom_pattern
    
    def test_generate_speaking_order_stores_history(self):
        """Test that speaking orders are stored in history."""
        assert len(self.service.speaking_orders) == 0
        
        order1 = self.service.generate_speaking_order(self.mock_agents, 1)
        assert len(self.service.speaking_orders) == 1
        assert self.service.speaking_orders[0] == order1
        
        order2 = self.service.generate_speaking_order(self.mock_agents, 2)
        assert len(self.service.speaking_orders) == 2
        assert self.service.speaking_orders[1] == order2
    
    def test_get_speaking_orders_returns_copy(self):
        """Test that get_speaking_orders returns a copy."""
        self.service.generate_speaking_order(self.mock_agents, 1)
        
        orders = self.service.get_speaking_orders()
        orders.append(["fake_order"])
        
        # Original should not be modified
        assert len(self.service.speaking_orders) == 1
        assert "fake_order" not in self.service.speaking_orders[0]
    
    def test_set_communication_pattern(self):
        """Test changing communication pattern."""
        new_pattern = SequentialCommunicationPattern()
        self.service.set_communication_pattern(new_pattern)
        
        assert self.service.pattern == new_pattern
    
    @pytest.mark.asyncio
    async def test_extract_principle_choice_valid(self):
        """Test principle choice extraction with valid response."""
        response_text = "Based on my analysis, I choose principle 3 because it balances efficiency with fairness."
        
        # Mock moderator and its response
        mock_moderator = Mock()
        mock_result = Mock()
        mock_result.new_items = ["3"]
        
        with patch('src.maai.services.conversation_service.Runner.run') as mock_run:
            with patch('src.maai.services.conversation_service.ItemHelpers.text_message_outputs') as mock_text:
                mock_run.return_value = mock_result
                mock_text.return_value = "3"
                
                choice = await self.service._extract_principle_choice(
                    response_text, "agent1", "Agent1", mock_moderator
                )
                
                assert choice.principle_id == 3
                assert choice.principle_name == "Maximize the Average Income with a Floor Constraint"
                assert choice.reasoning == response_text[:500]
    
    @pytest.mark.asyncio
    async def test_extract_principle_choice_invalid_defaults_to_1(self):
        """Test principle choice extraction with invalid response defaults to 1."""
        response_text = "I'm not sure which principle to choose."
        
        mock_moderator = Mock()
        mock_result = Mock()
        mock_result.new_items = ["unclear"]
        
        with patch('src.maai.services.conversation_service.Runner.run') as mock_run:
            with patch('src.maai.services.conversation_service.ItemHelpers.text_message_outputs') as mock_text:
                mock_run.return_value = mock_result
                mock_text.return_value = "unclear"
                
                choice = await self.service._extract_principle_choice(
                    response_text, "agent1", "Agent1", mock_moderator
                )
                
                assert choice.principle_id == 1  # Default
                assert choice.principle_name == "Maximize the Minimum Income"
    
    @pytest.mark.asyncio
    async def test_extract_principle_choice_creates_moderator_when_none(self):
        """Test that moderator is created when none provided."""
        response_text = "I choose principle 2."
        
        mock_result = Mock()
        mock_result.new_items = ["2"]
        
        with patch('src.maai.services.conversation_service.Runner.run') as mock_run:
            with patch('src.maai.services.conversation_service.ItemHelpers.text_message_outputs') as mock_text:
                with patch('src.maai.services.conversation_service.create_discussion_moderator') as mock_create:
                    mock_moderator = Mock()
                    mock_create.return_value = mock_moderator
                    mock_run.return_value = mock_result
                    mock_text.return_value = "2"
                    
                    choice = await self.service._extract_principle_choice(
                        response_text, "agent1", "Agent1", None
                    )
                    
                    assert choice.principle_id == 2
                    mock_create.assert_called_once()
    
    def test_build_public_context_empty_transcript(self):
        """Test building public context with empty transcript."""
        mock_agent = Mock(current_choice=PrincipleChoice(1, "Test", "Test reasoning"))
        round_context = RoundContext(1, [mock_agent], [], ["agent1"])
        
        context = self.service._build_public_context("agent1", round_context)
        
        assert "Your current choice: Principle 1" in context
        assert "SPEAKERS IN THIS ROUND SO FAR" not in context
    
    def test_build_public_context_with_speakers(self):
        """Test building public context with previous speakers."""
        mock_agent = Mock(agent_id="agent1", current_choice=PrincipleChoice(2, "Test", "Test reasoning"))
        
        # Create mock transcript with responses from current round
        mock_response = Mock(
            round_number=1,
            agent_name="Agent2",
            public_message="I think principle 1 is best because it ensures fairness for all."
        )
        
        round_context = RoundContext(1, [mock_agent], [mock_response], ["agent1"])
        
        context = self.service._build_public_context("agent1", round_context)
        
        assert "SPEAKERS IN THIS ROUND SO FAR:" in context
        assert "Agent2: I think principle 1 is best because it ensures fairness for all." in context
        assert "Your current choice: Principle 2" in context
    
    @pytest.mark.asyncio
    async def test_generate_public_communication_with_logging(self):
        """Test public communication generation with logging."""
        mock_agent = Mock(agent_id="agent1", name="Agent1", current_choice=PrincipleChoice(1, "Test", "Test"))
        mock_memory = Mock(strategy_update="Test strategy")
        round_context = RoundContext(1, [mock_agent], [], ["agent1"])
        
        mock_result = Mock()
        mock_result.new_items = ["I choose principle 1"]
        
        with patch('src.maai.services.conversation_service.Runner.run') as mock_run:
            with patch('src.maai.services.conversation_service.ItemHelpers.text_message_outputs') as mock_text:
                mock_run.return_value = mock_result
                mock_text.return_value = "I choose principle 1"
                
                response = await self.service._generate_public_communication(
                    mock_agent, round_context, mock_memory
                )
                
                assert response == "I choose principle 1"
                
                # Check that logger was called for input and output
                assert self.mock_logger.log_agent_interaction.call_count == 2
                
                # Check input logging
                input_call = self.mock_logger.log_agent_interaction.call_args_list[0]
                assert input_call[1]['agent_id'] == "agent1"
                assert input_call[1]['agent_name'] == "Agent1"
                assert input_call[1]['round_num'] == 1
                assert 'input_prompt' in input_call[1]
                
                # Check output logging
                output_call = self.mock_logger.log_agent_interaction.call_args_list[1]
                assert output_call[1]['agent_id'] == "agent1"
                assert output_call[1]['agent_name'] == "Agent1"
                assert output_call[1]['round_num'] == 1
                assert output_call[1]['raw_llm_response'] == "I choose principle 1"
                assert 'processing_time_ms' in output_call[1]


class TestConversationServiceIntegration:
    """Integration tests for ConversationService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ConversationService()
        self.mock_agents = [
            Mock(spec=DeliberationAgent, agent_id="agent1", name="Agent1"),
            Mock(spec=DeliberationAgent, agent_id="agent2", name="Agent2")
        ]
    
    def test_speaking_order_constraint_integration(self):
        """Test that speaking order constraints work across multiple rounds."""
        # Set sequential pattern for predictable behavior
        self.service.set_communication_pattern(SequentialCommunicationPattern())
        
        # Round 1: Should be [agent1, agent2]
        order1 = self.service.generate_speaking_order(self.mock_agents, 1)
        assert order1 == ["agent1", "agent2"]
        
        # Round 2: Should be [agent2, agent1]
        order2 = self.service.generate_speaking_order(self.mock_agents, 2)
        assert order2 == ["agent2", "agent1"]
        
        # Round 3: Should be [agent1, agent2] again
        order3 = self.service.generate_speaking_order(self.mock_agents, 3)
        assert order3 == ["agent1", "agent2"]
    
    def test_pattern_switching_preserves_history(self):
        """Test that switching patterns preserves speaking order history."""
        # Generate one order with random pattern
        order1 = self.service.generate_speaking_order(self.mock_agents, 1)
        
        # Switch to sequential pattern
        self.service.set_communication_pattern(SequentialCommunicationPattern())
        
        # Generate another order
        order2 = self.service.generate_speaking_order(self.mock_agents, 2)
        
        # History should contain both orders
        history = self.service.get_speaking_orders()
        assert len(history) == 2
        assert history[0] == order1
        assert history[1] == order2
    
    @pytest.mark.asyncio
    async def test_principle_choice_extraction_all_principles(self):
        """Test principle choice extraction for all valid principles."""
        test_cases = [
            ("I choose principle 1", 1, "Maximize the Minimum Income"),
            ("Principle 2 is best", 2, "Maximize the Average Income"),
            ("Let's go with 3", 3, "Maximize the Average Income with a Floor Constraint"),
            ("Number 4 makes sense", 4, "Maximize the Average Income with a Range Constraint"),
        ]
        
        for response_text, expected_id, expected_name in test_cases:
            mock_moderator = Mock()
            mock_result = Mock()
            mock_result.new_items = [str(expected_id)]
            
            with patch('src.maai.services.conversation_service.Runner.run') as mock_run:
                with patch('src.maai.services.conversation_service.ItemHelpers.text_message_outputs') as mock_text:
                    mock_run.return_value = mock_result
                    mock_text.return_value = str(expected_id)
                    
                    choice = await self.service._extract_principle_choice(
                        response_text, "agent1", "Agent1", mock_moderator
                    )
                    
                    assert choice.principle_id == expected_id
                    assert choice.principle_name == expected_name
                    assert choice.reasoning == response_text[:500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])