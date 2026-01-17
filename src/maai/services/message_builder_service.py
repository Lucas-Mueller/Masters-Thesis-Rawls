"""
MessageBuilder service for creating standardized agent messages.
Centralizes all message construction with consistent 4-part structure.
"""

from typing import Optional
from ..core.models import StandardizedMessage, get_all_principles_text
from ..agents.enhanced import DeliberationAgent
from .earnings_tracking_service import EarningsTrackingService


class MessageBuilder:
    """Centralized service for building standardized agent messages."""
    
    def __init__(self, earnings_service: Optional[EarningsTrackingService] = None):
        """
        Initialize the message builder.
        
        Args:
            earnings_service: Optional earnings tracking service for bank balance
        """
        self.earnings_service = earnings_service
    
    def build_message(self, 
                     agent: DeliberationAgent,
                     task_instruction: str,
                     memory_context: str) -> StandardizedMessage:
        """
        Build a standardized message for an agent.
        
        Args:
            agent: The DeliberationAgent to build message for
            task_instruction: Specific task instruction for this interaction
            memory_context: Agent's current memory
            
        Returns:
            StandardizedMessage object with all 4 parts
        """
        return StandardizedMessage(
            role_description=self.get_role_description(agent),
            negotiation_description=self.get_negotiation_description(),
            bank_balance=self.get_standardized_bank_balance(agent.agent_id),
            memory_context=memory_context,
            task_instruction=task_instruction
        )
    
    def get_role_description(self, agent: DeliberationAgent) -> str:
        """
        Get the role description for an agent.
        
        Args:
            agent: The agent to get role description for
            
        Returns:
            Formatted role description
        """
        # Extract personality from agent's current instructions
        # For now, we'll use a default but this could be enhanced
        return getattr(agent, 'personality', 'You are an agent participating in an economic experiment.')
    
    def get_negotiation_description(self) -> str:
        """
        Get the standard negotiation description.
        
        Returns:
            Formatted negotiation description
        """
        return f"""You are participating in a negotiation about distributive justice principles where you and other participants will discuss fair income distribution approaches.

The negotiation consists of two phases:
Phase 1 (Individual): You will learn about principles individually through examples and practice rounds
Phase 2 (Group): You will discuss with other participants to reach agreement on one principle

Your decisions have real financial consequences - you will receive actual monetary payouts based on your assigned income class after the group decides on a principle.

The four principles being considered are:
{get_all_principles_text()}"""
    
    def get_standardized_bank_balance(self, agent_id: str) -> str:
        """
        Get standardized bank balance message.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Standardized bank balance message
        """
        if not self.earnings_service:
            return "You have a current bank balance of $0.0000"
            
        # Validate balance accuracy
        if not self.earnings_service.validate_balance_accuracy(agent_id):
            print(f"WARNING: Bank balance validation failed for {agent_id}")
        
        total_earnings = self.earnings_service.get_agent_total_earnings(agent_id)
        return f"You have a current bank balance of ${total_earnings:.4f}"
    
    
    def validate_balance_accuracy(self, agent_id: str) -> bool:
        """
        Validate that calculated balance matches stored balance.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if balance is accurate, False otherwise
        """
        if not self.earnings_service:
            # If no earnings service, we can't validate but consider it "accurate"
            return True
            
        return self.earnings_service.validate_balance_accuracy(agent_id)