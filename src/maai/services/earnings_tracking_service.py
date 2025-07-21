"""
EarningsTrackingService for tracking and reporting agent earnings throughout the experiment.
Provides comprehensive earnings tracking with strategic disclosure capabilities.
"""

import random
from typing import List, Dict, Optional, Any
from ..core.models import (
    AgentEarnings, 
    EarningsUpdate, 
    EarningsContext, 
    EarningsTrackingConfig,
    IncomeDistribution,
    IncomeClass
)
from ..agents.enhanced import DeliberationAgent


class EarningsTrackingService:
    """
    Service for tracking and reporting agent earnings throughout experiment.
    Manages cumulative earnings tracking and strategic disclosure to agents.
    """
    
    def __init__(self, payout_ratio: float, config: EarningsTrackingConfig, income_distributions: List[IncomeDistribution]):
        """
        Initialize the earnings tracking service.
        
        Args:
            payout_ratio: Ratio for converting income to actual payout
            config: Earnings tracking configuration
            income_distributions: Available income distribution scenarios for range calculations
        """
        self.agent_earnings: Dict[str, AgentEarnings] = {}
        self.payout_ratio = payout_ratio
        self.config = config
        self.income_distributions = income_distributions
        self.disclosure_history: Dict[str, List[str]] = {}  # agent_id -> list of disclosure messages
        self.logger = None  # Will be set by orchestrator
    
    def initialize_agent_earnings(self, agent_id: str) -> None:
        """Initialize earnings tracking for a new agent."""
        if agent_id not in self.agent_earnings:
            self.agent_earnings[agent_id] = AgentEarnings(agent_id=agent_id)
            self.disclosure_history[agent_id] = []
    
    def add_individual_round_payout(self, agent_id: str, payout: float, round_num: int, context: str = "") -> AgentEarnings:
        """
        Add payout from an individual round.
        
        Args:
            agent_id: Agent identifier
            payout: Payout amount
            round_num: Round number
            context: Context description for the payout
            
        Returns:
            Updated AgentEarnings object
        """
        self.initialize_agent_earnings(agent_id)
        earnings = self.agent_earnings[agent_id]
        earnings.add_individual_round_payout(payout, round_num, context)
        
        # Log to experiment logger if available
        if self.logger and earnings.earnings_history:
            latest_update = earnings.earnings_history[-1]
            self.logger.log_earnings_update(agent_id, latest_update)
        
        return earnings
    
    def add_group_payout(self, agent_id: str, payout: float, context: str = "") -> AgentEarnings:
        """
        Add payout from group outcome.
        
        Args:
            agent_id: Agent identifier
            payout: Payout amount
            context: Context description for the payout
            
        Returns:
            Updated AgentEarnings object
        """
        self.initialize_agent_earnings(agent_id)
        earnings = self.agent_earnings[agent_id]
        earnings.add_group_payout(payout, context)
        
        # Log to experiment logger if available
        if self.logger and earnings.earnings_history:
            latest_update = earnings.earnings_history[-1]
            self.logger.log_earnings_update(agent_id, latest_update)
        
        return earnings
    
    def get_agent_total_earnings(self, agent_id: str) -> float:
        """Get total earnings for an agent."""
        if agent_id not in self.agent_earnings:
            return 0.0
        return self.agent_earnings[agent_id].total_earnings
    
    def get_earnings_summary(self, agent_id: str) -> EarningsContext:
        """
        Get earnings context for disclosure to agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            EarningsContext with current earnings and comparative data
        """
        self.initialize_agent_earnings(agent_id)
        earnings = self.agent_earnings[agent_id]
        
        potential_range = self.calculate_potential_earnings_range()
        performance_percentile = self.get_performance_percentile(agent_id)
        
        return EarningsContext(
            agent_id=agent_id,
            current_total=earnings.total_earnings,
            phase1_total=earnings.phase1_earnings,
            phase2_total=earnings.phase2_earnings,
            round_count=len(earnings.individual_round_payouts),
            potential_range=potential_range,
            performance_percentile=performance_percentile
        )
    
    def calculate_potential_earnings_range(self) -> Dict[str, float]:
        """
        Calculate potential earnings range based on income distributions.
        
        Returns:
            Dictionary with 'min' and 'max' potential earnings
        """
        if not self.income_distributions:
            return {"min": 0.0, "max": 0.0}
        
        # Calculate min and max possible incomes across all distributions
        all_incomes = []
        for dist in self.income_distributions:
            all_incomes.extend(dist.income_by_class.values())
        
        min_income = min(all_incomes)
        max_income = max(all_incomes)
        
        # Assume 4 individual rounds + 1 group round for maximum potential
        min_earnings = (min_income * 5) * self.payout_ratio
        max_earnings = (max_income * 5) * self.payout_ratio
        
        return {
            "min": min_earnings,
            "max": max_earnings
        }
    
    def get_performance_percentile(self, agent_id: str) -> float:
        """
        Calculate performance percentile for an agent compared to all agents.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Performance percentile (0.0 to 1.0)
        """
        if agent_id not in self.agent_earnings or len(self.agent_earnings) <= 1:
            return 0.5  # Default to median if no comparison data
        
        agent_total = self.agent_earnings[agent_id].total_earnings
        all_totals = [earnings.total_earnings for earnings in self.agent_earnings.values()]
        all_totals.sort()
        
        # Calculate percentile
        rank = sum(1 for total in all_totals if total < agent_total)
        percentile = rank / len(all_totals)
        
        return percentile
    
    async def generate_earnings_disclosure(self, agent: DeliberationAgent, context: EarningsContext, disclosure_point: str) -> str:
        """
        Generate earnings disclosure message for an agent.
        
        Args:
            agent: The agent to send disclosure to
            context: Earnings context data
            disclosure_point: When this disclosure is happening
            
        Returns:
            Formatted disclosure message
        """
        if not self.config.enabled:
            return ""
        
        style = self.config.disclosure_style
        
        # Base earnings information
        message_parts = []
        
        if disclosure_point == "after_round_2":
            message_parts.append(f"You have now completed {context.round_count} individual rounds and earned ${context.current_total:.2f} total so far.")
            if style in ["motivational", "detailed"]:
                message_parts.append("Your choices and economic outcomes are building your understanding of how different principles affect income distributions.")
                message_parts.append("Continue applying your developing strategy in the remaining rounds.")
        
        elif disclosure_point == "end_phase1":
            message_parts.append(f"Phase 1 Complete! You earned ${context.phase1_total:.2f} total from {context.round_count} individual rounds.")
            
            if self.config.show_potential_ranges:
                min_val = context.potential_range.get("min", 0)
                max_val = context.potential_range.get("max", 0)
                # Adjust range for Phase 1 only (4 rounds typically)
                phase1_min = (min_val * 4) / 5 if min_val > 0 else 0
                phase1_max = (max_val * 4) / 5 if max_val > 0 else 0
                message_parts.append(f"(possible range was ${phase1_min:.2f} - ${phase1_max:.2f})")
            
            if style in ["motivational", "detailed"]:
                message_parts.append("You're now ready to enter group deliberation with this experience.")
                message_parts.append("Your individual learning and earnings will inform your approach to reaching group consensus.")
        
        elif disclosure_point == "after_group":
            message_parts.append(f"Group Decision Payout: ${context.phase2_total:.2f}")
            if self.config.include_phase_breakdown:
                message_parts.append(f"Phase 1 Total: ${context.phase1_total:.2f}")
            message_parts.append(f"Grand Total: ${context.current_total:.2f}")
        
        elif disclosure_point == "experiment_end":
            message_parts.append(f"Experiment Complete! Your total earnings: ${context.current_total:.2f}")
            
            if self.config.include_phase_breakdown:
                message_parts.append(f"- Phase 1 (Individual): ${context.phase1_total:.2f} ({context.round_count} rounds)")
                message_parts.append(f"- Phase 2 (Group): ${context.phase2_total:.2f} (final outcome)")
            
            # Performance context
            if self.config.show_performance_context and context.performance_percentile is not None:
                percentile_display = int(context.performance_percentile * 100)
                if context.performance_percentile >= self.config.congratulatory_threshold:
                    performance_msg = f"Performance: {percentile_display}th percentile (excellent performance!)"
                elif context.performance_percentile <= self.config.encouragement_threshold:
                    performance_msg = f"Performance: {percentile_display}th percentile (thank you for your participation)"
                else:
                    performance_msg = f"Performance: {percentile_display}th percentile (above average)"
                message_parts.append(performance_msg)
            
            if style in ["motivational", "detailed"]:
                message_parts.append("Thank you for your thoughtful participation in this distributive justice experiment.")
        
        # Join message parts
        disclosure_message = "\n".join(message_parts)
        
        # Store disclosure history
        if context.agent_id not in self.disclosure_history:
            self.disclosure_history[context.agent_id] = []
        self.disclosure_history[context.agent_id].append(f"{disclosure_point}: {disclosure_message}")
        
        # Log to experiment logger if available
        if self.logger:
            self.logger.log_earnings_disclosure(context.agent_id, disclosure_point, disclosure_message)
        
        return disclosure_message
    
    def should_disclose_at_point(self, disclosure_point: str) -> bool:
        """Check if disclosure should happen at this point based on configuration."""
        return self.config.enabled and disclosure_point in self.config.disclosure_points
    
    def get_all_agent_earnings(self) -> Dict[str, AgentEarnings]:
        """Get earnings data for all agents."""
        return self.agent_earnings.copy()
    
    def get_disclosure_history(self, agent_id: str) -> List[str]:
        """Get disclosure history for an agent."""
        return self.disclosure_history.get(agent_id, []).copy()
    
    def get_total_experiment_payouts(self) -> Dict[str, float]:
        """Get total payouts for all agents as a summary dictionary."""
        return {
            agent_id: earnings.total_earnings 
            for agent_id, earnings in self.agent_earnings.items()
        }