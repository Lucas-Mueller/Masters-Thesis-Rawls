"""
PreferenceService for collecting and managing agent preference rankings.
Simple service replacing the Likert scale evaluation with 1-4 rankings and certainty levels.
"""

import asyncio
from typing import List
from agents import Runner, ItemHelpers
from ..core.models import (
    PreferenceRanking, 
    CertaintyLevel, 
    get_all_principles_text
)
from ..agents.enhanced import DeliberationAgent


class PreferenceService:
    """
    Simple service for collecting preference rankings from agents.
    Replaces the Likert scale evaluation system with ranking collection.
    """
    
    def __init__(self, max_concurrent_evaluations: int = 50):
        """
        Initialize the preference service.
        
        Args:
            max_concurrent_evaluations: Maximum number of concurrent preference collections
        """
        self.max_concurrent_evaluations = max_concurrent_evaluations
        self.semaphore = asyncio.Semaphore(max_concurrent_evaluations)
    
    async def collect_preference_ranking(
        self, 
        agent: DeliberationAgent, 
        phase: str, 
        context: str = ""
    ) -> PreferenceRanking:
        """
        Collect preference ranking from a single agent.
        
        Args:
            agent: Agent to collect ranking from
            phase: Phase identifier (initial, post_individual, post_group)
            context: Additional context for the ranking request
            
        Returns:
            Agent's preference ranking with certainty level
        """
        async with self.semaphore:
            principles_text = get_all_principles_text()
            
            prompt = f"""Please rank the 4 distributive justice principles from best (1) to worst (4) according to your preference.

{principles_text}

{context}

Please provide your ranking as a numbered list from 1 (best) to 4 (worst), then indicate your certainty level.

Example format:
RANKING:
1. [Principle number] - [Principle name]
2. [Principle number] - [Principle name] 
3. [Principle number] - [Principle name]
4. [Principle number] - [Principle name]

CERTAINTY: [Very Unsure/Unsure/No Opinion/Sure/Very Sure]

REASONING: [Explain your ranking and certainty level]
"""
            
            # Get agent's response
            result = await Runner.run(agent, prompt)
            response_text = ItemHelpers.text_message_outputs(result.new_items)
            
            # Parse the ranking response
            return self._parse_ranking_response(response_text, agent.agent_id, phase)
    
    async def collect_batch_preference_rankings(
        self, 
        agents: List[DeliberationAgent], 
        phase: str,
        context: str = ""
    ) -> List[PreferenceRanking]:
        """
        Collect preference rankings from multiple agents in parallel.
        
        Args:
            agents: List of agents to collect rankings from
            phase: Phase identifier
            context: Additional context for the ranking requests
            
        Returns:
            List of preference rankings from all agents
        """
        tasks = [
            self.collect_preference_ranking(agent, phase, context)
            for agent in agents
        ]
        
        return await asyncio.gather(*tasks)
    
    def _parse_ranking_response(self, response_text: str, agent_id: str, phase: str) -> PreferenceRanking:
        """
        Parse agent's ranking response to extract rankings, certainty, and reasoning.
        
        Args:
            response_text: Raw response from agent
            agent_id: Agent identifier
            phase: Phase identifier
            
        Returns:
            Parsed preference ranking
        """
        lines = response_text.strip().split('\n')
        rankings = []
        certainty_level = CertaintyLevel.NO_OPINION
        reasoning = ""
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.upper().startswith('RANKING:'):
                current_section = 'ranking'
                continue
            elif line.upper().startswith('CERTAINTY:'):
                current_section = 'certainty'
                certainty_text = line.split(':', 1)[1].strip().lower()
                certainty_level = self._parse_certainty_level(certainty_text)
                continue
            elif line.upper().startswith('REASONING:'):
                current_section = 'reasoning'
                reasoning = line.split(':', 1)[1].strip()
                continue
            
            if current_section == 'ranking' and line:
                # Parse ranking line: "1. 2 - Maximize the Average Income"
                try:
                    if line[0].isdigit():
                        parts = line.split('.', 1)[1].strip()
                        principle_num = int(parts.split()[0])
                        rankings.append(principle_num)
                except (ValueError, IndexError):
                    # Skip malformed lines
                    continue
            elif current_section == 'reasoning' and line:
                reasoning += " " + line
        
        # Ensure we have exactly 4 rankings
        if len(rankings) != 4 or set(rankings) != {1, 2, 3, 4}:
            # Default ranking if parsing failed
            rankings = [1, 2, 3, 4]
            reasoning += " [Note: Ranking parsing failed, using default order]"
        
        return PreferenceRanking(
            agent_id=agent_id,
            rankings=rankings,
            certainty_level=certainty_level,
            reasoning=reasoning.strip(),
            phase=phase
        )
    
    def _parse_certainty_level(self, certainty_text: str) -> CertaintyLevel:
        """
        Parse certainty level from response text.
        
        Args:
            certainty_text: Raw certainty text from agent
            
        Returns:
            Parsed certainty level enum
        """
        certainty_text = certainty_text.lower().strip()
        
        if 'very unsure' in certainty_text:
            return CertaintyLevel.VERY_UNSURE
        elif 'very sure' in certainty_text:
            return CertaintyLevel.VERY_SURE
        elif 'unsure' in certainty_text:
            return CertaintyLevel.UNSURE
        elif 'sure' in certainty_text:
            return CertaintyLevel.SURE
        elif 'no opinion' in certainty_text:
            return CertaintyLevel.NO_OPINION
        else:
            return CertaintyLevel.NO_OPINION
    
    def compare_rankings(self, before: PreferenceRanking, after: PreferenceRanking) -> dict:
        """
        Compare two preference rankings to identify changes.
        
        Args:
            before: Initial preference ranking
            after: Later preference ranking
            
        Returns:
            Dictionary with comparison analysis
        """
        changes = []
        for i, (before_rank, after_rank) in enumerate(zip(before.rankings, after.rankings)):
            if before_rank != after_rank:
                changes.append({
                    'position': i + 1,
                    'before': before_rank,
                    'after': after_rank
                })
        
        certainty_change = before.certainty_level != after.certainty_level
        
        return {
            'rankings_changed': len(changes) > 0,
            'changes': changes,
            'certainty_changed': certainty_change,
            'certainty_before': before.certainty_level.to_display(),
            'certainty_after': after.certainty_level.to_display(),
            'num_changes': len(changes)
        }