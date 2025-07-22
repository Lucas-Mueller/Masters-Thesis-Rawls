"""
Public History Service for managing public conversation history in experiments.
Supports both full and summarized public history modes.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.models import (
    PublicHistoryMode, 
    DeliberationResponse, 
    RoundSummary, 
    ExperimentConfig
)


class PublicHistoryService:
    """
    Service for managing public conversation history in experiments.
    Supports both full and summarized public history modes.
    """
    
    def __init__(self, config: ExperimentConfig):
        """
        Initialize the public history service.
        
        Args:
            config: Experiment configuration containing public history settings
        """
        self.config = config
        self.mode = config.public_history_mode
        self.round_summaries: List[RoundSummary] = []
    
    async def build_public_context(
        self, 
        current_round: int,
        current_round_speakers: List[DeliberationResponse],
        all_previous_responses: List[DeliberationResponse],
        agent_current_choice: Optional[str] = None
    ) -> str:
        """
        Build public context based on the configured history mode.
        
        Args:
            current_round: Current round number
            current_round_speakers: Responses from agents who have spoken this round
            all_previous_responses: All responses from previous rounds
            agent_current_choice: Current agent's principle choice (optional)
            
        Returns:
            Formatted public context string
        """
        if self.mode == PublicHistoryMode.FULL:
            return await self._build_full_public_context(
                current_round, current_round_speakers, all_previous_responses, agent_current_choice
            )
        elif self.mode == PublicHistoryMode.SUMMARIZED:
            return await self._build_summarized_public_context(
                current_round, current_round_speakers, agent_current_choice
            )
        else:
            raise ValueError(f"Unknown public history mode: {self.mode}")
    
    async def _build_full_public_context(
        self,
        current_round: int,
        current_round_speakers: List[DeliberationResponse],
        all_previous_responses: List[DeliberationResponse],
        agent_current_choice: Optional[str] = None
    ) -> str:
        """Build full public context with all previous rounds."""
        context_parts = []
        
        # Add all previous rounds
        if all_previous_responses:
            context_parts.append("PREVIOUS ROUNDS:")
            
            # Group responses by round
            rounds_dict: Dict[int, List[DeliberationResponse]] = {}
            for response in all_previous_responses:
                if response.round_number not in rounds_dict:
                    rounds_dict[response.round_number] = []
                rounds_dict[response.round_number].append(response)
            
            # Add each round chronologically
            for round_num in sorted(rounds_dict.keys()):
                if round_num < current_round:  # Only previous rounds
                    context_parts.append(f"\n--- Round {round_num} ---")
                    round_responses = rounds_dict[round_num]
                    # Sort by speaking position for consistent ordering
                    round_responses.sort(key=lambda x: x.speaking_position)
                    
                    for response in round_responses:
                        context_parts.append(f"{response.agent_name}: {response.public_message}")
        
        # Add current round speakers
        if current_round_speakers:
            context_parts.append(f"\n--- Current Round {current_round} ---")
            context_parts.append("SPEAKERS IN THIS ROUND SO FAR:")
            
            # Sort by speaking position
            sorted_speakers = sorted(current_round_speakers, key=lambda x: x.speaking_position)
            for response in sorted_speakers:
                context_parts.append(f"{response.agent_name}: {response.public_message}")
        
        # Add agent's current choice if provided
        if agent_current_choice:
            context_parts.append(f"\nYour current choice: {agent_current_choice}")
        
        return "\n".join(context_parts)
    
    async def _build_summarized_public_context(
        self,
        current_round: int,
        current_round_speakers: List[DeliberationResponse],
        agent_current_choice: Optional[str] = None
    ) -> str:
        """Build summarized public context using round summaries."""
        context_parts = []
        
        # Add previous round summaries
        if self.round_summaries:
            context_parts.append("PREVIOUS ROUNDS SUMMARY:")
            
            for summary in self.round_summaries:
                if summary.round_number < current_round:
                    context_parts.append(f"\n--- Round {summary.round_number} Summary ---")
                    context_parts.append(summary.summary_text)
        
        # Add current round speakers (always show current round in detail)
        if current_round_speakers:
            context_parts.append(f"\n--- Current Round {current_round} ---")
            context_parts.append("SPEAKERS IN THIS ROUND SO FAR:")
            
            # Sort by speaking position
            sorted_speakers = sorted(current_round_speakers, key=lambda x: x.speaking_position)
            for response in sorted_speakers:
                context_parts.append(f"{response.agent_name}: {response.public_message}")
        
        # Add agent's current choice if provided
        if agent_current_choice:
            context_parts.append(f"\nYour current choice: {agent_current_choice}")
        
        return "\n".join(context_parts)
    
    async def generate_round_summary(
        self, 
        round_number: int, 
        round_responses: List[DeliberationResponse]
    ) -> RoundSummary:
        """
        Generate a summary for a completed round.
        
        Args:
            round_number: The round number to summarize
            round_responses: All responses from the round
            
        Returns:
            Generated round summary
        """
        if not round_responses:
            return RoundSummary(
                round_number=round_number,
                summary_text="No discussion occurred in this round.",
                key_arguments={},
                principle_preferences={},
                consensus_status="No activity",
                summary_agent_model="system"
            )
        
        # Generate simple text-based summary since SummaryAgent was removed
        participants = list(set([r.agent_name for r in round_responses]))
        key_topics = []
        
        for response in round_responses:
            if "principle" in response.public_message.lower():
                key_topics.append(f"{response.agent_name} discussed principles")
            if "income" in response.public_message.lower():
                key_topics.append(f"{response.agent_name} discussed income")
                
        summary_text = f"Round {round_number} had {len(round_responses)} contributions from {', '.join(participants)}."
        if key_topics:
            summary_text += f" Key topics: {'; '.join(key_topics[:3])}."
        
        # Create and store the summary
        round_summary = RoundSummary(
            round_number=round_number,
            summary_text=summary_text,
            key_arguments={agent: f"Participated in round {round_number}" for agent in participants},
            principle_preferences={},
            consensus_status="Discussion ongoing",
            summary_agent_model="system"
        )
        
        # Store for future use
        self.round_summaries.append(round_summary)
        
        return round_summary
    
    def get_round_summaries(self) -> List[RoundSummary]:
        """Get all generated round summaries."""
        return self.round_summaries.copy()
    
    def add_round_summary(self, summary: RoundSummary) -> None:
        """Add a pre-generated round summary."""
        self.round_summaries.append(summary)
    
    def clear_summaries(self) -> None:
        """Clear all stored summaries (for testing)."""
        self.round_summaries.clear()
    
    def get_mode(self) -> PublicHistoryMode:
        """Get the current public history mode."""
        return self.mode
    
    def should_generate_summaries(self) -> bool:
        """Check if summaries should be generated for this configuration."""
        return self.mode == PublicHistoryMode.SUMMARIZED