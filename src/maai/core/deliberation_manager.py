"""
Multi-round deliberation engine for the distributive justice experiment.
Refactored to use decomposed services for better modularity and testability.
"""

import os 
from dotenv import load_dotenv
from typing import List, Optional
from agents import trace

from .models import (
    ExperimentConfig, 
    ExperimentResults
)
from ..services.experiment_orchestrator import ExperimentOrchestrator
from ..services.consensus_service import ConsensusService
from ..services.conversation_service import ConversationService
from ..services.memory_service import MemoryService

# Load environment variables
load_dotenv()



class DeliberationManager:
    """
    Manages the complete deliberation process from initialization to consensus.
    Refactored to use decomposed services for better modularity and research flexibility.
    """
    
    def __init__(self, config: ExperimentConfig, 
                 consensus_service: ConsensusService = None,
                 conversation_service: ConversationService = None,
                 memory_service: MemoryService = None):
        """
        Initialize DeliberationManager with configurable services.
        
        Args:
            config: Experiment configuration
            consensus_service: Optional custom consensus service
            conversation_service: Optional custom conversation service  
            memory_service: Optional custom memory service
        """
        self.config = config
        
        # Initialize orchestrator with custom services if provided
        self.orchestrator = ExperimentOrchestrator(
            consensus_service=consensus_service,
            conversation_service=conversation_service,
            memory_service=memory_service
        )
        
    async def run_experiment(self) -> ExperimentResults:
        """
        Run the complete deliberation experiment.
        
        Returns:
            ExperimentResults with all data collected
        """
        with trace("deliberation_experiment"):
            try:
                results = await self.orchestrator.run_experiment(self.config)
                return results
            except Exception as e:
                # Let AgentOps auto-capture the error
                raise
    
    # Expose services for advanced users who want to experiment with different strategies
    @property
    def consensus_service(self) -> ConsensusService:
        """Access to the consensus service for strategy experimentation."""
        return self.orchestrator.consensus_service
    
    @property  
    def conversation_service(self) -> ConversationService:
        """Access to the conversation service for communication pattern experimentation."""
        return self.orchestrator.conversation_service
    
    @property
    def memory_service(self) -> MemoryService:
        """Access to the memory service for memory strategy experimentation."""
        return self.orchestrator.memory_service
    
    def get_experiment_state(self) -> dict:
        """Get current experiment state for monitoring."""
        return self.orchestrator.get_experiment_state()


async def run_single_experiment(config: ExperimentConfig) -> ExperimentResults:
    """
    Run a single deliberation experiment with the given configuration.
    
    Args:
        config: Experiment configuration
        
    Returns:
        Complete experiment results
    """
    with trace("single_experiment"):
        manager = DeliberationManager(config)
        return await manager.run_experiment()