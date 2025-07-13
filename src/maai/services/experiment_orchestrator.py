"""
ExperimentOrchestrator for high-level experiment coordination.
Coordinates all services to run complete deliberation experiments.
"""

import time
from datetime import datetime
from typing import List, Optional
# No longer need trace import - handled by main caller
from agents.model_settings import ModelSettings
from ..core.models import (
    ExperimentConfig,
    ExperimentResults,
    PerformanceMetrics,
    ConsensusResult,
    DeliberationResponse,
    FeedbackResponse,
    AgentEvaluationResponse,
    AgentMemory,
    get_principle_by_id
)
from ..agents.enhanced import DeliberationAgent, create_deliberation_agents, create_discussion_moderator
from ..export.data_export import export_experiment_data
from .consensus_service import ConsensusService
from .conversation_service import ConversationService, RoundContext
from .memory_service import MemoryService
from .evaluation_service import EvaluationService


class ExperimentOrchestrator:
    """High-level orchestrator for deliberation experiments."""
    
    def __init__(self, 
                 consensus_service: ConsensusService = None,
                 conversation_service: ConversationService = None,
                 memory_service: MemoryService = None,
                 evaluation_service: EvaluationService = None):
        """
        Initialize experiment orchestrator.
        
        Args:
            consensus_service: Service for consensus detection
            conversation_service: Service for conversation management
            memory_service: Service for memory management
            evaluation_service: Service for post-consensus evaluation
        """
        self.consensus_service = consensus_service or ConsensusService()
        self.conversation_service = conversation_service or ConversationService()
        self.memory_service = memory_service or MemoryService()
        self.evaluation_service = evaluation_service or EvaluationService()
        
        # Experiment state
        self.config: Optional[ExperimentConfig] = None
        self.agents: List[DeliberationAgent] = []
        self.moderator = None
        self.transcript: List[DeliberationResponse] = []
        self.initial_evaluation_responses: List[AgentEvaluationResponse] = []
        self.evaluation_responses: List[AgentEvaluationResponse] = []
        self.feedback_responses: List[FeedbackResponse] = []
        self.current_round = 0
        self.start_time: Optional[datetime] = None
        self.performance_metrics = PerformanceMetrics(
            total_duration_seconds=0.0,
            average_round_duration=0.0,
            errors_encountered=0
        )
    
    async def run_experiment(self, config: ExperimentConfig) -> ExperimentResults:
        """
        Run a complete deliberation experiment.
        
        Args:
            config: Experiment configuration
            
        Returns:
            Complete experiment results
        """
        self.config = config
        self.start_time = datetime.now()
        
        print(f"\n=== Starting Deliberation Experiment ===")
        print(f"Experiment ID: {config.experiment_id}")
        print(f"Agents: {config.num_agents}")
        print(f"Decision Rule: {config.decision_rule}")
        print(f"Max Rounds: {config.max_rounds}")
        
        # No trace here - let the main caller handle tracing
        try:
            # Phase 1: Initialize agents
            self._initialize_agents()
            
            # Phase 2: Initial Likert scale assessment (NEW - data collection only)
            await self._initial_likert_assessment()
            
            # Phase 3: Initial individual evaluation (existing - principle choice)
            await self._initial_evaluation()
            
            # Phase 4: Multi-round deliberation
            consensus_result = await self._run_deliberation_rounds()
            
            # Phase 5: Post-consensus evaluation with Likert scale
            await self._conduct_evaluation(consensus_result)
            
            # Phase 6: Post-experiment feedback collection (legacy)
            await self._collect_feedback(consensus_result)
            
            # Phase 7: Finalize results
            results = self._finalize_results(consensus_result)
            
            print(f"\n=== Experiment Complete ===")
            print(f"Consensus reached: {consensus_result.unanimous}")
            if consensus_result.unanimous:
                principle = get_principle_by_id(consensus_result.agreed_principle.principle_id)
                print(f"Agreed principle: {principle['name']}")
            print(f"Total rounds: {consensus_result.rounds_to_consensus}")
            
            # Phase 8: Export data in multiple formats
            exported_files = export_experiment_data(results)
            print(f"\n--- Data Export Complete ---")
            for format_name, filepath in exported_files.items():
                print(f"  {format_name}: {filepath}")
            
            return results
            
        except Exception as e:
            print(f"Error during experiment: {e}")
            self.performance_metrics.errors_encountered += 1
            raise
    
    def _initialize_agents(self):
        """Initialize all deliberation agents."""
        print("\n--- Initializing Agents ---")
        
        self.agents = create_deliberation_agents(
            agent_configs=self.config.agents,
            defaults=self.config.defaults,
            global_temperature=self.config.global_temperature
        )
        
        # Create ModelSettings for moderator (always create, never None)
        if self.config.global_temperature is not None:
            moderator_model_settings = ModelSettings(temperature=self.config.global_temperature)
        else:
            moderator_model_settings = ModelSettings()  # Empty but valid ModelSettings
        
        self.moderator = create_discussion_moderator(model_settings=moderator_model_settings)
        
        print(f"Created {len(self.agents)} deliberation agents")
        for agent in self.agents:
            print(f"  - {agent.name} ({agent.agent_id})")
            # Initialize memory for each agent
            self.memory_service.initialize_agent_memory(agent.agent_id)
    
    async def _initial_likert_assessment(self):
        """Conduct initial Likert scale assessment for data collection."""
        print("\n--- Phase 2: Initial Principle Assessment ---")
        print("  Collecting baseline preferences before any deliberation...")
        
        # Use conversation service to conduct initial assessment
        self.initial_evaluation_responses = await self.conversation_service.conduct_initial_likert_assessment(
            self.agents, self.evaluation_service
        )
        
        print(f"  ✓ Initial assessment complete - {len(self.initial_evaluation_responses)} responses collected")
    
    async def _initial_evaluation(self):
        """Have each agent individually evaluate the principles."""
        print("\n--- Initial Individual Evaluation ---")
        
        # No trace here - part of the main experiment trace
        # Use conversation service to conduct initial evaluation
        await self.conversation_service.conduct_initial_evaluation(
            self.agents, self.transcript
        )
        
        # Check if already unanimous after initial evaluation
        initial_consensus = await self.consensus_service.detect_consensus(self.transcript)
        if initial_consensus.unanimous:
            print(f"  ✓ Unanimous agreement reached in initial evaluation!")
        else:
            print(f"  Initial choices: {[agent.current_choice.principle_id for agent in self.agents]}")
    
    async def _run_deliberation_rounds(self) -> ConsensusResult:
        """Run multiple rounds of deliberation until consensus or timeout."""
        print("\n--- Starting Multi-Round Deliberation ---")
        
        consensus_result = None
        
        for round_num in range(1, self.config.max_rounds + 1):
            print(f"\n--- Round {round_num} ---")
            self.current_round = round_num
            round_start_time = time.time()
            
            # No trace here - part of the main experiment trace
            # Generate speaking order for this round
            speaking_order = self.conversation_service.generate_speaking_order(
                self.agents, round_num
            )
            agent_names = [agent.name for agent in self.agents if agent.agent_id in speaking_order]
            print(f"  Speaking order: {agent_names}")
            
            # Create round context
            round_context = RoundContext(
                round_number=round_num,
                agents=self.agents,
                transcript=self.transcript,
                speaking_order=speaking_order
            )
            
            # Conduct round using conversation service
            await self.conversation_service.conduct_round(
                round_context, self.memory_service, self.moderator
            )
            
            # Check for consensus after round
            consensus_result = await self.consensus_service.detect_consensus(self.transcript)
            
            round_duration = time.time() - round_start_time
            print(f"  Round {round_num} completed in {round_duration:.1f}s")
            
            if consensus_result.unanimous:
                print(f"  ✓ Unanimous agreement reached!")
                break
            else:
                print(f"  Current choices: {[agent.current_choice.principle_id for agent in self.agents]}")
                print(f"  Dissenting agents: {consensus_result.dissenting_agents}")
        
        if not consensus_result or not consensus_result.unanimous:
            print(f"\n  ⚠️  No consensus reached after {self.config.max_rounds} rounds")
        
        return consensus_result or ConsensusResult(
            unanimous=False,
            agreed_principle=None,
            dissenting_agents=[agent.agent_id for agent in self.agents],
            rounds_to_consensus=0,
            total_messages=len(self.transcript)
        )
    
    async def _conduct_evaluation(self, consensus_result: ConsensusResult):
        """Conduct post-consensus evaluation using Likert scale ratings."""
        print("\n--- Post-Consensus Principle Evaluation ---")
        
        if consensus_result.unanimous:
            principle = get_principle_by_id(consensus_result.agreed_principle.principle_id)
            print(f"  Evaluating all principles after consensus on: {principle['name']}")
        else:
            print("  Evaluating all principles after no consensus was reached")
        
        # Use evaluation service for parallel processing
        self.evaluation_responses = await self.evaluation_service.conduct_parallel_evaluation(
            self.agents, 
            consensus_result, 
            self.moderator
        )
        
        # Display evaluation summary
        print(f"  ✓ Collected evaluations from {len(self.evaluation_responses)} agents")
        for response in self.evaluation_responses:
            ratings = [eval.satisfaction_rating.to_display() for eval in response.principle_evaluations]
            print(f"    {response.agent_name}: {ratings}")
            if response.evaluation_duration:
                print(f"      (Evaluation time: {response.evaluation_duration:.1f}s)")
    
    async def _collect_feedback(self, consensus_result: ConsensusResult):
        """Generate simple post-experiment feedback based on agent choices."""
        print("\n--- Post-Experiment Feedback Analysis ---")
        
        if not consensus_result.unanimous:
            print("  No consensus reached - generating feedback based on experience")
        else:
            principle = get_principle_by_id(consensus_result.agreed_principle.principle_id)
            print(f"  Consensus reached on Principle {consensus_result.agreed_principle.principle_id}: {principle['name']}")
        
        # Generate simple feedback based on agent behavior
        for agent in self.agents:
            # Simple satisfaction calculation based on consensus and agent's final choice
            if consensus_result.unanimous:
                # If consensus reached and agent agreed, high satisfaction
                satisfaction = 8 if agent.current_choice.principle_id == consensus_result.agreed_principle.principle_id else 6
                fairness = 8 if agent.current_choice.principle_id == consensus_result.agreed_principle.principle_id else 7
                would_choose_again = agent.current_choice.principle_id == consensus_result.agreed_principle.principle_id
            else:
                # No consensus, moderate satisfaction
                satisfaction = 5
                fairness = 6
                would_choose_again = True
            
            feedback = FeedbackResponse(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                satisfaction_rating=satisfaction,
                fairness_rating=fairness,
                would_choose_again=would_choose_again,
                alternative_preference=None,
                reasoning=f"Generated based on final choice: Principle {agent.current_choice.principle_id}",
                confidence_in_feedback=0.7,
                timestamp=datetime.now()
            )
            
            self.feedback_responses.append(feedback)
            print(f"  {agent.name}: Satisfaction {feedback.satisfaction_rating}/10, Fairness {feedback.fairness_rating}/10")
    
    def _finalize_results(self, consensus_result: ConsensusResult) -> ExperimentResults:
        """Finalize and package all experiment results."""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate performance metrics
        self.performance_metrics.total_duration_seconds = total_duration
        self.performance_metrics.average_round_duration = (
            total_duration / max(1, self.current_round)
        )
        
        # Get agent memories from memory service
        agent_memories = self.memory_service.get_all_agent_memories()
        
        # Get speaking orders from conversation service
        speaking_orders = self.conversation_service.get_speaking_orders()
        
        results = ExperimentResults(
            experiment_id=self.config.experiment_id,
            configuration=self.config,
            deliberation_transcript=self.transcript,
            agent_memories=agent_memories,
            speaking_orders=speaking_orders,
            consensus_result=consensus_result,
            initial_evaluation_responses=self.initial_evaluation_responses,
            evaluation_responses=self.evaluation_responses,
            feedback_responses=self.feedback_responses,
            performance_metrics=self.performance_metrics,
            start_time=self.start_time,
            end_time=end_time
        )
        
        return results
    
    def get_experiment_state(self) -> dict:
        """Get current experiment state for monitoring."""
        return {
            "experiment_id": self.config.experiment_id if self.config else None,
            "current_round": self.current_round,
            "num_agents": len(self.agents),
            "transcript_length": len(self.transcript),
            "start_time": self.start_time,
            "performance_metrics": self.performance_metrics.dict() if self.performance_metrics else None
        }
    
    def reset_experiment(self):
        """Reset orchestrator state for new experiment."""
        self.config = None
        self.agents = []
        self.moderator = None
        self.transcript = []
        self.initial_evaluation_responses = []
        self.evaluation_responses = []
        self.feedback_responses = []
        self.current_round = 0
        self.start_time = None
        self.performance_metrics = PerformanceMetrics(
            total_duration_seconds=0.0,
            average_round_duration=0.0,
            errors_encountered=0
        )
        
        # Reset services
        self.memory_service.clear_all_memories()
        self.conversation_service.speaking_orders = []