"""
ConversationService for managing agent communication flow and patterns.
Handles speaking order generation, round orchestration, and communication patterns.
"""

import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from agents import Runner, ItemHelpers
from ..core.models import DeliberationResponse, PrincipleChoice, MemoryEntry, get_all_principles_text
from ..agents.enhanced import DeliberationAgent


class CommunicationPattern(ABC):
    """Abstract base class for communication patterns."""
    
    @abstractmethod
    def generate_speaking_order(self, agents: List[DeliberationAgent], round_num: int, 
                               previous_orders: List[List[str]]) -> List[str]:
        """
        Generate speaking order for a round.
        
        Args:
            agents: List of agents participating
            round_num: Current round number
            previous_orders: Previous speaking orders (for constraint checking)
            
        Returns:
            List of agent IDs in speaking order
        """
        pass


class RandomCommunicationPattern(CommunicationPattern):
    """
    Random speaking order with constraint: last speaker in round N cannot be first in round N+1.
    This is the current behavior.
    """
    
    def generate_speaking_order(self, agents: List[DeliberationAgent], round_num: int, 
                               previous_orders: List[List[str]]) -> List[str]:
        """Generate random speaking order with constraint."""
        agent_ids = [agent.agent_id for agent in agents]
        
        # For first round or initial evaluation, any order is fine
        if round_num <= 1 or not previous_orders:
            random.shuffle(agent_ids)
            return agent_ids
        
        # Get last speaker from previous round
        previous_order = previous_orders[-1]
        last_speaker = previous_order[-1] if previous_order else None
        
        # Try to generate valid order (last speaker not first)
        for attempt in range(10):
            random.shuffle(agent_ids)
            if last_speaker is None or agent_ids[0] != last_speaker:
                return agent_ids
        
        # Fallback: if can't generate valid order after 10 attempts, 
        # allow consecutive speaking
        return agent_ids


class SequentialCommunicationPattern(CommunicationPattern):
    """Fixed sequential order (A, B, C, A, B, C, ...)."""
    
    def generate_speaking_order(self, agents: List[DeliberationAgent], round_num: int, 
                               previous_orders: List[List[str]]) -> List[str]:
        """Generate sequential speaking order."""
        agent_ids = [agent.agent_id for agent in agents]
        
        # Sort for consistency
        agent_ids.sort()
        
        # Rotate based on round number
        if round_num > 0:
            rotate_by = (round_num - 1) % len(agent_ids)
            agent_ids = agent_ids[rotate_by:] + agent_ids[:rotate_by]
        
        return agent_ids


class HierarchicalCommunicationPattern(CommunicationPattern):
    """Hierarchical pattern where certain agents speak first (leaders)."""
    
    def __init__(self, leader_count: int = 1):
        """
        Initialize hierarchical pattern.
        
        Args:
            leader_count: Number of agents that should speak first
        """
        self.leader_count = leader_count
    
    def generate_speaking_order(self, agents: List[DeliberationAgent], round_num: int, 
                               previous_orders: List[List[str]]) -> List[str]:
        """Generate hierarchical speaking order."""
        agent_ids = [agent.agent_id for agent in agents]
        
        # For simplicity, leaders are the first N agents alphabetically
        sorted_agents = sorted(agent_ids)
        leaders = sorted_agents[:self.leader_count]
        followers = sorted_agents[self.leader_count:]
        
        # Randomize within each group
        random.shuffle(leaders)
        random.shuffle(followers)
        
        return leaders + followers


class RoundContext:
    """Context information for a conversation round."""
    
    def __init__(self, round_number: int, agents: List[DeliberationAgent], 
                 transcript: List[DeliberationResponse], speaking_order: List[str]):
        self.round_number = round_number
        self.agents = agents
        self.transcript = transcript
        self.speaking_order = speaking_order
        self.agent_lookup = {agent.agent_id: agent for agent in agents}
    
    def get_agent_by_id(self, agent_id: str) -> DeliberationAgent:
        """Get agent by ID."""
        agent = self.agent_lookup.get(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")
        return agent


class ConversationService:
    """Service for managing agent communication flow and patterns."""
    
    def __init__(self, communication_pattern: CommunicationPattern = None, logger=None):
        """
        Initialize conversation service.
        
        Args:
            communication_pattern: Pattern for generating speaking orders.
                                  Defaults to RandomCommunicationPattern.
            logger: ExperimentLogger instance for logging agent interactions
        """
        self.pattern = communication_pattern or RandomCommunicationPattern()
        self.speaking_orders: List[List[str]] = []
        self.logger = logger
    
    def generate_speaking_order(self, agents: List[DeliberationAgent], round_num: int) -> List[str]:
        """
        Generate speaking order for a round.
        
        Args:
            agents: List of agents participating
            round_num: Current round number
            
        Returns:
            List of agent IDs in speaking order
        """
        speaking_order = self.pattern.generate_speaking_order(agents, round_num, self.speaking_orders)
        self.speaking_orders.append(speaking_order)
        return speaking_order
    
    async def conduct_initial_evaluation(self, agents: List[DeliberationAgent], 
                                       transcript: List[DeliberationResponse]) -> List[DeliberationResponse]:
        """
        Conduct initial individual evaluation where each agent evaluates principles.
        
        Args:
            agents: List of agents to conduct evaluation
            transcript: Current transcript to append to
            
        Returns:
            List of new DeliberationResponse entries
        """
        print("\n--- Initial Individual Evaluation ---")
        
        # Generate speaking order for initial evaluation
        speaking_order = self.generate_speaking_order(agents, 0)
        agent_names = [next(a.name for a in agents if a.agent_id == agent_id) for agent_id in speaking_order]
        print(f"  Speaking order: {agent_names}")
        
        new_responses = []
        
        for position, agent_id in enumerate(speaking_order, 1):
            agent = next(a for a in agents if a.agent_id == agent_id)
            print(f"\n  --- {agent.name} (Position {position}) ---")
            
            # Initial evaluation prompt
            evaluation_prompt = f"""
{get_all_principles_text()}

Please carefully evaluate each of these four principles of distributive justice.

Consider that:
- You are behind a 'veil of ignorance' - you don't know your future economic position
- Your position (wealthy, middle class, or poor) will be randomly assigned AFTER the group decides

After your evaluation, please:
1. State which principle you choose (1, 2, 3, or 4)
2. Explain your reasoning clearly

Format your response clearly with your final choice at the end.
"""
            
            # Get agent's response
            import time
            start_time = time.time()
            
            result = await Runner.run(agent, evaluation_prompt)
            response_text = ItemHelpers.text_message_outputs(result.new_items)
            processing_time_ms = (time.time() - start_time) * 1000
            
            choice = await self._extract_principle_choice(response_text, agent.agent_id, agent.name)
            
            # Log initial evaluation (round_0) with new unified format
            if self.logger:
                self.logger.log_initial_evaluation(
                    agent_id=agent.name,
                    input_prompt=evaluation_prompt,
                    raw_response=response_text,
                    rating_likert=choice.principle_name,
                    rating_numeric=choice.principle_id
                )
            
            agent.current_choice = choice
            print(f"    Chose Principle {choice.principle_id}")
            
            # Create response entry
            response = DeliberationResponse(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                public_message=response_text,
                private_memory_entry=None,  # No memory for initial evaluation
                updated_choice=choice,
                round_number=0,  # Round 0 for initial evaluation
                timestamp=datetime.now(),
                speaking_position=position
            )
            
            new_responses.append(response)
            transcript.append(response)
        
        return new_responses
    
    async def conduct_initial_likert_assessment(
        self, 
        agents: List[DeliberationAgent],
        evaluation_service  # EvaluationService - avoiding circular import
    ) -> List:  # List[AgentEvaluationResponse] - avoiding circular import
        """
        Conduct initial Likert scale assessment of all principles (parallel).
        This is purely for data collection - no consensus detection or decision making.
        
        Args:
            agents: List of agents to assess
            evaluation_service: Service for parallel evaluation
            
        Returns:
            List of initial evaluation responses
        """
        print("\n--- Initial Principle Assessment (Likert Scale) ---")
        print("  Collecting baseline preference data before deliberation...")
        
        # Create a dummy consensus result for the evaluation service
        # (we're not using consensus logic, just need it for the prompt)
        from ..core.models import ConsensusResult
        dummy_consensus = ConsensusResult(
            unanimous=False,
            agreed_principle=None,
            dissenting_agents=[],
            rounds_to_consensus=0,
            total_messages=0
        )
        
        # Create a simple moderator for parsing (reuse pattern from existing code)
        from ..agents.enhanced import create_discussion_moderator
        moderator = create_discussion_moderator()
        
        # Use evaluation service for parallel assessment
        initial_responses = await evaluation_service.conduct_initial_assessment(
            agents, dummy_consensus, moderator
        )
        
        # Display summary
        print(f"  ✓ Collected initial assessments from {len(initial_responses)} agents")
        for response in initial_responses:
            ratings = [eval.satisfaction_rating.to_display() for eval in response.principle_evaluations]
            print(f"    {response.agent_name}: {ratings}")
            
            # Log structured initial evaluation data
            if self.logger:
                # Create principle ratings dictionary
                principle_ratings = {}
                for eval in response.principle_evaluations:
                    principle_ratings[str(eval.principle_id)] = {
                        "rating": eval.satisfaction_rating.to_numeric(),
                        "rating_text": eval.satisfaction_rating.to_display(),
                        "principle_name": eval.principle_name,
                        "reasoning": eval.reasoning
                    }
                
                # Find the chosen principle (highest rating or explicit choice)
                if response.principle_evaluations:
                    chosen_principle = max(response.principle_evaluations, 
                                         key=lambda x: x.satisfaction_rating.to_numeric())
                    
                    self.logger.log_initial_evaluation(
                        agent_id=response.agent_name,
                        input_prompt="[Initial Likert Assessment - details in principle_ratings]",
                        raw_response=response.overall_reasoning,
                        rating_likert=chosen_principle.principle_name,
                        rating_numeric=chosen_principle.principle_id,
                        principle_ratings=principle_ratings
                    )
                else:
                    # Fallback if no principle evaluations
                    self.logger.log_initial_evaluation(
                        agent_id=response.agent_name,
                        input_prompt="[Initial Likert Assessment - details in principle_ratings]",
                        raw_response=response.overall_reasoning,
                        rating_likert="Unknown",
                        rating_numeric=1,
                        principle_ratings=principle_ratings
                    )
        
        # Set agent.current_choice for each agent based on their highest-rated principle
        # and create DeliberationResponse objects for transcript
        deliberation_responses = []
        
        for agent in agents:
            # Find the corresponding response for this agent
            agent_response = next((r for r in initial_responses if r.agent_id == agent.agent_id), None)
            if agent_response and agent_response.principle_evaluations:
                # Find the highest-rated principle
                chosen_principle = max(agent_response.principle_evaluations, 
                                     key=lambda x: x.satisfaction_rating.to_numeric())
                
                # Create PrincipleChoice object
                from ..core.models import PrincipleChoice, DeliberationResponse
                agent.current_choice = PrincipleChoice(
                    principle_id=chosen_principle.principle_id,
                    principle_name=chosen_principle.principle_name,
                    reasoning=chosen_principle.reasoning
                )
                
                # Create DeliberationResponse for consensus detection
                deliberation_response = DeliberationResponse(
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    public_message=agent_response.overall_reasoning,
                    private_memory_entry=None,
                    updated_choice=agent.current_choice,
                    round_number=0,  # Round 0 for initial evaluation
                    timestamp=datetime.now(),
                    speaking_position=0
                )
                deliberation_responses.append(deliberation_response)
        
        # Add to transcript for consensus detection
        if hasattr(self, 'transcript') and self.transcript is not None:
            self.transcript.extend(deliberation_responses)
        
        return initial_responses
    
    async def conduct_round(self, round_context: RoundContext, 
                          memory_service, moderator) -> List[DeliberationResponse]:
        """
        Conduct a single round of deliberation.
        
        Args:
            round_context: Context for this round
            memory_service: Service for updating agent memory
            moderator: Discussion moderator for choice extraction
            
        Returns:
            List of new DeliberationResponse entries
        """
        new_responses = []
        
        for position, agent_id in enumerate(round_context.speaking_order, 1):
            agent = round_context.get_agent_by_id(agent_id)
            print(f"    {agent.name} (Position {position})")
            
            # Log round start with unified format
            if self.logger:
                public_history = self._build_public_context(agent_id, round_context)
                self.logger.log_round_start(
                    agent_id=agent.name,
                    round_num=round_context.round_number,
                    speaking_order=position,
                    public_history=public_history
                )
            
            # 1. Update agent memory
            private_memory_entry = await memory_service.update_agent_memory(
                agent, round_context.round_number, position, round_context.transcript
            )
            
            # Log memory generation
            if self.logger:
                self.logger.log_memory_generation(
                    agent_id=agent.name,
                    round_num=round_context.round_number,
                    memory_content=private_memory_entry.situation_assessment,
                    strategy=private_memory_entry.strategy_update
                )
            
            # 2. Generate public communication
            public_message = await self._generate_public_communication(
                agent, round_context, private_memory_entry
            )
            
            # 3. Extract principle choice
            updated_choice = await self._extract_principle_choice(public_message, agent.agent_id, agent.name, moderator)
            agent.current_choice = updated_choice
            
            # Log communication and choice
            if self.logger:
                self.logger.log_communication(
                    agent_id=agent.name,
                    round_num=round_context.round_number,
                    communication=public_message,
                    choice=updated_choice.principle_name
                )
            
            # 4. Create response entry
            response = DeliberationResponse(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                public_message=public_message,
                private_memory_entry=private_memory_entry,
                updated_choice=updated_choice,
                round_number=round_context.round_number,
                timestamp=datetime.now(),
                speaking_position=position
            )
            
            new_responses.append(response)
            round_context.transcript.append(response)
            
            print(f"      Chose Principle {updated_choice.principle_id}")
            print(f"      Strategy: {private_memory_entry.strategy_update}")
        
        return new_responses
    
    async def _generate_public_communication(self, agent: DeliberationAgent, 
                                           round_context: RoundContext, 
                                           memory_entry: MemoryEntry) -> str:
        """Generate agent's public communication based on their memory."""
        # Build context for public communication
        public_context = self._build_public_context(agent.agent_id, round_context)
        
        communication_prompt = f"""Now it's your turn to speak publicly to the other agents in round {round_context.round_number}.

Based on your private analysis:
STRATEGY: {memory_entry.strategy_update}

{public_context}


What do you want to say to the group? End with your current principle choice (1, 2, 3, or 4).
"""
        
        # Get public communication
        import time
        start_time = time.time()
        
        # Log interaction with unified format
        if self.logger:
            self.logger.log_agent_interaction(
                agent_id=agent.name,
                round_num=round_context.round_number,
                interaction_type="communication",
                input_prompt=communication_prompt,
                sequence_num=1  # Communication generation step
            )
        
        comm_result = await Runner.run(agent, communication_prompt)
        response_text = ItemHelpers.text_message_outputs(comm_result.new_items)
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Log response with unified format
        if self.logger:
            self.logger.log_agent_interaction(
                agent_id=agent.name,
                round_num=round_context.round_number,
                interaction_type="communication",
                raw_response=response_text,
                sequence_num=1  # Communication generation step
            )
        
        return response_text
    
    def _build_public_context(self, agent_id: str, round_context: RoundContext) -> str:
        """Build context for public communication."""
        context_parts = []
        
        # Current round speakers so far
        current_round_responses = [r for r in round_context.transcript if r.round_number == round_context.round_number]
        if current_round_responses:
            context_parts.append(f"SPEAKERS IN THIS ROUND SO FAR:")
            for response in current_round_responses:
                context_parts.append(f"{response.agent_name}: {response.public_message}")
        
        # Agent's current choice
        agent = round_context.get_agent_by_id(agent_id)
        if agent.current_choice:
            context_parts.append(f"\nYour current choice: Principle {agent.current_choice.principle_id}")
        
        return "\n".join(context_parts)
    
    async def _extract_principle_choice(self, response_text: str, agent_id: str, agent_name: str, moderator=None) -> PrincipleChoice:
        """Extract principle choice from agent response."""
        if moderator is None:
            # Import here to avoid circular dependencies
            from ..agents.enhanced import create_discussion_moderator
            moderator = create_discussion_moderator()
        
        extraction_prompt = f"""
Extract the principle choice from this agent's response:

{response_text}

The agent should have chosen one of these principles:
1. Maximize the Minimum Income
2. Maximize the Average Income  
3. Maximize the Average Income with a Floor Constraint
4. Maximize the Average Income with a Range Constraint

Please respond with ONLY the number (1, 2, 3, or 4) that the agent chose.
If unclear, respond with the number that seems most aligned with their reasoning.
"""
        
        judge_result = await Runner.run(moderator, extraction_prompt)
        choice_text = ItemHelpers.text_message_outputs(judge_result.new_items).strip()
        
        # Extract principle ID
        principle_id = 1  # Default
        for char in choice_text:
            if char.isdigit() and 1 <= int(char) <= 4:
                principle_id = int(char)
                break
        
        from ..core.models import get_principle_by_id
        principle_info = get_principle_by_id(principle_id)
        
        return PrincipleChoice(
            principle_id=principle_id,
            principle_name=principle_info["name"],
            reasoning=response_text  # Full reasoning text, no truncation
        )
    
    def get_speaking_orders(self) -> List[List[str]]:
        """Get all speaking orders used so far."""
        return self.speaking_orders.copy()
    
    def set_communication_pattern(self, pattern: CommunicationPattern):
        """Change the communication pattern."""
        self.pattern = pattern