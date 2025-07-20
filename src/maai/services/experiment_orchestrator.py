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
    PreferenceRanking,
    EconomicOutcome,
    IncomeDistribution,
    get_principle_by_id
)
from ..agents.enhanced import DeliberationAgent, create_deliberation_agents, create_discussion_moderator
from .consensus_service import ConsensusService
from .conversation_service import ConversationService, RoundContext
from .memory_service import MemoryService
from .evaluation_service import EvaluationService
from .experiment_logger import ExperimentLogger
from .public_history_service import PublicHistoryService
from .economics_service import EconomicsService
from .preference_service import PreferenceService
from .validation_service import ValidationService


class ExperimentOrchestrator:
    """High-level orchestrator for deliberation experiments."""
    
    def __init__(self, 
                 consensus_service: ConsensusService = None,
                 conversation_service: ConversationService = None,
                 memory_service: MemoryService = None,
                 evaluation_service: EvaluationService = None,
                 public_history_service: PublicHistoryService = None,
                 economics_service: EconomicsService = None,
                 preference_service: PreferenceService = None,
                 validation_service: ValidationService = None):
        """
        Initialize experiment orchestrator.
        
        Args:
            consensus_service: Service for consensus detection
            conversation_service: Service for conversation management
            memory_service: Service for memory management
            evaluation_service: Service for post-consensus evaluation
            public_history_service: Service for public history management
            economics_service: Service for economic calculations and outcomes
            preference_service: Service for preference ranking collection
            validation_service: Service for principle choice validation
        """
        self.consensus_service = consensus_service or ConsensusService()
        self.conversation_service = conversation_service or ConversationService()
        self.memory_service = memory_service or MemoryService()
        self.evaluation_service = evaluation_service or EvaluationService()
        self.public_history_service = public_history_service
        # New services will be initialized when experiment starts (need config)
        self._economics_service = economics_service
        self._preference_service = preference_service
        self._validation_service = validation_service
        
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
        
        # New game logic state
        self.initial_preference_rankings: List[PreferenceRanking] = []
        self.post_individual_rankings: List[PreferenceRanking] = []
        self.final_preference_rankings: List[PreferenceRanking] = []
        self.economic_outcomes: List[EconomicOutcome] = []
        self.economics_service: Optional[EconomicsService] = None
        self.preference_service: Optional[PreferenceService] = None
        self.validation_service: Optional[ValidationService] = None
        
        # Experiment logger (initialized when experiment starts)
        self.logger: Optional[ExperimentLogger] = None
    
    async def run_experiment(self, config: ExperimentConfig) -> ExperimentResults:
        """
        Run a complete deliberation experiment with new two-phase game logic.
        
        Phase 1: Individual Familiarization
        - Initial preference ranking
        - 4 rounds of individual principle application with economic outcomes
        
        Phase 2: Group Experiment  
        - Group deliberation
        - Secret ballot voting
        - Economic outcomes based on group decision
        - Final preference ranking
        
        Args:
            config: Experiment configuration
            
        Returns:
            Complete experiment results
        """
        self.config = config
        self.start_time = datetime.now()
        
        # Initialize experiment logger
        self.logger = ExperimentLogger(config.experiment_id, config)
        
        # Initialize public history service if not provided
        if self.public_history_service is None:
            self.public_history_service = PublicHistoryService(config)
        
        # Initialize new services with configuration
        self.economics_service = self._economics_service or EconomicsService(
            config.income_distributions, config.payout_ratio
        )
        self.preference_service = self._preference_service or PreferenceService()
        self.validation_service = self._validation_service or ValidationService()
        
        # Update services with logger and public history service
        self.conversation_service.logger = self.logger
        self.conversation_service.public_history_service = self.public_history_service
        self.memory_service.logger = self.logger
        
        print(f"\n=== Starting New Game Logic Experiment ===")
        print(f"Experiment ID: {config.experiment_id}")
        print(f"Agents: {config.num_agents}")
        print(f"Individual Rounds: {config.individual_rounds}")
        print(f"Group Deliberation Max Rounds: {config.max_rounds}")
        print(f"Income Distributions: {len(config.income_distributions)}")
        print(f"Payout Ratio: ${config.payout_ratio:.4f} per $1")
        
        try:
            # Initialize agents
            self._initialize_agents()
            
            # PHASE 1: Individual Familiarization
            print(f"\n=== PHASE 1: Individual Familiarization ===")
            
            # Step 1: Initial preference ranking
            await self._collect_initial_preference_ranking()
            
            # Step 2: Individual principle application rounds
            await self._run_individual_application_rounds()
            
            # Step 3: Post-individual preference ranking
            await self._collect_post_individual_ranking()
            
            # PHASE 2: Group Experiment
            print(f"\n=== PHASE 2: Group Experiment ===")
            
            # Step 4: Group deliberation
            consensus_result = await self._run_group_deliberation()
            
            # Step 5: Secret ballot voting (if no consensus)
            if not consensus_result.unanimous:
                consensus_result = await self._conduct_secret_ballot()
            
            # Step 6: Apply group decision economic outcomes
            await self._apply_group_economic_outcomes(consensus_result)
            
            # Step 7: Final preference ranking
            await self._collect_final_preference_ranking(consensus_result)
            
            # Finalize results
            results = self._finalize_results(consensus_result)
            
            print(f"\n=== Experiment Complete ===")
            print(f"Consensus reached: {consensus_result.unanimous}")
            if consensus_result.unanimous:
                principle = get_principle_by_id(consensus_result.agreed_principle.principle_id)
                print(f"Agreed principle: {principle['name']}")
            print(f"Individual rounds completed: {config.individual_rounds}")
            print(f"Total economic outcomes: {len(self.economic_outcomes)}")
            
            # Phase 8: Log final data and export unified JSON file
            self._log_final_data(consensus_result, results)
            exported_file = self.logger.export_unified_json()
            print(f"\n--- Data Export Complete ---")
            print(f"  Unified Agent-Centric JSON: {exported_file}")
            
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
        
        # Check if already unanimous after initial evaluation
        initial_consensus = await self.consensus_service.detect_consensus(self.transcript)
        if initial_consensus.unanimous:
            print(f"  ✓ Unanimous agreement reached in initial evaluation!")
        else:
            print(f"  Initial choices: {[agent.current_choice.principle_id for agent in self.agents]}")
    
    async def _initial_evaluation(self):
        """Have each agent individually evaluate the principles."""
        print("\n--- Initial Individual Evaluation ---")
        
        # No trace here - part of the main experiment trace
        # Use conversation service to conduct initial Likert assessment
        await self.conversation_service.conduct_initial_likert_assessment(
            self.agents, self.evaluation_service
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
            
            # Generate round summary if using summarized public history mode
            if self.public_history_service and self.public_history_service.should_generate_summaries():
                print(f"  Generating summary for round {round_num}...")
                round_responses = [r for r in self.transcript if r.round_number == round_num]
                if round_responses:
                    try:
                        summary = await self.public_history_service.generate_round_summary(
                            round_num, round_responses
                        )
                        print(f"    ✓ Round summary generated ({len(summary.summary_text)} chars)")
                    except Exception as e:
                        print(f"    ⚠️  Summary generation failed: {e}")
            
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
        
        # Get round summaries from public history service
        round_summaries = []
        if self.public_history_service:
            round_summaries = self.public_history_service.get_round_summaries()
        
        results = ExperimentResults(
            experiment_id=self.config.experiment_id,
            configuration=self.config,
            deliberation_transcript=self.transcript,
            agent_memories=agent_memories,
            speaking_orders=speaking_orders,
            round_summaries=round_summaries,
            consensus_result=consensus_result,
            initial_evaluation_responses=self.initial_evaluation_responses,
            evaluation_responses=self.evaluation_responses,
            feedback_responses=self.feedback_responses,
            performance_metrics=self.performance_metrics,
            start_time=self.start_time,
            end_time=end_time
        )
        
        return results
    
    def _log_final_data(self, consensus_result: ConsensusResult, results: ExperimentResults):
        """Log final experiment data to the new unified logger."""
        if not self.logger:
            return
            
        # Log final consensus data for each agent
        for agent in self.agents:
            agent_satisfaction = None
            # Try to find satisfaction rating from evaluation responses
            for eval_response in self.evaluation_responses:
                if eval_response.agent_id == agent.agent_id:
                    # Get satisfaction with agreed principle
                    if consensus_result.unanimous and consensus_result.agreed_principle:
                        for evaluation in eval_response.principle_evaluations:
                            if evaluation.principle_id == consensus_result.agreed_principle.principle_id:
                                agent_satisfaction = evaluation.satisfaction_rating.value
                                break
                    break
            
            self.logger.log_final_consensus(
                agent_id=agent.name,
                agreement_reached=consensus_result.unanimous,
                agreement_choice=consensus_result.agreed_principle.principle_name if consensus_result.unanimous else None,
                num_rounds=consensus_result.rounds_to_consensus,
                satisfaction=agent_satisfaction
            )
        
        # Log experiment completion
        self.logger.log_experiment_completion(
            consensus_result=consensus_result,
            total_rounds=consensus_result.rounds_to_consensus
        )
    
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
    
    # NEW GAME LOGIC METHODS
    
    async def _collect_initial_preference_ranking(self):
        """Collect initial preference rankings from all agents."""
        print("\n--- Phase 1.1: Initial Preference Ranking ---")
        
        self.initial_preference_rankings = await self.preference_service.collect_batch_preference_rankings(
            self.agents, "initial", "This is your initial assessment of the four distributive justice principles before any individual application or group discussion."
        )
        
        print(f"Collected initial rankings from {len(self.initial_preference_rankings)} agents")
        
        # Log to experiment logger
        for ranking in self.initial_preference_rankings:
            self.logger.log_preference_ranking(ranking)
    
    async def _run_individual_application_rounds(self):
        """Run individual principle application rounds with economic outcomes."""
        print(f"\n--- Phase 1.2: Individual Application Rounds ({self.config.individual_rounds} rounds) ---")
        
        for round_num in range(1, self.config.individual_rounds + 1):
            print(f"\n  Round {round_num}/{self.config.individual_rounds}")
            
            # For each agent, let them choose a principle and apply it
            for agent in self.agents:
                await self._run_individual_round_for_agent(agent, round_num)
        
        print(f"Completed {self.config.individual_rounds} individual rounds with {len(self.economic_outcomes)} total outcomes")
    
    async def _run_individual_round_for_agent(self, agent, round_num):
        """Run a single individual round for one agent."""
        from agents import Runner, ItemHelpers
        
        # Present current distributions if detailed examples are enabled
        distributions_text = ""
        if self.config.enable_detailed_examples and self.config.income_distributions:
            distributions_text = "\nCurrent income distribution scenarios:\n"
            for dist in self.config.income_distributions:
                distributions_text += f"\n{dist.name}:\n"
                for income_class, amount in dist.income_by_class.items():
                    distributions_text += f"  {income_class}: ${amount:,}\n"
        
        prompt = f"""Individual Round {round_num}:

You are now going to make an individual choice about which distributive justice principle to apply to an income distribution scenario.

{distributions_text}

Please choose one of the four principles of distributive justice:
1. MAXIMIZING THE FLOOR INCOME
2. MAXIMIZING THE AVERAGE INCOME  
3. MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT (specify the floor amount in dollars)
4. MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT (specify the range amount in dollars)

Your choice will determine which income distribution is selected, and you will be randomly assigned to an income class.
You will receive actual economic rewards based on your assigned income.

Please state:
1. Your chosen principle (1, 2, 3, or 4)
2. If choosing principle 3 or 4, specify the constraint amount
3. Your reasoning for this choice

Format: "I choose principle [number] [with constraint $X if applicable] because [reasoning]"
"""
        
        # Get agent's choice
        result = await Runner.run(agent, prompt)
        response_text = ItemHelpers.text_message_outputs(result.new_items)
        
        # Parse the principle choice
        principle_choice = await self._parse_individual_principle_choice(response_text, agent.agent_id)
        
        # Validate the choice
        validation_result = self.validation_service.validate_principle_choice(principle_choice)
        if not validation_result['is_valid']:
            print(f"    Invalid choice from {agent.name}: {validation_result['errors']}")
            # For simplicity, default to principle 1 if invalid
            from ..core.models import PrincipleChoice, get_principle_by_id
            principle_choice = PrincipleChoice(
                principle_id=1,
                principle_name=get_principle_by_id(1)['name'],
                reasoning="Invalid choice, defaulted to principle 1"
            )
        
        # Create economic outcome
        economic_outcome = self.economics_service.create_economic_outcome(
            agent.agent_id, round_num, principle_choice
        )
        
        # Store the outcome
        self.economic_outcomes.append(economic_outcome)
        
        print(f"    {agent.name}: Principle {principle_choice.principle_id} -> {economic_outcome.assigned_income_class.value} class (${economic_outcome.actual_income:,}, payout: ${economic_outcome.payout_amount:.2f})")
        
        # Log to experiment logger
        self.logger.log_economic_outcome(economic_outcome)
    
    async def _parse_individual_principle_choice(self, response_text, agent_id):
        """Parse agent's individual principle choice from response text."""
        from ..core.models import PrincipleChoice, get_principle_by_id
        import re
        
        # Try to extract principle number
        principle_match = re.search(r'principle (\d+)', response_text.lower())
        principle_id = int(principle_match.group(1)) if principle_match else 1
        
        # Ensure valid principle ID
        if principle_id not in [1, 2, 3, 4]:
            principle_id = 1
        
        # Try to extract constraints
        floor_constraint = None
        range_constraint = None
        
        if principle_id == 3:
            # Look for floor constraint
            floor_match = re.search(r'\$?([\d,]+)', response_text)
            if floor_match:
                floor_constraint = int(floor_match.group(1).replace(',', ''))
            else:
                # Provide reasonable default floor constraint if not specified
                floor_constraint = 15000  # Default minimum income of $15,000
        
        elif principle_id == 4:
            # Look for range constraint  
            range_match = re.search(r'\$?([\d,]+)', response_text)
            if range_match:
                range_constraint = int(range_match.group(1).replace(',', ''))
            else:
                # Provide reasonable default range constraint if not specified
                range_constraint = 20000  # Default max income difference of $20,000
        
        principle_info = get_principle_by_id(principle_id)
        
        return PrincipleChoice(
            principle_id=principle_id,
            principle_name=principle_info['name'],
            reasoning=response_text,
            floor_constraint=floor_constraint,
            range_constraint=range_constraint
        )
    
    async def _collect_post_individual_ranking(self):
        """Collect preference rankings after individual rounds."""
        print("\n--- Phase 1.3: Post-Individual Preference Ranking ---")
        
        context = f"""You have now completed {self.config.individual_rounds} individual rounds where you applied different principles and received economic outcomes.

Based on your experience with the economic consequences of each principle, please rank the 4 distributive justice principles again."""
        
        self.post_individual_rankings = await self.preference_service.collect_batch_preference_rankings(
            self.agents, "post_individual", context
        )
        
        print(f"Collected post-individual rankings from {len(self.post_individual_rankings)} agents")
        
        # Log to experiment logger
        for ranking in self.post_individual_rankings:
            self.logger.log_preference_ranking(ranking)
    
    async def _run_group_deliberation(self):
        """Run group deliberation phase (similar to existing system)."""
        print(f"\n--- Phase 2.1: Group Deliberation (max {self.config.max_rounds} rounds) ---")
        
        # This reuses the existing deliberation system but with updated context
        return await self._run_deliberation_rounds()
    
    async def _conduct_secret_ballot(self):
        """Conduct secret ballot voting if no consensus was reached."""
        print("\n--- Phase 2.2: Secret Ballot Voting ---")
        
        # For simplicity, collect individual votes privately
        votes = []
        for agent in self.agents:
            vote = await self._collect_secret_vote(agent)
            votes.append(vote)
        
        # Check if votes are unanimous
        principle_ids = [vote.principle_id for vote in votes]
        if len(set(principle_ids)) == 1:
            # Unanimous vote
            agreed_principle = votes[0]
            print(f"Secret ballot achieved unanimity on principle {agreed_principle.principle_id}")
            
            from ..core.models import ConsensusResult
            return ConsensusResult(
                unanimous=True,
                agreed_principle=agreed_principle,
                dissenting_agents=[],
                rounds_to_consensus=0,
                total_messages=0
            )
        else:
            # No unanimity - random outcome
            print("Secret ballot did not achieve unanimity - using random distribution")
            from ..core.models import ConsensusResult
            return ConsensusResult(
                unanimous=False,
                agreed_principle=None,
                dissenting_agents=[agent.agent_id for agent in self.agents],
                rounds_to_consensus=0,
                total_messages=0
            )
    
    async def _collect_secret_vote(self, agent):
        """Collect a secret vote from one agent."""
        from agents import Runner, ItemHelpers
        
        prompt = """SECRET BALLOT VOTE:

Please cast your final vote for which distributive justice principle the group should adopt.

Choose one of the four principles:
1. MAXIMIZING THE FLOOR INCOME
2. MAXIMIZING THE AVERAGE INCOME  
3. MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT (specify the floor amount)
4. MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT (specify the range amount)

Your vote is secret and will not be shared with other agents.

Format your response as: "I vote for principle [number] [with constraint $X if applicable]"
"""
        
        result = await Runner.run(agent, prompt)
        response_text = ItemHelpers.text_message_outputs(result.new_items)
        
        # Parse the vote (reuse existing parsing logic)
        return await self._parse_individual_principle_choice(response_text, agent.agent_id)
    
    async def _apply_group_economic_outcomes(self, consensus_result):
        """Apply economic outcomes based on group decision."""
        print("\n--- Phase 2.3: Group Economic Outcomes ---")
        
        if consensus_result.unanimous:
            # Apply the agreed principle
            principle_choice = consensus_result.agreed_principle
            print(f"Applying agreed principle: {principle_choice.principle_name}")
        else:
            # Random assignment - use a default distribution
            print("No consensus reached - using random distribution assignment")
            # For simplicity, randomly assign everyone to different income classes
            
        # For each agent, create a group economic outcome
        for agent in self.agents:
            if consensus_result.unanimous:
                economic_outcome = self.economics_service.create_economic_outcome(
                    agent.agent_id, 999, consensus_result.agreed_principle  # Use 999 for group round
                )
            else:
                # Random assignment
                assigned_class = self.economics_service.assign_random_income_class()
                # Use first distribution if available, otherwise create default
                if self.config.income_distributions:
                    income = self.economics_service.get_income_for_class(
                        self.config.income_distributions[0], assigned_class
                    )
                else:
                    income = 20000  # Default fallback
                
                from ..core.models import EconomicOutcome
                economic_outcome = EconomicOutcome(
                    agent_id=agent.agent_id,
                    round_number=999,  # Group round
                    chosen_principle=0,  # No principle chosen
                    assigned_income_class=assigned_class,
                    actual_income=income,
                    payout_amount=self.economics_service.calculate_payout(income)
                )
            
            self.economic_outcomes.append(economic_outcome)
            print(f"  {agent.name}: {economic_outcome.assigned_income_class.value} class (${economic_outcome.actual_income:,}, payout: ${economic_outcome.payout_amount:.2f})")
            
            # Log to experiment logger
            self.logger.log_economic_outcome(economic_outcome)
    
    async def _collect_final_preference_ranking(self, consensus_result):
        """Collect final preference rankings after group experiment."""
        print("\n--- Phase 2.4: Final Preference Ranking ---")
        
        if consensus_result.unanimous:
            context = f"""The group discussion is now complete and you have reached unanimous agreement on principle {consensus_result.agreed_principle.principle_id}: {consensus_result.agreed_principle.principle_name}.

You have also received your final economic outcome from the group decision.

Please provide your final ranking of all 4 distributive justice principles based on your complete experience."""
        else:
            context = """The group discussion is complete but no unanimous agreement was reached. You have received a random economic outcome.

Please provide your final ranking of all 4 distributive justice principles based on your complete experience."""
        
        self.final_preference_rankings = await self.preference_service.collect_batch_preference_rankings(
            self.agents, "final", context
        )
        
        print(f"Collected final rankings from {len(self.final_preference_rankings)} agents")
        
        # Log to experiment logger
        for ranking in self.final_preference_rankings:
            self.logger.log_preference_ranking(ranking)
    
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