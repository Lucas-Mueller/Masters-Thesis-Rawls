"""
Multi-round deliberation engine for the distributive justice experiment.
Refactored to use decomposed services for better modularity and testability.

This module demonstrates SERVICE-ORIENTED ARCHITECTURE where complex functionality
is broken down into specialized services that can be mixed and matched.
"""

import os 
from dotenv import load_dotenv
from typing import List, Optional
from agents import trace

# Import the data models that define the structure of our experiments
from .models import (
    ExperimentConfig,  # Configuration for how the experiment should run
    ExperimentResults  # Results data structure containing all experiment outcomes
)
# Import all the specialized services that handle different aspects of experiments
from ..services.experiment_orchestrator import ExperimentOrchestrator
from ..services.consensus_service import ConsensusService
from ..services.conversation_service import ConversationService
from ..services.memory_service import MemoryService, create_memory_strategy

# Load environment variables (like API keys) from .env file
load_dotenv()



class DeliberationManager:
    """
    FACADE PATTERN: This class provides a simple interface for complex operations.
    
    Think of this like a TV remote control - you press one button "turn on TV"
    but behind the scenes it coordinates many systems (power, display, sound, etc.).
    
    Similarly, this class provides simple methods like "run_experiment()" 
    but coordinates many complex services behind the scenes.
    
    The key design principle is DEPENDENCY INJECTION - instead of hard-coding
    which services to use, we let the user choose (or provide sensible defaults).
    """
    
    def __init__(self, config: ExperimentConfig, 
                 consensus_service: ConsensusService = None,
                 conversation_service: ConversationService = None,
                 memory_service: MemoryService = None):
        """
        CONSTRUCTOR: Sets up the DeliberationManager with all its dependencies.
        
        DEPENDENCY INJECTION PATTERN:
        - Instead of creating services inside this class, we accept them as parameters
        - This makes the code more flexible and testable
        - If no service is provided, the orchestrator will create default ones
        
        Args:
            config: The experiment configuration (how many agents, rounds, etc.)
            consensus_service: Optional service for detecting when agents agree
            conversation_service: Optional service for managing who speaks when
            memory_service: Optional service for managing what agents remember
        """
        # Store the configuration - this is COMPOSITION (object contains other objects)
        self.config = config
        
        # DELEGATION PATTERN: Instead of doing the work ourselves, we delegate to a specialist
        # The ExperimentOrchestrator is like hiring a general contractor who coordinates
        # all the specialized workers (consensus service, conversation service, etc.)
        self.orchestrator = ExperimentOrchestrator(
            consensus_service=consensus_service,
            conversation_service=conversation_service,
            memory_service=memory_service
        )
        
    async def run_experiment(self) -> ExperimentResults:
        """
        MAIN METHOD: Run the complete deliberation experiment.
        
        This method demonstrates the FACADE PATTERN in action - it provides a simple
        interface but delegates all the complex work to the orchestrator.
        
        The 'async' keyword means this is an ASYNCHRONOUS function - it can pause
        and resume while waiting for things like AI agent responses.
        
        Returns:
            ExperimentResults: A structured object containing all experiment data
        """
        # ERROR HANDLING: We use try/except to catch any problems
        try:
            # DELEGATION: We don't do the work ourselves - we ask the orchestrator to do it
            # This is like a manager asking their team to handle the details
            results = await self.orchestrator.run_experiment(self.config)
            return results
        except Exception as e:
            # EXCEPTION PROPAGATION: If something goes wrong, we let it bubble up
            # to the caller who can decide how to handle it
            raise
    
    # PROPERTY PATTERN: These methods look like simple attributes but actually
    # delegate to the orchestrator. This is ENCAPSULATION - hiding internal details
    # while providing controlled access to internal services.
    
    @property
    def consensus_service(self) -> ConsensusService:
        """
        PROPERTY: Provides access to the consensus service for advanced users.
        
        This demonstrates CONTROLLED ACCESS - advanced users can access internal
        services to experiment with different strategies, but they have to go
        through this controlled interface.
        """
        return self.orchestrator.consensus_service
    
    @property  
    def conversation_service(self) -> ConversationService:
        """
        PROPERTY: Provides access to the conversation service for advanced users.
        
        Example usage: manager.conversation_service.set_pattern("sequential")
        """
        return self.orchestrator.conversation_service
    
    @property
    def memory_service(self) -> MemoryService:
        """
        PROPERTY: Provides access to the memory service for advanced users.
        
        Example usage: manager.memory_service.set_strategy("recent_only")
        """
        return self.orchestrator.memory_service
    
    def get_experiment_state(self) -> dict:
        """
        DELEGATION: Get current experiment state for monitoring.
        
        This method demonstrates how we can expose internal state without
        exposing the internal implementation details.
        """
        return self.orchestrator.get_experiment_state()


async def run_single_experiment(config: ExperimentConfig) -> ExperimentResults:
    """
    CONVENIENCE FUNCTION: Run a single deliberation experiment with default settings.
    
    This is a FACTORY FUNCTION pattern - it creates and configures objects for you.
    Most users will call this function instead of creating DeliberationManager directly.
    
    Think of this like a "one-click" button that handles all the setup for you.
    
    Args:
        config: Experiment configuration (loaded from YAML file typically)
        
    Returns:
        Complete experiment results with all data collected
    """
    # TRACING: We wrap the entire experiment in a trace for monitoring/debugging
    # This is like adding a "tracking number" to monitor the experiment's progress
    trace_name = f"Distributive Justice Experiment - {config.experiment_id}"
    
    # CONTEXT MANAGER: The 'with' statement ensures the trace is properly closed
    with trace(trace_name):
        # FACTORY PATTERN: Create services based on configuration
        memory_strategy = create_memory_strategy(config.memory_strategy)
        memory_service = MemoryService(memory_strategy=memory_strategy)
        
        # Create a manager with configured services
        manager = DeliberationManager(config, memory_service=memory_service)
        
        # DELEGATION: Let the manager handle all the complex work
        return await manager.run_experiment()