"""
Comprehensive tests for the message structure overhaul implementation.
Tests the new standardized message system and simplified memory modes.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.maai.core.models import StandardizedMessage, FullMemoryEntry, EarningsTrackingConfig
from src.maai.services.message_builder_service import MessageBuilder
from src.maai.services.simple_memory_service import SimpleMemoryService
from src.maai.services.earnings_tracking_service import EarningsTrackingService
from src.maai.agents.enhanced import DeliberationAgent


class TestStandardizedMessage:
    """Test the StandardizedMessage model."""
    
    def test_standardized_message_creation(self):
        """Test creating a StandardizedMessage."""
        message = StandardizedMessage(
            role_description="You are an economist agent.",
            negotiation_description="This is a distributive justice negotiation.",
            bank_balance="You have a current bank balance of $0.0000",
            memory_context="No previous interactions.",
            task_instruction="Please rank the principles."
        )
        
        assert message.role_description == "You are an economist agent."
        assert message.negotiation_description == "This is a distributive justice negotiation."
        assert message.bank_balance == "You have a current bank balance of $0.0000"
        assert message.memory_context == "No previous interactions."
        assert message.task_instruction == "Please rank the principles."
    
    def test_to_system_prompt(self):
        """Test system prompt generation."""
        message = StandardizedMessage(
            role_description="You are an economist agent.",
            negotiation_description="This is a distributive justice negotiation.",
            bank_balance="You have a current bank balance of $0.0000",
            memory_context="No previous interactions.",
            task_instruction="Please rank the principles."
        )
        
        system_prompt = message.to_system_prompt()
        
        assert "=== ROLE DESCRIPTION ===" in system_prompt
        assert "You are an economist agent." in system_prompt
        assert "=== NEGOTIATION DESCRIPTION ===" in system_prompt
        assert "This is a distributive justice negotiation." in system_prompt
        
        # System prompt should NOT include bank balance, memory, or task
        assert "current bank balance" not in system_prompt
        assert "No previous interactions" not in system_prompt
        assert "Please rank" not in system_prompt
    
    def test_to_input_prompt(self):
        """Test input prompt generation."""
        message = StandardizedMessage(
            role_description="You are an economist agent.",
            experiment_description="This is a distributive justice experiment.",
            bank_balance="Current Balance: $0.0000",
            memory_context="No previous interactions.",
            task_instruction="Please rank the principles."
        )
        
        input_prompt = message.to_input_prompt()
        
        # Input prompt should include ALL sections
        assert "=== ROLE DESCRIPTION ===" in input_prompt
        assert "=== EXPERIMENT DESCRIPTION ===" in input_prompt
        assert "=== BANK BALANCE ===" in input_prompt
        assert "=== MEMORY CONTEXT ===" in input_prompt
        assert "=== TASK INSTRUCTION ===" in input_prompt
        
        assert "You are an economist agent." in input_prompt
        assert "Current Balance: $0.0000" in input_prompt
        assert "No previous interactions." in input_prompt
        assert "Please rank the principles." in input_prompt


class TestMessageBuilder:
    """Test the MessageBuilder service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock earnings service
        self.mock_earnings_service = Mock(spec=EarningsTrackingService)
        self.mock_earnings_service.validate_balance_accuracy.return_value = True
        self.mock_earnings_service.get_verified_bank_balance_message.return_value = "Current Balance: $5.2500\nRecent Transactions:\n  Round 1: +$2.5000\n  Round 2: +$2.7500"
        
        self.message_builder = MessageBuilder(self.mock_earnings_service)
        
        # Create mock agent
        self.mock_agent = Mock(spec=DeliberationAgent)
        self.mock_agent.agent_id = "test_agent_1"
        self.mock_agent.personality = "You are an economist focused on efficiency."
    
    def test_build_message_complete(self):
        """Test building a complete standardized message."""
        message = self.message_builder.build_message(
            agent=self.mock_agent,
            task_instruction="Please rank the 4 principles from 1-4.",
            memory_context="Previous round: Agent discussed principle 2.",
            memory_mode="full"
        )
        
        assert isinstance(message, StandardizedMessage)
        assert "You are an economist focused on efficiency." in message.role_description
        assert "distributive justice experiment" in message.experiment_description
        assert "Current Balance: $5.2500" in message.bank_balance
        assert "COMPLETE INTERACTION HISTORY:" in message.memory_context
        assert "Please rank the 4 principles" in message.task_instruction
        
        # Verify earnings service was called
        self.mock_earnings_service.validate_balance_accuracy.assert_called_with("test_agent_1")
        self.mock_earnings_service.get_verified_bank_balance_message.assert_called_with("test_agent_1")
    
    def test_build_message_no_earnings_service(self):
        """Test building message without earnings service."""
        builder_no_earnings = MessageBuilder(None)
        
        message = builder_no_earnings.build_message(
            agent=self.mock_agent,
            task_instruction="Test task",
            memory_context="Test memory",
            memory_mode="short"
        )
        
        assert "No earnings tracking available" in message.bank_balance
    
    def test_memory_mode_formatting(self):
        """Test memory context formatting for different modes."""
        # Full mode
        formatted_full = self.message_builder.format_memory_context("Agent said hello.", "full")
        assert "COMPLETE INTERACTION HISTORY:" in formatted_full
        assert "Agent said hello." in formatted_full
        
        # Short mode
        formatted_short = self.message_builder.format_memory_context("Key insight: prefer principle 2.", "short")
        assert "AGENT-MANAGED MEMORY:" in formatted_short
        assert "Key insight: prefer principle 2." in formatted_short
        
        # Empty context
        formatted_empty = self.message_builder.format_memory_context("", "full")
        assert "No previous interactions recorded." in formatted_empty
    
    def test_experiment_description_includes_principles(self):
        """Test that experiment description includes all 4 principles."""
        description = self.message_builder.get_experiment_description()
        
        assert "distributive justice experiment" in description
        assert "Phase 1 (Individual)" in description
        assert "Phase 2 (Group)" in description
        assert "monetary payouts" in description
        assert "four principles" in description


class TestSimpleMemoryService:
    """Test the SimpleMemoryService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.memory_service = SimpleMemoryService()
        
        # Create mock agent
        self.mock_agent = Mock(spec=DeliberationAgent)
        self.mock_agent.agent_id = "test_agent"
    
    def test_initialization(self):
        """Test memory service initialization."""
        assert isinstance(self.memory_service.full_memory, dict)
        assert isinstance(self.memory_service.short_memory, dict)
        assert isinstance(self.memory_service.sequence_counters, dict)
    
    def test_agent_memory_initialization(self):
        """Test initializing memory for a new agent."""
        agent_id = "new_agent"
        self.memory_service.initialize_agent_memory(agent_id)
        
        assert agent_id in self.memory_service.full_memory
        assert agent_id in self.memory_service.short_memory
        assert agent_id in self.memory_service.sequence_counters
        assert self.memory_service.full_memory[agent_id] == []
        assert self.memory_service.short_memory[agent_id] == ""
        assert self.memory_service.sequence_counters[agent_id] == 0
    
    def test_store_interactions(self):
        """Test storing different types of interactions."""
        agent_id = "test_agent"
        
        # Store system prompt
        self.memory_service.store_system_prompt(agent_id, "=== ROLE DESCRIPTION ===\nYou are an agent.")
        
        # Store input prompt
        self.memory_service.store_input_prompt(agent_id, "Please choose a principle.", round_number=1)
        
        # Store agent response
        self.memory_service.store_agent_response(agent_id, "I choose principle 2.", round_number=1)
        
        # Verify storage
        assert len(self.memory_service.full_memory[agent_id]) == 3
        assert self.memory_service.sequence_counters[agent_id] == 3
        
        entries = self.memory_service.full_memory[agent_id]
        assert entries[0].interaction_type == "system_prompt"
        assert entries[1].interaction_type == "input_prompt"
        assert entries[2].interaction_type == "agent_response"
        assert entries[1].round_number == 1
        assert entries[2].round_number == 1
    
    @pytest.mark.asyncio
    async def test_get_full_memory_context(self):
        """Test getting full memory context."""
        agent_id = "test_agent"
        
        # Store some interactions
        self.memory_service.store_input_prompt(agent_id, "First prompt", round_number=1)
        self.memory_service.store_agent_response(agent_id, "First response", round_number=1)
        
        context = await self.memory_service.get_memory_context(agent_id, mode="full")
        
        assert "Input_Prompt: First prompt" in context
        assert "Agent_Response: First response" in context
        assert len(context.split('\n')) >= 2  # At least 2 lines
    
    @pytest.mark.asyncio
    async def test_get_short_memory_context(self):
        """Test getting short memory context."""
        agent_id = "test_agent"
        
        # Initialize agent memory first
        self.memory_service.initialize_agent_memory(agent_id)
        
        # Set some short memory
        self.memory_service.short_memory[agent_id] = "I prefer principle 2 based on efficiency."
        
        context = await self.memory_service.get_memory_context(agent_id, mode="short")
        
        assert context == "I prefer principle 2 based on efficiency."
    
    @pytest.mark.asyncio
    async def test_update_short_memory(self):
        """Test updating short memory with agent reasoning."""
        # Create a real agent for this test (we need it for Runner.run)
        agent = DeliberationAgent(
            agent_id="test_agent",
            name="Test Agent",
            personality="You are a test agent."
        )
        
        # Mock the Runner.run to return a predictable result
        mock_result = Mock()
        mock_result.new_items = [Mock()]
        mock_result.new_items[0].content = "Updated memory: I now understand principle 2 better."
        
        with patch('src.maai.services.simple_memory_service.Runner.run', return_value=mock_result):
            with patch('src.maai.services.simple_memory_service.ItemHelpers.text_message_outputs', return_value="Updated memory: I now understand principle 2 better."):
                
                updated_memory = await self.memory_service.update_short_memory(
                    agent=agent,
                    interaction_context="Agent chose principle 2 in last round.",
                    current_memory="Previous insights about principles."
                )
                
                assert "Updated memory: I now understand principle 2 better." in updated_memory
                assert self.memory_service.short_memory[agent.agent_id] == updated_memory
    
    def test_memory_stats(self):
        """Test getting memory statistics."""
        agent_id = "test_agent"
        
        # Add some interactions
        self.memory_service.store_input_prompt(agent_id, "Prompt 1")
        self.memory_service.store_agent_response(agent_id, "Response 1")
        self.memory_service.short_memory[agent_id] = "Some memory content"
        
        stats = self.memory_service.get_memory_stats(agent_id)
        
        assert stats["full_memory_entries"] == 2
        assert stats["short_memory_characters"] == len("Some memory content")
        assert stats["total_interactions"] == 2
    
    def test_clear_agent_memory(self):
        """Test clearing agent memory."""
        agent_id = "test_agent"
        
        # Add some data
        self.memory_service.store_input_prompt(agent_id, "Test prompt")
        self.memory_service.short_memory[agent_id] = "Test memory"
        
        # Clear memory
        self.memory_service.clear_agent_memory(agent_id)
        
        assert self.memory_service.full_memory[agent_id] == []
        assert self.memory_service.short_memory[agent_id] == ""
        assert self.memory_service.sequence_counters[agent_id] == 0


class TestFullMemoryEntry:
    """Test the FullMemoryEntry model."""
    
    def test_full_memory_entry_creation(self):
        """Test creating a FullMemoryEntry."""
        entry = FullMemoryEntry(
            interaction_type="input_prompt",
            content="Please choose a principle.",
            round_number=1,
            sequence_number=5
        )
        
        assert entry.interaction_type == "input_prompt"
        assert entry.content == "Please choose a principle."
        assert entry.round_number == 1
        assert entry.sequence_number == 5
        assert isinstance(entry.timestamp, datetime)
    
    def test_full_memory_entry_optional_fields(self):
        """Test FullMemoryEntry with optional fields."""
        entry = FullMemoryEntry(
            interaction_type="system_prompt",
            content="You are an agent.",
            sequence_number=1
        )
        
        assert entry.round_number is None
        assert entry.sequence_number == 1


class TestEarningsTrackingEnhancements:
    """Test the enhanced earnings tracking functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from src.maai.core.models import EarningsTrackingConfig
        
        config = EarningsTrackingConfig(enabled=True)
        self.earnings_service = EarningsTrackingService(
            payout_ratio=0.0001,
            config=config,
            income_distributions=[]
        )
    
    def test_verified_bank_balance_message(self):
        """Test getting verified bank balance message."""
        agent_id = "test_agent"
        
        # Add some earnings
        self.earnings_service.add_individual_round_payout(agent_id, 2.5, 1, "Round 1 payout")
        self.earnings_service.add_individual_round_payout(agent_id, 1.8, 2, "Round 2 payout")
        
        balance_msg = self.earnings_service.get_verified_bank_balance_message(agent_id)
        
        assert "Current Balance: $4.3000" in balance_msg
        assert "Recent Transactions:" in balance_msg
        assert "Round 1 payout: +$2.5000" in balance_msg
        assert "Round 2 payout: +$1.8000" in balance_msg
    
    def test_verified_bank_balance_no_earnings(self):
        """Test bank balance message with no earnings."""
        agent_id = "new_agent"
        
        balance_msg = self.earnings_service.get_verified_bank_balance_message(agent_id)
        
        assert "Current Balance: $0.0000" in balance_msg
        assert "No earnings history yet." in balance_msg
    
    def test_validate_balance_accuracy_success(self):
        """Test successful balance validation."""
        agent_id = "test_agent"
        
        # Add earnings
        self.earnings_service.add_individual_round_payout(agent_id, 2.5, 1, "Test payout")
        
        is_accurate = self.earnings_service.validate_balance_accuracy(agent_id)
        
        assert is_accurate is True
    
    def test_validate_balance_accuracy_new_agent(self):
        """Test balance validation for new agent."""
        agent_id = "new_agent"
        
        is_accurate = self.earnings_service.validate_balance_accuracy(agent_id)
        
        assert is_accurate is True  # No earnings, so accurate


class TestIntegration:
    """Integration tests for the complete message structure system."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        from src.maai.core.models import EarningsTrackingConfig
        
        # Create earnings service
        config = EarningsTrackingConfig(enabled=True)  
        self.earnings_service = EarningsTrackingService(
            payout_ratio=0.0001,
            config=config,
            income_distributions=[]
        )
        
        # Create message builder
        self.message_builder = MessageBuilder(self.earnings_service)
        
        # Create memory service
        self.memory_service = SimpleMemoryService()
        
        # Create agent
        self.agent = DeliberationAgent(
            agent_id="integration_test_agent",
            name="Integration Test Agent",
            personality="You are an agent focused on testing integration."
        )
    
    def test_complete_message_workflow(self):
        """Test complete workflow from memory storage to message building."""
        agent_id = self.agent.agent_id
        
        # Add some earnings
        self.earnings_service.add_individual_round_payout(agent_id, 3.25, 1, "Integration test payout")
        
        # Store some memory interactions
        self.memory_service.store_system_prompt(agent_id, "System prompt content")
        self.memory_service.store_input_prompt(agent_id, "Please choose principle", round_number=1)
        self.memory_service.store_agent_response(agent_id, "I choose principle 2", round_number=1)
        
        # Get memory context
        memory_context = asyncio.run(self.memory_service.get_memory_context(agent_id, mode="full"))
        
        # Build standardized message
        message = self.message_builder.build_message(
            agent=self.agent,
            task_instruction="Continue the deliberation by stating your final choice.",
            memory_context=memory_context,
            memory_mode="full"
        )
        
        # Verify all components are present
        assert "You are an agent focused on testing integration." in message.role_description
        assert "distributive justice experiment" in message.experiment_description
        assert "Current Balance: $3.2500" in message.bank_balance
        assert "COMPLETE INTERACTION HISTORY:" in message.memory_context
        assert "System_Prompt: System prompt content" in message.memory_context
        assert "Continue the deliberation" in message.task_instruction
        
        # Test input prompt includes all sections
        input_prompt = message.to_input_prompt()
        sections = ["=== ROLE DESCRIPTION ===", "=== EXPERIMENT DESCRIPTION ===", 
                   "=== BANK BALANCE ===", "=== MEMORY CONTEXT ===", "=== TASK INSTRUCTION ==="]
        for section in sections:
            assert section in input_prompt
    
    def test_system_vs_input_prompt_separation(self):
        """Test that system prompts are properly separated from input prompts."""
        # Build message
        message = self.message_builder.build_message(
            agent=self.agent,
            task_instruction="Test task instruction",
            memory_context="Test memory",
            memory_mode="short"
        )
        
        system_prompt = message.to_system_prompt()
        input_prompt = message.to_input_prompt()
        
        # System prompt should only have role and experiment
        assert "=== ROLE DESCRIPTION ===" in system_prompt
        assert "=== EXPERIMENT DESCRIPTION ===" in system_prompt
        assert "=== BANK BALANCE ===" not in system_prompt
        assert "=== MEMORY CONTEXT ===" not in system_prompt
        assert "=== TASK INSTRUCTION ===" not in system_prompt
        
        # Input prompt should have everything
        assert "=== ROLE DESCRIPTION ===" in input_prompt
        assert "=== EXPERIMENT DESCRIPTION ===" in input_prompt
        assert "=== BANK BALANCE ===" in input_prompt
        assert "=== MEMORY CONTEXT ===" in input_prompt
        assert "=== TASK INSTRUCTION ===" in input_prompt
        
        # Prompts should be different
        assert system_prompt != input_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])