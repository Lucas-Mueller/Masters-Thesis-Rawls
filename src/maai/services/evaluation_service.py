"""
EvaluationService for conducting principle preference evaluations.
Updated to use preference ranking system instead of Likert scale ratings.
"""

import asyncio
import logging
from typing import List, Optional
from ..core.models import (
    PreferenceRanking, 
    ConsensusResult, 
    DeliberationResponse
)
from .preference_service import PreferenceService

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for conducting principle preference evaluations using rankings."""
    
    def __init__(self, max_concurrent_evaluations: int = 50):
        """
        Initialize the evaluation service.
        
        Args:
            max_concurrent_evaluations: Maximum number of concurrent evaluations
        """
        self.preference_service = PreferenceService(max_concurrent_evaluations)
    
    async def conduct_parallel_evaluation(
        self, 
        agents: List,  # List[DeliberationAgent] - avoiding circular import
        consensus_result: ConsensusResult,
        phase: str = "post_group"
    ) -> List[PreferenceRanking]:
        """
        Conduct parallel preference ranking evaluation by all agents.
        
        Args:
            agents: List of agents to evaluate
            consensus_result: Result of the consensus process
            phase: Phase identifier for the ranking collection
            
        Returns:
            List of preference rankings from all agents
        """
        logger.info(f"Starting parallel preference ranking evaluation with {len(agents)} agents")
        
        # Create context based on consensus result
        if consensus_result.unanimous:
            context = f"""The group has reached unanimous agreement on principle {consensus_result.agreed_principle.principle_id}: {consensus_result.agreed_principle.principle_name}.

Now please rank all 4 principles based on your final assessment after the group discussion."""
        else:
            context = """The group did not reach unanimous agreement on a principle.

Now please rank all 4 principles based on your final assessment after the group discussion."""
        
        # Use preference service to collect rankings
        try:
            preference_rankings = await self.preference_service.collect_batch_preference_rankings(
                agents, phase, context
            )
            logger.info(f"Completed preference ranking evaluation - collected {len(preference_rankings)} rankings")
            return preference_rankings
        except Exception as e:
            logger.error(f"Preference ranking evaluation failed: {e}")
            # Return empty list if evaluation fails
            return []
    
    async def conduct_initial_assessment(
        self,
        agents: List,  # List[DeliberationAgent]
        phase: str = "initial"
    ) -> List[PreferenceRanking]:
        """
        Conduct initial preference ranking assessment (parallel).
        This is purely for data collection before any deliberation.
        
        Args:
            agents: List of agents to assess
            phase: Phase identifier for the ranking collection
            
        Returns:
            List of initial preference rankings
        """
        logger.info(f"Starting initial preference ranking assessment with {len(agents)} agents")
        
        context = """This is your initial assessment before any group discussion.
        
Please rank the 4 distributive justice principles based on your initial preference, without considering input from other agents."""
        
        # Use preference service to collect initial rankings
        try:
            preference_rankings = await self.preference_service.collect_batch_preference_rankings(
                agents, phase, context
            )
            logger.info(f"Completed initial preference ranking assessment - collected {len(preference_rankings)} rankings")
            return preference_rankings
        except Exception as e:
            logger.error(f"Initial preference ranking assessment failed: {e}")
            # Return empty list if assessment fails
            return []
    
    def compare_rankings(self, before: List[PreferenceRanking], after: List[PreferenceRanking]) -> dict:
        """
        Compare preference rankings before and after deliberation.
        
        Args:
            before: Initial preference rankings
            after: Post-deliberation preference rankings
            
        Returns:
            Dictionary with comparison analysis
        """
        comparisons = []
        
        # Match rankings by agent_id
        before_dict = {ranking.agent_id: ranking for ranking in before}
        after_dict = {ranking.agent_id: ranking for ranking in after}
        
        for agent_id in before_dict:
            if agent_id in after_dict:
                comparison = self.preference_service.compare_rankings(
                    before_dict[agent_id], after_dict[agent_id]
                )
                comparison['agent_id'] = agent_id
                comparisons.append(comparison)
        
        # Calculate summary statistics
        total_agents = len(comparisons)
        agents_changed = sum(1 for comp in comparisons if comp['rankings_changed'])
        certainty_changed = sum(1 for comp in comparisons if comp['certainty_changed'])
        
        return {
            'total_agents': total_agents,
            'agents_with_ranking_changes': agents_changed,
            'agents_with_certainty_changes': certainty_changed,
            'percentage_ranking_changes': (agents_changed / total_agents * 100) if total_agents > 0 else 0,
            'percentage_certainty_changes': (certainty_changed / total_agents * 100) if total_agents > 0 else 0,
            'individual_comparisons': comparisons
        }