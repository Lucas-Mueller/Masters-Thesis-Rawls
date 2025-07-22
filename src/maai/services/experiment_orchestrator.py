"""
ExperimentOrchestrator for high-level experiment coordination.
Coordinates all services to run complete deliberation experiments.
"""

import time
from datetime import datetime
from typing import List, Optional
from agents import gen_trace_id
from agents.model_settings import ModelSettings
from ..core.models import (
    ExperimentConfig,
    ExperimentResults,
    PerformanceMetrics,
    ConsensusResult,
    DeliberationResponse,
    AgentEvaluationResponse,
    PreferenceRanking,
    EconomicOutcome,
    IncomeDistribution,
    get_principle_by_id,
    IndividualReflectionContext,
    LearningContext,
    Phase1ExperienceData
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
from .detailed_examples_service import DetailedExamplesService
from .earnings_tracking_service import EarningsTrackingService


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
        self.detailed_examples_service: Optional[DetailedExamplesService] = None
        self.earnings_tracking_service: Optional[EarningsTrackingService] = None
        
        # Experiment logger (initialized when experiment starts)
        self.logger: Optional[ExperimentLogger] = None
        
        # Tracing
        self.trace_id: Optional[str] = None
    
    async def run_experiment(self, config: ExperimentConfig, trace_id: str = None) -> ExperimentResults:
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
            trace_id: Optional trace ID for OpenAI Agents SDK tracing
            
        Returns:
            Complete experiment results
        """
        self.config = config
        self.start_time = datetime.now()
        self.trace_id = trace_id or gen_trace_id()
        
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
        self.detailed_examples_service = DetailedExamplesService(self.economics_service)
        self.earnings_tracking_service = EarningsTrackingService(
            config.payout_ratio, 
            config.earnings_tracking, 
            config.income_distributions
        )
        
        # Update services with logger and public history service
        self.conversation_service.logger = self.logger
        self.conversation_service.public_history_service = self.public_history_service
        self.memory_service.logger = self.logger
        self.earnings_tracking_service.logger = self.logger
        
        # Configure Phase 1 memory settings
        self.memory_service.enable_phase1_memory = config.enable_phase1_memory
        
        print(f"\n=== Starting New Game Logic Experiment ===")
        print(f"Experiment ID: {config.experiment_id}")
        print(f"Agents: {config.num_agents}")
        print(f"Individual Rounds: 4 (fixed per new_logic.md)")
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
            
            # Step 1.5: Present detailed examples (if enabled)
            if getattr(config, 'enable_detailed_examples', True):
                await self._present_detailed_examples()
                # Step 1.6: Second Assessment - Post-examples preference ranking
                await self._collect_post_examples_preference_ranking()
            
            # Step 2: Individual principle application rounds  
            await self._run_individual_application_rounds()
            
            # Step 3: Third Assessment - Post-individual preference ranking (moved to end of individual rounds)
            
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
            
            # Final earnings disclosure
            await self._final_earnings_disclosure()
            
            # Finalize results
            results = self._finalize_results(consensus_result)
            
            print(f"\n=== Experiment Complete ===")
            print(f"Consensus reached: {consensus_result.unanimous}")
            if consensus_result.unanimous:
                principle = get_principle_by_id(consensus_result.agreed_principle.principle_id)
                print(f"Agreed principle: {principle['name']}")
            print(f"Individual rounds completed: {self.config.individual_rounds}")
            print(f"Total economic outcomes: {len(self.economic_outcomes)}")
            
            # Phase 8: Log final data and export unified JSON file
            self._log_final_data(consensus_result, results)
            exported_file = self.logger.export_unified_json()
            print(f"\n--- Data Export Complete ---")
            print(f"  Unified Agent-Centric JSON: {exported_file}")
            
            # Print trace information
            if self.trace_id:
                print(f"\n--- Tracing Information ---")
                print(f"  Trace ID: {self.trace_id}")
                print(f"  View trace: https://platform.openai.com/traces/trace?trace_id={self.trace_id}")
            
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
        
        # Get earnings data
        agent_earnings_list = []
        earnings_disclosures = {}
        if self.earnings_tracking_service:
            agent_earnings_dict = self.earnings_tracking_service.get_all_agent_earnings()
            agent_earnings_list = list(agent_earnings_dict.values())
            
            for agent_id in agent_earnings_dict.keys():
                earnings_disclosures[agent_id] = self.earnings_tracking_service.get_disclosure_history(agent_id)
            
            # Log final earnings summaries to experiment logger
            for earnings in agent_earnings_list:
                self.logger.log_agent_earnings_summary(earnings)
        
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
            performance_metrics=self.performance_metrics,
            start_time=self.start_time,
            end_time=end_time,
            agent_earnings=agent_earnings_list,
            earnings_disclosures=earnings_disclosures
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
            self.logger.log_first_assessment(ranking)
        
        # Generate Phase 1 memory: Initial reflection
        if self.config.enable_phase1_memory and self.config.phase1_memory_frequency in ["each_activity", "each_round"]:
            print("Generating initial reflection memories...")
            for agent in self.agents:
                # Find this agent's ranking
                agent_ranking = next((r for r in self.initial_preference_rankings if r.agent_id == agent.agent_id), None)
                if agent_ranking:
                    reflection_context = IndividualReflectionContext(
                        activity="initial_ranking",
                        data={"rankings": agent_ranking.rankings, "certainty": agent_ranking.certainty_level.value},
                        reasoning_prompt="Why did you rank the four distributive justice principles in this order? What factors influenced your initial assessment?"
                    )
                    await self.memory_service.generate_individual_reflection(agent, reflection_context)
    
    async def _present_detailed_examples(self):
        """Present detailed examples showing principle outcome mappings."""
        print("\n--- Phase 1.2: Detailed Examples ---")
        print("Presenting detailed examples of principle outcomes to agents...")
        
        await self.detailed_examples_service.present_detailed_examples(self.agents)
        
        print(f"Detailed examples presented to {len(self.agents)} agents")
        
        # Log to experiment logger
        if self.logger:
            analysis = self.economics_service.analyze_all_principle_outcomes()
            self.logger.log_detailed_examples_phase(
                timestamp=datetime.now(),
                analysis=analysis
            )
        
        # Generate Phase 1 memory: Learning from examples
        if self.config.enable_phase1_memory and self.config.phase1_memory_frequency in ["each_activity", "each_round"]:
            print("Generating learning memories from detailed examples...")
            for agent in self.agents:
                # Get the analysis for learning context
                principle_analysis = self.economics_service.analyze_all_principle_outcomes()
                examples_summary = f"Saw {len(self.config.income_distributions)} income distribution scenarios across 4 principles"
                
                learning_context = LearningContext(
                    learning_stage="detailed_examples",
                    new_information=f"Detailed examples showing how each principle maps to specific income distributions. {examples_summary}",
                    previous_understanding="Initial rankings based on principle descriptions only"
                )
                await self.memory_service.update_individual_learning(agent, learning_context)
    
    async def _collect_post_examples_preference_ranking(self):
        """Collect preference rankings after detailed examples (Second Assessment)."""
        print("\n--- Phase 1.2.1: Second Assessment (After Detailed Examples) ---")
        
        post_examples_rankings = await self.preference_service.collect_batch_preference_rankings(
            self.agents, 
            "post_examples", 
            "Now that you have seen detailed examples of how each principle maps to specific income distributions, please rank the principles again."
        )
        
        print(f"Collected post-examples rankings from {len(post_examples_rankings)} agents")
        
        # Store and log rankings
        for ranking in post_examples_rankings:
            self.logger.log_second_assessment(ranking)
    
    async def _run_individual_application_rounds(self):
        """Run configurable number of individual principle application rounds with economic outcomes."""
        rounds_count = self.config.individual_rounds
        print(f"\n--- Phase 1.3: Individual Application Rounds ({rounds_count} rounds) ---")
        
        for round_num in range(1, rounds_count + 1):  # Use configurable count
            print(f"\n  Round {round_num}/{rounds_count}")
            
            # For each agent, let them choose a principle and apply it
            for agent in self.agents:
                await self._run_individual_round_for_agent(agent, round_num)
        
        print(f"Completed {rounds_count} individual rounds with {len(self.economic_outcomes)} total outcomes")
        
        # Step 3: Third Assessment - Post-individual preference ranking
        await self._collect_post_individual_preference_ranking()
        
        # End of Phase 1 earnings disclosure
        await self._phase1_end_earnings_disclosure()
    
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
        
        # Track earnings for this agent
        context_description = f"Round {round_num}: {principle_choice.principle_name}, {economic_outcome.assigned_income_class.value} class, ${economic_outcome.actual_income:,}"
        self.earnings_tracking_service.add_individual_round_payout(
            agent.agent_id, 
            economic_outcome.payout_amount, 
            round_num, 
            context_description
        )
        
        print(f"    {agent.name}: Principle {principle_choice.principle_id} -> {economic_outcome.assigned_income_class.value} class (${economic_outcome.actual_income:,}, payout: ${economic_outcome.payout_amount:.2f})")
        
        # Check for strategic earnings disclosure
        await self._check_earnings_disclosure(agent, round_num)
        
        # Log to experiment logger
        self.logger.log_economic_outcome(economic_outcome)
        
        # Generate Phase 1 memory: Experience integration
        if self.config.enable_phase1_memory and self.config.phase1_memory_frequency in ["each_activity", "each_round"]:
            experience_data = Phase1ExperienceData(
                round_number=round_num,
                principle_choice=principle_choice,
                economic_outcome=economic_outcome,
                reflection_prompt=f"What did you learn from Round {round_num}? How did the economic outcome (${economic_outcome.actual_income:,} as {economic_outcome.assigned_income_class.value}) affect your thinking about distributive justice principles?"
            )
            await self.memory_service.integrate_phase1_experience(agent, experience_data)
    
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
    
    async def _collect_post_individual_preference_ranking(self):
        """Collect preference rankings after individual rounds (Third Assessment)."""
        print("\n--- Phase 1.3.1: Third Assessment (After Individual Application) ---")
        
        rounds_count = self.config.individual_rounds
        context = f"""You have now completed {rounds_count} individual rounds where you applied different principles and received economic outcomes.

Based on your actual experience with applying principles and receiving economic rewards, please rank the 4 distributive justice principles again."""
        
        self.post_individual_rankings = await self.preference_service.collect_batch_preference_rankings(
            self.agents, "post_individual", context
        )
        
        print(f"Collected post-individual rankings from {len(self.post_individual_rankings)} agents")
        
        # Log to experiment logger
        for ranking in self.post_individual_rankings:
            self.logger.log_third_assessment(ranking)
        
        # Generate Phase 1 memory: Final reflection
        if self.config.enable_phase1_memory and self.config.phase1_memory_frequency in ["each_activity", "phase_end"]:
            print("Generating post-individual reflection memories...")
            for agent in self.agents:
                # Find this agent's ranking
                agent_ranking = next((r for r in self.post_individual_rankings if r.agent_id == agent.agent_id), None)
                if agent_ranking:
                    # Get agent's economic outcomes for context
                    agent_outcomes = [outcome for outcome in self.economic_outcomes if outcome.agent_id == agent.agent_id]
                    outcomes_summary = f"Completed {len(agent_outcomes)} individual rounds with varied economic outcomes"
                    
                    reflection_context = IndividualReflectionContext(
                        activity="post_individual_ranking",
                        data={
                            "new_rankings": agent_ranking.rankings, 
                            "certainty": agent_ranking.certainty_level.value,
                            "economic_experiences": outcomes_summary
                        },
                        reasoning_prompt=f"How has your experience with {rounds_count} individual rounds and actual economic outcomes changed your ranking of the distributive justice principles? What insights did you gain?"
                    )
                    await self.memory_service.generate_individual_reflection(agent, reflection_context)
    
    async def _run_group_deliberation(self):
        """Run group deliberation phase (similar to existing system)."""
        print(f"\n--- Phase 1 to Phase 2 Transition: Memory Consolidation ---")
        
        # Consolidate Phase 1 memories before starting group deliberation
        if self.config.enable_phase1_memory and self.config.phase1_memory_integration:
            print("Consolidating individual phase memories...")
            for agent in self.agents:
                consolidated_memory = await self.memory_service.consolidate_phase1_memories(agent.agent_id)
                if consolidated_memory:
                    print(f"  {agent.name}: Consolidated {len(self.memory_service.get_agent_memory(agent.agent_id).individual_memories)} individual memories")
        
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
            
            # Track group earnings
            if consensus_result.unanimous:
                context_description = f"Group decision: {principle_choice.principle_name}, {economic_outcome.assigned_income_class.value} class, ${economic_outcome.actual_income:,}"
            else:
                context_description = f"Random assignment: {economic_outcome.assigned_income_class.value} class, ${economic_outcome.actual_income:,}"
            
            self.earnings_tracking_service.add_group_payout(
                agent.agent_id,
                economic_outcome.payout_amount,
                context_description
            )
            
            print(f"  {agent.name}: {economic_outcome.assigned_income_class.value} class (${economic_outcome.actual_income:,}, payout: ${economic_outcome.payout_amount:.2f})")
            
            # Log to experiment logger
            self.logger.log_economic_outcome(economic_outcome)
        
        # After-group earnings disclosure
        await self._after_group_earnings_disclosure(consensus_result)
    
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
    
    async def _check_earnings_disclosure(self, agent, round_num):
        """Check if earnings should be disclosed at this point."""
        if not self.earnings_tracking_service or not self.earnings_tracking_service.config.enabled:
            return
        
        # After round 2 disclosure
        if round_num == 2 and self.earnings_tracking_service.should_disclose_at_point("after_round_2"):
            await self._send_earnings_disclosure(agent, "after_round_2")
    
    async def _phase1_end_earnings_disclosure(self):
        """Send Phase 1 end earnings disclosure to all agents."""
        if not self.earnings_tracking_service or not self.earnings_tracking_service.should_disclose_at_point("end_phase1"):
            return
        
        print("\n--- Phase 1 Earnings Summary ---")
        for agent in self.agents:
            await self._send_earnings_disclosure(agent, "end_phase1")
    
    async def _send_earnings_disclosure(self, agent, disclosure_point):
        """Send earnings disclosure to an agent."""
        from agents import Runner, ItemHelpers
        
        # Get earnings context
        context = self.earnings_tracking_service.get_earnings_summary(agent.agent_id)
        
        # Generate disclosure message
        disclosure_message = await self.earnings_tracking_service.generate_earnings_disclosure(
            agent, context, disclosure_point
        )
        
        if disclosure_message:
            print(f"  Earnings disclosure to {agent.name}: {disclosure_message}")
            
            # Send disclosure message to agent
            prompt = f"""EARNINGS UPDATE:

{disclosure_message}

Please acknowledge that you have received this earnings information with a brief response."""
            
            try:
                result = await Runner.run(agent, prompt)
                response_text = ItemHelpers.text_message_outputs(result.new_items)
                print(f"    {agent.name} acknowledged: {response_text[:100]}...")
            except Exception as e:
                print(f"    Error sending earnings disclosure to {agent.name}: {e}")
    
    async def _after_group_earnings_disclosure(self, consensus_result):
        """Send after-group earnings disclosure to all agents."""
        if not self.earnings_tracking_service or not self.earnings_tracking_service.should_disclose_at_point("after_group"):
            return
        
        print("\n--- Group Outcome Earnings Summary ---")
        for agent in self.agents:
            await self._send_earnings_disclosure(agent, "after_group")
    
    async def _final_earnings_disclosure(self):
        """Send final experiment earnings disclosure to all agents."""
        if not self.earnings_tracking_service or not self.earnings_tracking_service.should_disclose_at_point("experiment_end"):
            return
        
        print("\n--- Final Earnings Summary ---")
        for agent in self.agents:
            await self._send_earnings_disclosure(agent, "experiment_end")