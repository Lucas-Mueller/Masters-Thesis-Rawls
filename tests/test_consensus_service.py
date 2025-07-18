"""
Comprehensive tests for ConsensusService and all consensus detection strategies.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.maai.services.consensus_service import (
    ConsensusService, 
    IdMatchingStrategy, 
    SemanticSimilarityStrategy, 
    ThresholdBasedStrategy,
    ConsensusDetectionStrategy
)
from src.maai.core.models import DeliberationResponse, ConsensusResult, PrincipleChoice


class TestIdMatchingStrategy:
    """Test IdMatchingStrategy consensus detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = IdMatchingStrategy()
        self.timestamp = datetime.now()
    
    def create_response(self, agent_id: str, principle_id: int, round_num: int = 1, 
                       reasoning: str = "Test reasoning", speaking_position: int = 1):
        """Helper to create DeliberationResponse objects."""
        return DeliberationResponse(
            agent_id=agent_id,
            agent_name=f"Agent_{agent_id}",
            public_message=f"I choose principle {principle_id}",
            updated_choice=PrincipleChoice(
                principle_id=principle_id,
                principle_name=f"Principle {principle_id}",
                reasoning=reasoning
            ),
            round_number=round_num,
            timestamp=self.timestamp,
            speaking_position=speaking_position
        )
    
    @pytest.mark.asyncio
    async def test_empty_responses(self):
        """Test consensus detection with empty responses."""
        result = await self.strategy.detect([])
        
        assert result.unanimous == False
        assert result.agreed_principle is None
        assert result.dissenting_agents == []
        assert result.rounds_to_consensus == 0
        assert result.total_messages == 0
    
    @pytest.mark.asyncio
    async def test_single_agent_response(self):
        """Test consensus detection with single agent."""
        responses = [self.create_response("agent1", 1)]
        result = await self.strategy.detect(responses)
        
        assert result.unanimous == True
        assert result.agreed_principle.principle_id == 1
        assert result.dissenting_agents == []
        assert result.rounds_to_consensus == 1
        assert result.total_messages == 1
    
    @pytest.mark.asyncio
    async def test_unanimous_consensus(self):
        """Test unanimous consensus detection."""
        responses = [
            self.create_response("agent1", 2, round_num=1),
            self.create_response("agent2", 2, round_num=1),
            self.create_response("agent3", 2, round_num=1)
        ]
        result = await self.strategy.detect(responses)
        
        assert result.unanimous == True
        assert result.agreed_principle.principle_id == 2
        assert result.dissenting_agents == []
        assert result.rounds_to_consensus == 1
        assert result.total_messages == 3
    
    @pytest.mark.asyncio
    async def test_no_consensus(self):
        """Test no consensus detection."""
        responses = [
            self.create_response("agent1", 1),
            self.create_response("agent2", 2),
            self.create_response("agent3", 3)
        ]
        result = await self.strategy.detect(responses)
        
        assert result.unanimous == False
        assert result.agreed_principle is None
        assert len(result.dissenting_agents) == 2  # 2 agents dissent from most common
        assert result.rounds_to_consensus == 0
        assert result.total_messages == 3
    
    @pytest.mark.asyncio
    async def test_partial_consensus(self):
        """Test partial consensus with dissenting agents."""
        responses = [
            self.create_response("agent1", 1),
            self.create_response("agent2", 1),
            self.create_response("agent3", 2),
            self.create_response("agent4", 2)
        ]
        result = await self.strategy.detect(responses)
        
        assert result.unanimous == False
        assert result.agreed_principle is None
        assert len(result.dissenting_agents) == 2  # Either 1,1 or 2,2 will be dissenting
        assert result.rounds_to_consensus == 0
        assert result.total_messages == 4
    
    @pytest.mark.asyncio
    async def test_evolving_consensus(self):
        """Test consensus that develops over multiple rounds."""
        responses = [
            # Round 1 - disagreement
            self.create_response("agent1", 1, round_num=1),
            self.create_response("agent2", 2, round_num=1),
            # Round 2 - agent2 changes mind
            self.create_response("agent1", 1, round_num=2),
            self.create_response("agent2", 1, round_num=2),
        ]
        result = await self.strategy.detect(responses)
        
        assert result.unanimous == True
        assert result.agreed_principle.principle_id == 1
        assert result.dissenting_agents == []
        assert result.rounds_to_consensus == 2
        assert result.total_messages == 4
    
    @pytest.mark.asyncio
    async def test_latest_response_priority(self):
        """Test that only latest response from each agent is considered."""
        responses = [
            # Agent1 changes from 1 to 2
            self.create_response("agent1", 1, round_num=1),
            self.create_response("agent1", 2, round_num=2),
            # Agent2 stays at 2
            self.create_response("agent2", 2, round_num=1),
        ]
        result = await self.strategy.detect(responses)
        
        assert result.unanimous == True
        assert result.agreed_principle.principle_id == 2
        assert result.dissenting_agents == []
        assert result.rounds_to_consensus == 2
        assert result.total_messages == 3


class TestThresholdBasedStrategy:
    """Test ThresholdBasedStrategy consensus detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = ThresholdBasedStrategy(threshold=0.8)
        self.timestamp = datetime.now()
    
    def create_response(self, agent_id: str, principle_id: int, round_num: int = 1):
        """Helper to create DeliberationResponse objects."""
        return DeliberationResponse(
            agent_id=agent_id,
            agent_name=f"Agent_{agent_id}",
            public_message=f"I choose principle {principle_id}",
            updated_choice=PrincipleChoice(
                principle_id=principle_id,
                principle_name=f"Principle {principle_id}",
                reasoning="Test reasoning"
            ),
            round_number=round_num,
            timestamp=self.timestamp,
            speaking_position=1
        )
    
    @pytest.mark.asyncio
    async def test_threshold_consensus_met(self):
        """Test consensus when threshold is met."""
        # 4 out of 5 agents agree (80% threshold)
        responses = [
            self.create_response("agent1", 1),
            self.create_response("agent2", 1),
            self.create_response("agent3", 1),
            self.create_response("agent4", 1),
            self.create_response("agent5", 2),
        ]
        result = await self.strategy.detect(responses)
        
        assert result.unanimous == False  # Not unanimous
        assert result.agreed_principle.principle_id == 1
        assert result.dissenting_agents == ["agent5"]
        assert result.rounds_to_consensus == 1
        assert result.total_messages == 5
    
    @pytest.mark.asyncio
    async def test_threshold_consensus_not_met(self):
        """Test no consensus when threshold is not met."""
        # Only 3 out of 5 agents agree (60% < 80% threshold)
        responses = [
            self.create_response("agent1", 1),
            self.create_response("agent2", 1),
            self.create_response("agent3", 1),
            self.create_response("agent4", 2),
            self.create_response("agent5", 3),
        ]
        result = await self.strategy.detect(responses)
        
        assert result.unanimous == False
        assert result.agreed_principle is None
        assert len(result.dissenting_agents) == 2  # agent4 and agent5 dissent from most common
        assert result.rounds_to_consensus == 0
        assert result.total_messages == 5
    
    @pytest.mark.asyncio
    async def test_unanimous_consensus(self):
        """Test unanimous consensus (100% agreement)."""
        responses = [
            self.create_response("agent1", 2),
            self.create_response("agent2", 2),
            self.create_response("agent3", 2),
        ]
        result = await self.strategy.detect(responses)
        
        assert result.unanimous == True
        assert result.agreed_principle.principle_id == 2
        assert result.dissenting_agents == []
        assert result.rounds_to_consensus == 1
        assert result.total_messages == 3
    
    @pytest.mark.asyncio
    async def test_custom_threshold(self):
        """Test with custom threshold value."""
        strategy = ThresholdBasedStrategy(threshold=0.6)  # 60% threshold
        
        # 3 out of 5 agents agree (60% threshold)
        responses = [
            self.create_response("agent1", 1),
            self.create_response("agent2", 1),
            self.create_response("agent3", 1),
            self.create_response("agent4", 2),
            self.create_response("agent5", 3),
        ]
        result = await strategy.detect(responses)
        
        assert result.unanimous == False
        assert result.agreed_principle.principle_id == 1
        assert len(result.dissenting_agents) == 2
        assert result.rounds_to_consensus == 1
        assert result.total_messages == 5


class TestSemanticSimilarityStrategy:
    """Test SemanticSimilarityStrategy consensus detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = SemanticSimilarityStrategy()
        self.timestamp = datetime.now()
    
    def create_response(self, agent_id: str, principle_id: int):
        """Helper to create DeliberationResponse objects."""
        return DeliberationResponse(
            agent_id=agent_id,
            agent_name=f"Agent_{agent_id}",
            public_message=f"I choose principle {principle_id}",
            updated_choice=PrincipleChoice(
                principle_id=principle_id,
                principle_name=f"Principle {principle_id}",
                reasoning="Test reasoning"
            ),
            round_number=1,
            timestamp=self.timestamp,
            speaking_position=1
        )
    
    @pytest.mark.asyncio
    async def test_semantic_strategy_delegates_to_id_matching(self):
        """Test that semantic strategy currently delegates to ID matching."""
        responses = [
            self.create_response("agent1", 1),
            self.create_response("agent2", 1),
            self.create_response("agent3", 2),
        ]
        result = await self.strategy.detect(responses)
        
        # Should behave like ID matching strategy
        assert result.unanimous == False
        assert result.agreed_principle is None
        assert len(result.dissenting_agents) == 1
        assert result.total_messages == 3


class TestConsensusService:
    """Test ConsensusService main service class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ConsensusService()
        self.timestamp = datetime.now()
    
    def create_response(self, agent_id: str, principle_id: int, round_num: int = 1, 
                       reasoning: str = "Test reasoning"):
        """Helper to create DeliberationResponse objects."""
        return DeliberationResponse(
            agent_id=agent_id,
            agent_name=f"Agent_{agent_id}",
            public_message=f"I choose principle {principle_id}",
            updated_choice=PrincipleChoice(
                principle_id=principle_id,
                principle_name=f"Principle {principle_id}",
                reasoning=reasoning
            ),
            round_number=round_num,
            timestamp=self.timestamp,
            speaking_position=1
        )
    
    @pytest.mark.asyncio
    async def test_default_strategy_is_id_matching(self):
        """Test that default strategy is ID matching."""
        assert isinstance(self.service.detection_strategy, IdMatchingStrategy)
    
    @pytest.mark.asyncio
    async def test_detect_consensus_with_default_strategy(self):
        """Test consensus detection with default strategy."""
        responses = [
            self.create_response("agent1", 1),
            self.create_response("agent2", 1),
        ]
        result = await self.service.detect_consensus(responses)
        
        assert result.unanimous == True
        assert result.agreed_principle.principle_id == 1
        assert result.dissenting_agents == []
    
    @pytest.mark.asyncio
    async def test_set_detection_strategy(self):
        """Test changing detection strategy."""
        threshold_strategy = ThresholdBasedStrategy(threshold=0.7)
        self.service.set_detection_strategy(threshold_strategy)
        
        assert isinstance(self.service.detection_strategy, ThresholdBasedStrategy)
        assert self.service.detection_strategy.threshold == 0.7
    
    @pytest.mark.asyncio
    async def test_validate_consensus_genuine(self):
        """Test validation of genuine consensus."""
        responses = [
            self.create_response("agent1", 1, round_num=1, reasoning="Fairness is important"),
            self.create_response("agent2", 1, round_num=2, reasoning="Equality matters most"),
        ]
        
        consensus_result = ConsensusResult(
            unanimous=True,
            agreed_principle=PrincipleChoice(principle_id=1, principle_name="Principle 1", reasoning="Test"),
            dissenting_agents=[],
            rounds_to_consensus=2,
            total_messages=2
        )
        
        is_valid = await self.service.validate_consensus(consensus_result, responses)
        assert is_valid == True
    
    @pytest.mark.asyncio
    async def test_validate_consensus_no_consensus(self):
        """Test validation when no consensus exists."""
        responses = [
            self.create_response("agent1", 1),
            self.create_response("agent2", 2),
        ]
        
        consensus_result = ConsensusResult(
            unanimous=False,
            agreed_principle=None,
            dissenting_agents=["agent2"],
            rounds_to_consensus=0,
            total_messages=2
        )
        
        is_valid = await self.service.validate_consensus(consensus_result, responses)
        assert is_valid == True  # No consensus to validate
    
    @pytest.mark.asyncio
    async def test_validate_consensus_suspicious_immediate(self):
        """Test validation of suspiciously immediate consensus."""
        responses = [
            self.create_response("agent1", 1, round_num=0),
        ]
        
        consensus_result = ConsensusResult(
            unanimous=True,
            agreed_principle=PrincipleChoice(principle_id=1, principle_name="Principle 1", reasoning="Test"),
            dissenting_agents=[],
            rounds_to_consensus=0,
            total_messages=1
        )
        
        is_valid = await self.service.validate_consensus(consensus_result, responses)
        assert is_valid == False  # Suspicious - single agent, round 0
    
    @pytest.mark.asyncio
    async def test_validate_consensus_identical_reasoning(self):
        """Test validation of consensus with identical reasoning."""
        responses = [
            self.create_response("agent1", 1, reasoning="Exact same reasoning"),
            self.create_response("agent2", 1, reasoning="Exact same reasoning"),
            self.create_response("agent3", 1, reasoning="Exact same reasoning"),
        ]
        
        consensus_result = ConsensusResult(
            unanimous=True,
            agreed_principle=PrincipleChoice(principle_id=1, principle_name="Principle 1", reasoning="Test"),
            dissenting_agents=[],
            rounds_to_consensus=1,
            total_messages=3
        )
        
        is_valid = await self.service.validate_consensus(consensus_result, responses)
        assert is_valid == False  # Suspicious - identical reasoning
    
    @pytest.mark.asyncio
    async def test_validate_consensus_insufficient_agents(self):
        """Test validation with insufficient agents."""
        responses = [
            self.create_response("agent1", 1),
        ]
        
        consensus_result = ConsensusResult(
            unanimous=True,
            agreed_principle=PrincipleChoice(principle_id=1, principle_name="Principle 1", reasoning="Test"),
            dissenting_agents=[],
            rounds_to_consensus=1,
            total_messages=1
        )
        
        is_valid = await self.service.validate_consensus(consensus_result, responses)
        assert is_valid == False  # Need at least 2 agents
    
    @pytest.mark.asyncio
    async def test_validate_consensus_no_agreed_principle(self):
        """Test validation with no agreed principle."""
        responses = [
            self.create_response("agent1", 1),
            self.create_response("agent2", 1),
        ]
        
        consensus_result = ConsensusResult(
            unanimous=True,
            agreed_principle=None,  # Invalid - no agreed principle
            dissenting_agents=[],
            rounds_to_consensus=1,
            total_messages=2
        )
        
        is_valid = await self.service.validate_consensus(consensus_result, responses)
        assert is_valid == False  # Invalid - no agreed principle


class TestConsensusServiceIntegration:
    """Integration tests for ConsensusService with different strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.timestamp = datetime.now()
    
    def create_response(self, agent_id: str, principle_id: int, round_num: int = 1, 
                       reasoning: str = "Test reasoning"):
        """Helper to create DeliberationResponse objects."""
        return DeliberationResponse(
            agent_id=agent_id,
            agent_name=f"Agent_{agent_id}",
            public_message=f"I choose principle {principle_id}",
            updated_choice=PrincipleChoice(
                principle_id=principle_id,
                principle_name=f"Principle {principle_id}",
                reasoning=reasoning
            ),
            round_number=round_num,
            timestamp=self.timestamp,
            speaking_position=1
        )
    
    @pytest.mark.asyncio
    async def test_id_matching_vs_threshold_strategies(self):
        """Test difference between ID matching and threshold strategies."""
        responses = [
            self.create_response("agent1", 1),
            self.create_response("agent2", 1),
            self.create_response("agent3", 1),
            self.create_response("agent4", 2),
            self.create_response("agent5", 2),
        ]
        
        # ID matching strategy - no consensus (not unanimous)
        id_service = ConsensusService(IdMatchingStrategy())
        id_result = await id_service.detect_consensus(responses)
        assert id_result.unanimous == False
        assert id_result.agreed_principle is None
        
        # Threshold strategy (60%) - consensus reached
        threshold_service = ConsensusService(ThresholdBasedStrategy(threshold=0.6))
        threshold_result = await threshold_service.detect_consensus(responses)
        assert threshold_result.unanimous == False
        assert threshold_result.agreed_principle.principle_id == 1  # 3/5 = 60%
    
    @pytest.mark.asyncio
    async def test_strategy_switching(self):
        """Test switching strategies during service lifetime."""
        service = ConsensusService()
        
        responses = [
            self.create_response("agent1", 1),
            self.create_response("agent2", 1),
            self.create_response("agent3", 2),
        ]
        
        # ID matching result - no consensus
        id_result = await service.detect_consensus(responses)
        assert id_result.unanimous == False
        
        # Switch to threshold strategy
        service.set_detection_strategy(ThresholdBasedStrategy(threshold=0.5))
        
        # Threshold result - consensus reached (2/3 = 66.7% > 50%)
        threshold_result = await service.detect_consensus(responses)
        assert threshold_result.unanimous == False
        assert threshold_result.agreed_principle.principle_id == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])