"""
Test suite for Phase 1 memory functionality.
Tests individual memory generation, learning accumulation, and phase transition.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Core models and services
from src.maai.core.models import (
    ExperimentConfig, AgentConfig, DefaultConfig,
    IndividualMemoryEntry, IndividualMemoryType, IndividualMemoryContent,
    IndividualReflectionContext, LearningContext, Phase1ExperienceData,
    ConsolidatedMemory, EnhancedAgentMemory, PrincipleChoice, EconomicOutcome, IncomeClass
)
from src.maai.services.memory_service import MemoryService
from src.maai.agents.enhanced import DeliberationAgent


class TestPhase1MemoryModels:
    """Test Phase 1 memory data models."""
    
    def test_individual_memory_content_creation(self):
        """Test creation of individual memory content."""
        content = IndividualMemoryContent(
            situation_assessment="Testing situation",
            reasoning_process="Testing reasoning",
            insights_gained="Testing insights",
            confidence_level=0.7,
            strategic_implications="Testing strategy",
            preference_evolution="Testing evolution"
        )
        
        assert content.situation_assessment == "Testing situation"
        assert content.confidence_level == 0.7
        assert 0.0 <= content.confidence_level <= 1.0
    
    def test_individual_memory_content_confidence_validation(self):
        """Test confidence level validation."""
        # Valid confidence levels
        content = IndividualMemoryContent(
            situation_assessment="Test",
            reasoning_process="Test", 
            insights_gained="Test",
            confidence_level=0.5
        )
        assert content.confidence_level == 0.5
        
        # Test boundary values
        content_min = IndividualMemoryContent(
            situation_assessment="Test",
            reasoning_process="Test",
            insights_gained="Test", 
            confidence_level=0.0
        )
        assert content_min.confidence_level == 0.0
        
        content_max = IndividualMemoryContent(
            situation_assessment="Test",
            reasoning_process="Test",
            insights_gained="Test",
            confidence_level=1.0
        )
        assert content_max.confidence_level == 1.0
    
    def test_individual_memory_entry_creation(self):
        """Test creation of individual memory entries."""
        content = IndividualMemoryContent(
            situation_assessment="Test situation",
            reasoning_process="Test reasoning",
            insights_gained="Test insights",
            confidence_level=0.8
        )
        
        entry = IndividualMemoryEntry(
            memory_id="test_id",
            agent_id="agent_123",
            memory_type=IndividualMemoryType.REFLECTION,
            content=content,
            activity_context="initial_ranking"
        )
        
        assert entry.memory_id == "test_id"
        assert entry.agent_id == "agent_123"
        assert entry.memory_type == IndividualMemoryType.REFLECTION
        assert entry.phase == "individual"
        assert entry.activity_context == "initial_ranking"
    
    def test_enhanced_agent_memory(self):
        """Test enhanced agent memory with Phase 1 functionality."""
        memory = EnhancedAgentMemory(agent_id="test_agent")
        
        # Test initial state
        assert not memory.has_individual_memories()
        assert len(memory.get_individual_insights()) == 0
        
        # Add individual memory
        content = IndividualMemoryContent(
            situation_assessment="Test",
            reasoning_process="Test",
            insights_gained="Key insight",
            confidence_level=0.7
        )
        
        entry = IndividualMemoryEntry(
            memory_id="mem_1",
            agent_id="test_agent",
            memory_type=IndividualMemoryType.REFLECTION,
            content=content,
            activity_context="test_activity"
        )
        
        memory.add_individual_memory(entry)
        
        # Test state after adding memory
        assert memory.has_individual_memories()
        assert len(memory.get_individual_insights()) == 1
        assert memory.get_individual_insights()[0] == "Key insight"
        assert memory.get_latest_individual_memory() == entry
        
        # Test activity filtering
        activity_memories = memory.get_memories_by_activity("test_activity")
        assert len(activity_memories) == 1
        assert activity_memories[0] == entry
    
    def test_consolidated_memory(self):
        """Test consolidated memory creation."""
        consolidated = ConsolidatedMemory(
            agent_id="test_agent",
            consolidated_insights="Main insights",
            strategic_preferences="Strategic approach",
            economic_learnings="Economic lessons", 
            confidence_summary="Confidence growth",
            principle_understanding="Principle knowledge"
        )
        
        assert consolidated.agent_id == "test_agent"
        assert consolidated.consolidated_insights == "Main insights"
        assert isinstance(consolidated.timestamp, datetime)


class TestMemoryServicePhase1:
    """Test MemoryService Phase 1 functionality."""
    
    @pytest.fixture
    def memory_service(self):
        """Create a MemoryService instance for testing."""
        return MemoryService(enable_phase1_memory=True)
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock DeliberationAgent for testing."""
        agent = MagicMock(spec=DeliberationAgent)
        agent.agent_id = "test_agent_id"
        agent.name = "Test Agent"
        return agent
    
    def test_memory_service_initialization(self, memory_service):
        """Test MemoryService initialization with Phase 1 support."""
        assert memory_service.enable_phase1_memory is True
        assert isinstance(memory_service.agent_memories, dict)
    
    def test_enhanced_agent_memory_initialization(self, memory_service):
        """Test that agent memory uses enhanced memory system."""
        memory_service.initialize_agent_memory("test_agent")
        agent_memory = memory_service.get_agent_memory("test_agent")
        
        assert isinstance(agent_memory, EnhancedAgentMemory)
        assert agent_memory.agent_id == "test_agent"
        assert not agent_memory.has_individual_memories()
    
    @pytest.mark.asyncio
    async def test_generate_individual_reflection(self, memory_service, mock_agent):
        """Test individual reflection memory generation."""
        # Mock the LLM response
        with patch('src.maai.services.memory_service.Runner.run') as mock_run:
            mock_result = MagicMock()
            mock_result.new_items = ["Mock response with structured output:\nSITUATION: Test situation\nREASONING: Test reasoning\nINSIGHTS: Test insights\nCONFIDENCE: 0.8\nPREFERENCES: Test preferences"]
            mock_run.return_value = mock_result
            
            with patch('src.maai.services.memory_service.ItemHelpers.text_message_outputs') as mock_text:
                mock_text.return_value = "SITUATION: Test situation\nREASONING: Test reasoning\nINSIGHTS: Test insights\nCONFIDENCE: 0.8\nPREFERENCES: Test preferences"
                
                reflection_context = IndividualReflectionContext(
                    activity="test_activity",
                    data={"test": "data"},
                    reasoning_prompt="Why did you make this choice?"
                )
                
                result = await memory_service.generate_individual_reflection(mock_agent, reflection_context)
                
                # Verify memory entry was created
                assert isinstance(result, IndividualMemoryEntry)
                assert result.agent_id == mock_agent.agent_id
                assert result.memory_type == IndividualMemoryType.REFLECTION
                assert result.activity_context == "test_activity"
                
                # Verify content was parsed
                assert result.content.situation_assessment == "Test situation"
                assert result.content.reasoning_process == "Test reasoning"
                assert result.content.insights_gained == "Test insights"
                assert result.content.confidence_level == 0.8
                assert result.content.preference_evolution == "Test preferences"
                
                # Verify memory was stored
                agent_memory = memory_service.get_agent_memory(mock_agent.agent_id)
                assert agent_memory.has_individual_memories()
                assert len(agent_memory.individual_memories) == 1
    
    @pytest.mark.asyncio
    async def test_update_individual_learning(self, memory_service, mock_agent):
        """Test individual learning memory generation."""
        with patch('src.maai.services.memory_service.Runner.run') as mock_run:
            mock_result = MagicMock()
            mock_result.new_items = ["Mock learning response"]
            mock_run.return_value = mock_result
            
            with patch('src.maai.services.memory_service.ItemHelpers.text_message_outputs') as mock_text:
                mock_text.return_value = "SITUATION: Learning context\nREASONING: Integration process\nINSIGHTS: New understanding\nCONFIDENCE: 0.7\nSTRATEGY: Strategic implications"
                
                learning_context = LearningContext(
                    learning_stage="detailed_examples",
                    new_information="New information about principles",
                    previous_understanding="Previous understanding"
                )
                
                result = await memory_service.update_individual_learning(mock_agent, learning_context)
                
                # Verify memory entry
                assert isinstance(result, IndividualMemoryEntry)
                assert result.memory_type == IndividualMemoryType.LEARNING
                assert result.activity_context == "detailed_examples"
                
                # Verify content
                assert result.content.situation_assessment == "Learning context"
                assert result.content.strategic_implications == "Strategic implications"
    
    @pytest.mark.asyncio
    async def test_integrate_phase1_experience(self, memory_service, mock_agent):
        """Test Phase 1 experience integration."""
        with patch('src.maai.services.memory_service.Runner.run') as mock_run:
            mock_result = MagicMock()
            mock_result.new_items = ["Mock integration response"]
            mock_run.return_value = mock_result
            
            with patch('src.maai.services.memory_service.ItemHelpers.text_message_outputs') as mock_text:
                mock_text.return_value = "SITUATION: Experience happened\nREASONING: Thought process\nINSIGHTS: Experience insights\nCONFIDENCE: 0.9\nSTRATEGY: Group implications"
                
                # Create mock principle choice and economic outcome
                principle_choice = PrincipleChoice(
                    principle_id=1,
                    principle_name="Test Principle",
                    reasoning="Test reasoning"
                )
                
                economic_outcome = EconomicOutcome(
                    agent_id=mock_agent.agent_id,
                    round_number=1,
                    chosen_principle=1,
                    assigned_income_class=IncomeClass.MEDIUM,
                    actual_income=30000,
                    payout_amount=3.0
                )
                
                experience_data = Phase1ExperienceData(
                    round_number=1,
                    principle_choice=principle_choice,
                    economic_outcome=economic_outcome,
                    reflection_prompt="What did you learn from this experience?"
                )
                
                result = await memory_service.integrate_phase1_experience(mock_agent, experience_data)
                
                # Verify memory entry
                assert isinstance(result, IndividualMemoryEntry)
                assert result.memory_type == IndividualMemoryType.INTEGRATION
                assert result.activity_context == "individual_round_1"
                assert result.round_context == 1
    
    @pytest.mark.asyncio
    async def test_consolidate_phase1_memories(self, memory_service, mock_agent):
        """Test Phase 1 memory consolidation."""
        # First add some individual memories
        memory_service.initialize_agent_memory(mock_agent.agent_id)
        agent_memory = memory_service.get_agent_memory(mock_agent.agent_id)
        
        # Add test memories
        for i in range(3):
            content = IndividualMemoryContent(
                situation_assessment=f"Situation {i}",
                reasoning_process=f"Reasoning {i}",
                insights_gained=f"Insight {i}",
                confidence_level=0.5 + i * 0.1
            )
            
            entry = IndividualMemoryEntry(
                memory_id=f"mem_{i}",
                agent_id=mock_agent.agent_id,
                memory_type=IndividualMemoryType.REFLECTION,
                content=content,
                activity_context=f"activity_{i}"
            )
            
            agent_memory.add_individual_memory(entry)
        
        # Mock consolidation LLM call
        with patch('src.maai.services.memory_service.Runner.run') as mock_run:
            mock_result = MagicMock()
            mock_result.new_items = ["Mock consolidation response"]
            mock_run.return_value = mock_result
            
            with patch('src.maai.services.memory_service.ItemHelpers.text_message_outputs') as mock_text:
                mock_text.return_value = "INSIGHTS: Consolidated insights\nPREFERENCES: Strategic preferences\nECONOMICS: Economic learnings\nCONFIDENCE: Confidence evolution\nPRINCIPLES: Principle understanding"
                
                result = await memory_service.consolidate_phase1_memories(mock_agent.agent_id)
                
                # Verify consolidated memory
                assert isinstance(result, ConsolidatedMemory)
                assert result.agent_id == mock_agent.agent_id
                assert result.consolidated_insights == "Consolidated insights"
                assert result.strategic_preferences == "Strategic preferences"
                assert result.economic_learnings == "Economic learnings"
                
                # Verify it was stored in agent memory
                assert agent_memory.consolidated_memory is not None
                assert agent_memory.consolidated_memory == result
    
    def test_get_phase1_context_for_phase2(self, memory_service, mock_agent):
        """Test Phase 1 context generation for Phase 2."""
        memory_service.initialize_agent_memory(mock_agent.agent_id)
        agent_memory = memory_service.get_agent_memory(mock_agent.agent_id)
        
        # Test with no memories
        context = memory_service.get_phase1_context_for_phase2(mock_agent.agent_id)
        assert context == ""
        
        # Add consolidated memory
        consolidated = ConsolidatedMemory(
            agent_id=mock_agent.agent_id,
            consolidated_insights="Key insights from individual phase",
            strategic_preferences="Strategic approach developed",
            economic_learnings="Economic lessons learned",
            confidence_summary="Confidence growth",
            principle_understanding="Principle understanding"
        )
        
        agent_memory.consolidated_memory = consolidated
        
        # Test with consolidated memory
        context = memory_service.get_phase1_context_for_phase2(mock_agent.agent_id)
        assert "YOUR INDIVIDUAL PHASE INSIGHTS:" in context
        assert "Key insights from individual phase" in context
        assert "Strategic approach developed" in context
        assert "Economic lessons learned" in context
    
    def test_memory_service_disabled(self):
        """Test MemoryService with Phase 1 memory disabled."""
        memory_service = MemoryService(enable_phase1_memory=False)
        
        # All Phase 1 methods should return None when disabled
        mock_agent = MagicMock(spec=DeliberationAgent)
        mock_agent.agent_id = "test_agent"
        
        async def run_disabled_tests():
            reflection_context = IndividualReflectionContext(
                activity="test",
                data={},
                reasoning_prompt="test"
            )
            
            result1 = await memory_service.generate_individual_reflection(mock_agent, reflection_context)
            assert result1 is None
            
            learning_context = LearningContext(
                learning_stage="test",
                new_information="test"
            )
            
            result2 = await memory_service.update_individual_learning(mock_agent, learning_context)
            assert result2 is None
            
            experience_data = Phase1ExperienceData(
                reflection_prompt="test"
            )
            
            result3 = await memory_service.integrate_phase1_experience(mock_agent, experience_data)
            assert result3 is None
            
            result4 = await memory_service.consolidate_phase1_memories(mock_agent.agent_id)
            assert result4 is None
        
        asyncio.run(run_disabled_tests())


class TestPhase1MemoryConfiguration:
    """Test Phase 1 memory configuration options."""
    
    def test_experiment_config_phase1_defaults(self):
        """Test default Phase 1 memory configuration values."""
        config = ExperimentConfig(
            experiment_id="test",
            agents=[AgentConfig(name="Test Agent")]
        )
        
        # Test default values
        assert config.enable_phase1_memory is True
        assert config.phase1_memory_frequency == "each_activity"
        assert config.phase1_consolidation_strategy == "summary"
        assert config.phase1_memory_integration is True
        assert config.phase1_reflection_depth == "standard"
    
    def test_experiment_config_phase1_custom(self):
        """Test custom Phase 1 memory configuration values."""
        config = ExperimentConfig(
            experiment_id="test",
            agents=[AgentConfig(name="Test Agent")],
            enable_phase1_memory=False,
            phase1_memory_frequency="phase_end",
            phase1_consolidation_strategy="detailed",
            phase1_memory_integration=False,
            phase1_reflection_depth="brief"
        )
        
        assert config.enable_phase1_memory is False
        assert config.phase1_memory_frequency == "phase_end"
        assert config.phase1_consolidation_strategy == "detailed"
        assert config.phase1_memory_integration is False
        assert config.phase1_reflection_depth == "brief"


class TestPhase1MemoryIntegration:
    """Test Phase 1 memory integration with existing systems."""
    
    def test_memory_strategy_factory_phase_aware(self):
        """Test memory strategy factory includes phase-aware strategy."""
        from src.maai.services.memory_service import create_memory_strategy
        
        # Test new phase-aware strategy
        strategy = create_memory_strategy("phase_aware_decomposed")
        assert strategy is not None
        assert hasattr(strategy, 'phase1_weight')
        
        # Test existing strategies still work
        recent_strategy = create_memory_strategy("recent")
        assert recent_strategy is not None
        
        decomposed_strategy = create_memory_strategy("decomposed")
        assert decomposed_strategy is not None
        
        # Test invalid strategy
        with pytest.raises(ValueError):
            create_memory_strategy("invalid_strategy")
    
    def test_enhanced_memory_summary(self):
        """Test enhanced memory summary includes Phase 1 data."""
        memory_service = MemoryService(enable_phase1_memory=True)
        memory_service.initialize_agent_memory("test_agent")
        
        # Add some test memories
        agent_memory = memory_service.get_agent_memory("test_agent")
        
        content = IndividualMemoryContent(
            situation_assessment="Test",
            reasoning_process="Test", 
            insights_gained="Test insight",
            confidence_level=0.7
        )
        
        entry = IndividualMemoryEntry(
            memory_id="test",
            agent_id="test_agent",
            memory_type=IndividualMemoryType.REFLECTION,
            content=content,
            activity_context="test_activity"
        )
        
        agent_memory.add_individual_memory(entry)
        
        # Get summary
        summary = memory_service.get_agent_memory_summary("test_agent")
        
        # Verify Phase 1 data is included
        assert "phase1" in summary
        assert "phase2" in summary
        assert "consolidated_memory" in summary
        
        phase1_summary = summary["phase1"]
        assert phase1_summary["total_individual_memories"] == 1
        assert phase1_summary["memory_types"] == ["reflection"]
        assert phase1_summary["activities"] == ["test_activity"]
        assert phase1_summary["insights"] == ["Test insight"]
        assert phase1_summary["has_consolidation"] is False


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_phase1_memory.py -v
    pytest.main([__file__, "-v"])