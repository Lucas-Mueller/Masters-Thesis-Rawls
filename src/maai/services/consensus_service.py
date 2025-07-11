"""
ConsensusService for detecting and validating consensus in multi-agent deliberation.
Uses strategy pattern to allow different consensus detection algorithms.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Set
from ..core.models import DeliberationResponse, ConsensusResult, PrincipleChoice


class ConsensusDetectionStrategy(ABC):
    """Abstract base class for consensus detection strategies."""
    
    @abstractmethod
    async def detect(self, responses: List[DeliberationResponse]) -> ConsensusResult:
        """
        Detect consensus from deliberation responses.
        
        Args:
            responses: List of agent responses to analyze
            
        Returns:
            ConsensusResult indicating whether consensus was reached
        """
        pass


class IdMatchingStrategy(ConsensusDetectionStrategy):
    """
    Simple consensus detection based on principle ID matching.
    This is the current approach used in the system.
    """
    
    async def detect(self, responses: List[DeliberationResponse]) -> ConsensusResult:
        """Detect consensus by checking if all agents have the same principle_id."""
        if not responses:
            return ConsensusResult(
                unanimous=False,
                agreed_principle=None,
                dissenting_agents=[],
                rounds_to_consensus=0,
                total_messages=0
            )
        
        # Get the latest response from each agent
        latest_responses = {}
        for response in responses:
            latest_responses[response.agent_id] = response
        
        if not latest_responses:
            return ConsensusResult(
                unanimous=False,
                agreed_principle=None,
                dissenting_agents=[],
                rounds_to_consensus=0,
                total_messages=len(responses)
            )
        
        # Check if all agents have the same principle_id
        principle_ids = [resp.updated_choice.principle_id for resp in latest_responses.values()]
        
        if len(set(principle_ids)) == 1:
            # Consensus reached - all agents chose the same principle
            consensus_principle_id = principle_ids[0]
            # Get the principle choice from any agent (they're all the same)
            sample_response = next(iter(latest_responses.values()))
            agreed_principle = sample_response.updated_choice
            
            # Calculate rounds to consensus
            max_round = max(resp.round_number for resp in latest_responses.values())
            
            return ConsensusResult(
                unanimous=True,
                agreed_principle=agreed_principle,
                dissenting_agents=[],
                rounds_to_consensus=max_round,
                total_messages=len(responses)
            )
        else:
            # No consensus - find dissenting agents
            most_common_principle = max(set(principle_ids), key=principle_ids.count)
            dissenting_agents = [
                agent_id for agent_id, resp in latest_responses.items()
                if resp.updated_choice.principle_id != most_common_principle
            ]
            
            return ConsensusResult(
                unanimous=False,
                agreed_principle=None,
                dissenting_agents=dissenting_agents,
                rounds_to_consensus=0,
                total_messages=len(responses)
            )


class SemanticSimilarityStrategy(ConsensusDetectionStrategy):
    """
    Advanced consensus detection based on semantic similarity of reasoning.
    For future implementation - could analyze reasoning text similarity.
    """
    
    async def detect(self, responses: List[DeliberationResponse]) -> ConsensusResult:
        """
        Detect consensus by analyzing semantic similarity of reasoning.
        For now, falls back to ID matching.
        """
        # For now, delegate to ID matching
        # In future, could implement semantic analysis of reasoning
        id_strategy = IdMatchingStrategy()
        return await id_strategy.detect(responses)


class ThresholdBasedStrategy(ConsensusDetectionStrategy):
    """
    Consensus detection based on threshold (e.g., 80% agreement).
    Allows for near-unanimous decisions.
    """
    
    def __init__(self, threshold: float = 0.8):
        """
        Initialize threshold-based strategy.
        
        Args:
            threshold: Minimum agreement percentage (0.0-1.0)
        """
        self.threshold = threshold
    
    async def detect(self, responses: List[DeliberationResponse]) -> ConsensusResult:
        """Detect consensus based on threshold agreement."""
        if not responses:
            return ConsensusResult(
                unanimous=False,
                agreed_principle=None,
                dissenting_agents=[],
                rounds_to_consensus=0,
                total_messages=0
            )
        
        # Get the latest response from each agent
        latest_responses = {}
        for response in responses:
            latest_responses[response.agent_id] = response
        
        if not latest_responses:
            return ConsensusResult(
                unanimous=False,
                agreed_principle=None,
                dissenting_agents=[],
                rounds_to_consensus=0,
                total_messages=len(responses)
            )
        
        # Count principle preferences
        principle_counts = {}
        for resp in latest_responses.values():
            principle_id = resp.updated_choice.principle_id
            principle_counts[principle_id] = principle_counts.get(principle_id, 0) + 1
        
        total_agents = len(latest_responses)
        max_count = max(principle_counts.values())
        agreement_ratio = max_count / total_agents
        
        if agreement_ratio >= self.threshold:
            # Threshold consensus reached
            majority_principle = max(principle_counts, key=principle_counts.get)
            
            # Get an example choice for the majority principle
            agreed_principle = None
            dissenting_agents = []
            
            for agent_id, resp in latest_responses.items():
                if resp.updated_choice.principle_id == majority_principle:
                    if agreed_principle is None:
                        agreed_principle = resp.updated_choice
                else:
                    dissenting_agents.append(agent_id)
            
            max_round = max(resp.round_number for resp in latest_responses.values())
            
            return ConsensusResult(
                unanimous=(agreement_ratio == 1.0),
                agreed_principle=agreed_principle,
                dissenting_agents=dissenting_agents,
                rounds_to_consensus=max_round,
                total_messages=len(responses)
            )
        else:
            # No consensus - insufficient agreement
            most_common_principle = max(principle_counts, key=principle_counts.get)
            dissenting_agents = [
                agent_id for agent_id, resp in latest_responses.items()
                if resp.updated_choice.principle_id != most_common_principle
            ]
            
            return ConsensusResult(
                unanimous=False,
                agreed_principle=None,
                dissenting_agents=dissenting_agents,
                rounds_to_consensus=0,
                total_messages=len(responses)
            )


class ConsensusService:
    """Service for detecting and validating consensus in deliberation."""
    
    def __init__(self, detection_strategy: ConsensusDetectionStrategy = None):
        """
        Initialize consensus service.
        
        Args:
            detection_strategy: Strategy for consensus detection. 
                               Defaults to IdMatchingStrategy for compatibility.
        """
        self.detection_strategy = detection_strategy or IdMatchingStrategy()
    
    async def detect_consensus(self, responses: List[DeliberationResponse]) -> ConsensusResult:
        """
        Detect consensus using the configured strategy.
        
        Args:
            responses: List of deliberation responses to analyze
            
        Returns:
            ConsensusResult with consensus information
        """
        return await self.detection_strategy.detect(responses)
    
    async def validate_consensus(self, result: ConsensusResult, responses: List[DeliberationResponse]) -> bool:
        """
        Validate that consensus is genuine and not due to prompt engineering artifacts.
        
        Args:
            result: ConsensusResult to validate
            responses: Original responses that led to consensus
            
        Returns:
            True if consensus appears genuine, False otherwise
        """
        if not result.unanimous:
            return True  # No consensus to validate
        
        # Basic validation checks
        if not result.agreed_principle:
            return False
        
        # Check that we have responses from multiple agents
        if not responses:
            return False
        
        agent_ids = set(resp.agent_id for resp in responses)
        if len(agent_ids) < 2:
            return False  # Need at least 2 agents for consensus
        
        # Check that consensus wasn't immediate (some deliberation occurred)
        max_round = max(resp.round_number for resp in responses)
        if max_round == 0 and len(responses) < len(agent_ids):
            return False  # Suspiciously quick consensus
        
        # Check for diversity in reasoning (basic check)
        latest_responses = {}
        for response in responses:
            latest_responses[response.agent_id] = response
        
        reasonings = [resp.updated_choice.reasoning for resp in latest_responses.values()]
        unique_reasonings = set(reasonings)
        
        # If all agents have identical reasoning, might be artificial
        if len(unique_reasonings) == 1 and len(reasonings) > 1:
            return False
        
        return True
    
    def set_detection_strategy(self, strategy: ConsensusDetectionStrategy):
        """Change the consensus detection strategy."""
        self.detection_strategy = strategy