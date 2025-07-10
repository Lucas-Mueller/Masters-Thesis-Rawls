"""
Multi-round deliberation engine for the distributive justice experiment.
Manages the conversation flow, consensus detection, and data collection.
"""

import asyncio
import time
import random
from datetime import datetime
from typing import List, Optional

from agents import Runner, ItemHelpers, trace
from .models import (
    DeliberationResponse, 
    ConsensusResult, 
    ExperimentConfig, 
    ExperimentResults,
    PerformanceMetrics,
    PrincipleChoice,
    FeedbackResponse,
    MemoryEntry,
    AgentMemory,
    get_principle_by_id,
    get_all_principles_text,
    detect_consensus
)
from ..agents.enhanced import (
    DeliberationAgent, 
    DiscussionModerator,
    FeedbackCollector,
    create_deliberation_agents,
    create_discussion_moderator,
    create_feedback_collector
)
from ..export.data_export import export_experiment_data


class DeliberationManager:
    """
    Manages the complete deliberation process from initialization to consensus.
    """
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.agents: List[DeliberationAgent] = []
        self.moderator: DiscussionModerator = create_discussion_moderator()
        self.feedback_collector: FeedbackCollector = create_feedback_collector()
        self.transcript: List[DeliberationResponse] = []
        self.feedback_responses: List[FeedbackResponse] = []
        self.agent_memories: List[AgentMemory] = []
        self.speaking_orders: List[List[str]] = []
        self.current_round = 0
        self.start_time: Optional[datetime] = None
        self.performance_metrics = PerformanceMetrics(
            total_duration_seconds=0.0,
            average_round_duration=0.0,
            total_tokens_used=0,
            api_calls_made=0,
            errors_encountered=0
        )
        
    async def run_experiment(self) -> ExperimentResults:
        """
        Run the complete deliberation experiment.
        
        Returns:
            ExperimentResults with all data collected
        """
        print(f"\n=== Starting Deliberation Experiment ===")
        print(f"Experiment ID: {self.config.experiment_id}")
        print(f"Agents: {self.config.num_agents}")
        print(f"Decision Rule: {self.config.decision_rule}")
        print(f"Max Rounds: {self.config.max_rounds}")
        
        self.start_time = datetime.now()
        
        with trace(f"Deliberation Experiment {self.config.experiment_id}"):
            try:
                # Phase 1: Initialize agents
                await self._initialize_agents()
                
                # Phase 2: Initial individual evaluation
                await self._initial_evaluation()
                
                # Phase 3: Multi-round deliberation
                consensus_result = await self._run_deliberation_rounds()
                
                # Phase 4: Post-experiment feedback collection
                await self._collect_feedback(consensus_result)
                
                # Phase 5: Finalize results
                results = await self._finalize_results(consensus_result)
                
                print(f"\n=== Experiment Complete ===")
                print(f"Consensus reached: {consensus_result.unanimous}")
                if consensus_result.unanimous:
                    principle = get_principle_by_id(consensus_result.agreed_principle.principle_id)
                    print(f"Agreed principle: {principle['name']}")
                print(f"Total rounds: {consensus_result.rounds_to_consensus}")
                
                # Phase 6: Export data in multiple formats
                exported_files = export_experiment_data(results)
                print(f"\n--- Data Export Complete ---")
                for format_name, filepath in exported_files.items():
                    print(f"  {format_name}: {filepath}")
                
                return results
                
            except Exception as e:
                print(f"Error during experiment: {e}")
                self.performance_metrics.errors_encountered += 1
                raise
    
    async def _initialize_agents(self):
        """Initialize all deliberation agents."""
        print("\n--- Initializing Agents ---")
        
        self.agents = create_deliberation_agents(
            num_agents=self.config.num_agents,
            models=self.config.models,
            personalities=self.config.personalities
        )
        
        print(f"Created {len(self.agents)} deliberation agents")
        for agent in self.agents:
            print(f"  - {agent.name} ({agent.agent_id})")
            # Initialize memory for each agent
            agent_memory = AgentMemory(agent_id=agent.agent_id)
            self.agent_memories.append(agent_memory)
    
    async def _initial_evaluation(self):
        """Have each agent individually evaluate the principles - sequential process."""
        print("\n--- Initial Individual Evaluation ---")
        
        # Generate speaking order for initial evaluation
        speaking_order = self._generate_speaking_order(0)
        self.speaking_orders.append(speaking_order)
        print(f"  Speaking order: {[self._get_agent_name(agent_id) for agent_id in speaking_order]}")
        
        with trace("Initial Individual Evaluation"):
            for position, agent_id in enumerate(speaking_order, 1):
                agent = self._get_agent_by_id(agent_id)
                print(f"\n  --- {agent.name} (Position {position}) ---")
                
                # Initial evaluation doesn't need memory update (no previous context)
                # Just get their initial assessment
                evaluation_prompt = f"""
{get_all_principles_text()}

Please carefully evaluate each of these four principles of distributive justice.

Consider that:
- You are behind a 'veil of ignorance' - you don't know your future economic position
- Your position (wealthy, middle class, or poor) will be randomly assigned AFTER the group decides
- You should choose the principle that would be most fair and just for society as a whole

After your evaluation, please:
1. State which principle you choose (1, 2, 3, or 4)
2. Explain your reasoning clearly

Format your response clearly with your final choice at the end.
"""
                
                # Get agent's response
                result = await Runner.run(agent, evaluation_prompt)
                response_text = ItemHelpers.text_message_outputs(result.new_items)
                choice = await self._extract_principle_choice(response_text, agent.agent_id)
                
                agent.current_choice = choice
                print(f"    Chose Principle {choice.principle_id}")
                
                # Add to transcript
                self.transcript.append(DeliberationResponse(
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    public_message=response_text,
                    private_memory_entry=None,  # No memory for initial evaluation
                    updated_choice=choice,
                    round_number=0,  # Round 0 for initial evaluation
                    timestamp=datetime.now(),
                    speaking_position=position
                ))
        
        # Check if already unanimous after initial evaluation
        initial_consensus = await self._check_consensus()
        if initial_consensus.unanimous:
            print(f"  ✓ Unanimous agreement reached in initial evaluation!")
            return initial_consensus
        
        print(f"  Initial choices: {[agent.current_choice.principle_id for agent in self.agents]}")
        return None
    
    async def _run_deliberation_rounds(self) -> ConsensusResult:
        """Run multiple rounds of sequential deliberation until consensus or timeout."""
        print("\n--- Starting Multi-Round Deliberation ---")
        
        consensus_result = None
        
        for round_num in range(1, self.config.max_rounds + 1):
            print(f"\n--- Round {round_num} ---")
            self.current_round = round_num
            round_start_time = time.time()
            
            with trace(f"Deliberation Round {round_num}"):
                # Generate speaking order for this round
                speaking_order = self._generate_speaking_order(round_num)
                self.speaking_orders.append(speaking_order)
                print(f"  Speaking order: {[self._get_agent_name(agent_id) for agent_id in speaking_order]}")
                
                # Run sequential deliberation round
                await self._run_single_round_sequential(round_num, speaking_order)
                
                # Check for consensus after round
                consensus_result = await self._check_consensus()
                
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
    
    async def _run_single_round_sequential(self, round_number: int, speaking_order: List[str]):
        """Run a single round of sequential deliberation with memory updates."""
        
        for position, agent_id in enumerate(speaking_order, 1):
            agent = self._get_agent_by_id(agent_id)
            print(f"    {agent.name} (Position {position})")
            
            # 1. Private Memory Update: Agent analyzes situation and develops strategy
            private_memory_entry = await self._update_agent_memory(agent, round_number, position)
            
            # 2. Public Communication: Agent speaks to the group based on their strategy
            public_message = await self._generate_public_communication(agent, round_number)
            
            # 3. Extract Choice: Determine agent's current principle choice
            updated_choice = await self._extract_principle_choice(public_message, agent.agent_id)
            agent.current_choice = updated_choice
            
            # 4. Record in Transcript: Store both private and public information
            self.transcript.append(DeliberationResponse(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                public_message=public_message,
                private_memory_entry=private_memory_entry,
                updated_choice=updated_choice,
                round_number=round_number,
                timestamp=datetime.now(),
                speaking_position=position
            ))
            
            print(f"      Chose Principle {updated_choice.principle_id}")
            print(f"      Strategy: {private_memory_entry.strategy_update[:100]}...")
    
    async def _generate_discussion_prompt(self, round_num: int) -> str:
        """Generate discussion prompt for a specific round."""
        
        if round_num == 1:
            return f"""
Now let's discuss these principles as a group. You need to reach UNANIMOUS agreement on one principle.

Current situation:
- Each agent has made their initial choice
- You can see different perspectives in the group
- Remember: if you don't reach unanimous agreement, everyone gets a poor outcome

{get_all_principles_text()}

Please:
1. Share your thoughts on the different principles
2. Respond to other agents' perspectives
3. Explain what concerns you about other principles
4. Work toward finding common ground
5. State your current choice at the end

Remember: you're all behind the veil of ignorance - focus on what would be fair for society as a whole.
"""
        else:
            return f"""
This is round {round_num} of deliberation. You still need to reach UNANIMOUS agreement.

{get_all_principles_text()}

Please:
1. Consider the arguments made by other agents in previous rounds
2. Address specific concerns that have been raised
3. Explain if and why you might change your position
4. Work toward finding a solution everyone can accept
5. State your current choice at the end

Remember: unanimous agreement is required, and time is running out.
"""
    
    async def _create_personalized_prompt(self, agent: DeliberationAgent, base_prompt: str) -> str:
        """Create a personalized prompt including conversation history."""
        
        # Get recent conversation history (last 2 rounds)
        recent_history = []
        for response in self.transcript[-10:]:  # Last 10 messages
            if response.agent_id != agent.agent_id:  # Don't include own messages
                recent_history.append(f"{response.agent_name}: {response.message[:200]}...")
        
        history_text = "\n".join(recent_history) if recent_history else "No previous discussion yet."
        
        personalized_prompt = f"""
{base_prompt}

Recent discussion history:
{history_text}

Your current choice: Principle {agent.current_choice.principle_id if agent.current_choice else 'None'}

Please respond to the discussion and state your current choice.
"""
        
        return personalized_prompt
    
    async def _extract_principle_choice(self, response_text: str, agent_id: str) -> PrincipleChoice:
        """Extract principle choice from agent response using the judge."""
        
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
        
        judge_result = await Runner.run(self.moderator, extraction_prompt)
        choice_text = ItemHelpers.text_message_outputs(judge_result.new_items).strip()
        
        # Extract principle ID
        principle_id = 1  # Default
        for char in choice_text:
            if char.isdigit() and 1 <= int(char) <= 4:
                principle_id = int(char)
                break
        
        principle_info = get_principle_by_id(principle_id)
        
        return PrincipleChoice(
            principle_id=principle_id,
            principle_name=principle_info["name"],
            reasoning=response_text[:500]  # Truncate for storage
        )
    
    def _generate_speaking_order(self, round_number: int) -> List[str]:
        """
        Generate random speaking order with constraint: 
        last speaker in round N cannot be first in round N+1.
        """
        agent_ids = [agent.agent_id for agent in self.agents]
        
        # For first round or initial evaluation, any order is fine
        if round_number <= 1 or not self.speaking_orders:
            random.shuffle(agent_ids)
            return agent_ids
        
        # Get last speaker from previous round
        previous_order = self.speaking_orders[-1]
        last_speaker = previous_order[-1] if previous_order else None
        
        # Try to generate valid order (last speaker not first)
        for attempt in range(10):
            random.shuffle(agent_ids)
            if last_speaker is None or agent_ids[0] != last_speaker:
                return agent_ids
        
        # Fallback: if can't generate valid order after 10 attempts, 
        # allow consecutive speaking (as per requirement)
        print(f"  ⚠️  Could not avoid consecutive speaking for {last_speaker}")
        return agent_ids
    
    def _get_agent_by_id(self, agent_id: str) -> DeliberationAgent:
        """Get agent by ID."""
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        raise ValueError(f"Agent with ID {agent_id} not found")
    
    def _get_agent_name(self, agent_id: str) -> str:
        """Get agent name by ID."""
        return self._get_agent_by_id(agent_id).name
    
    def _get_agent_memory(self, agent_id: str) -> AgentMemory:
        """Get agent memory by ID."""
        for memory in self.agent_memories:
            if memory.agent_id == agent_id:
                return memory
        raise ValueError(f"Memory for agent {agent_id} not found")
    
    async def _check_consensus(self) -> ConsensusResult:
        """Check if unanimous consensus has been reached using code-based detection."""
        
        # Use the new code-based consensus detection
        return detect_consensus(self.transcript)
    
    async def _update_agent_memory(self, agent: DeliberationAgent, round_number: int, speaking_position: int) -> MemoryEntry:
        """Update an agent's private memory before they speak."""
        agent_memory = self._get_agent_memory(agent.agent_id)
        
        # Get conversation history for memory update
        memory_context = self._build_memory_context(agent.agent_id, round_number)
        
        memory_prompt = f"""You are about to speak in round {round_number} of a deliberation about distributive justice principles.

PRIVATE MEMORY UPDATE - This is your internal analysis, not shared with others.

Based on everything that has happened so far, please provide:

1. SITUATION ASSESSMENT: What is the current state of the deliberation? Who is agreeing/disagreeing on what?

2. OTHER AGENTS ANALYSIS: What do you think about the other agents' positions, motivations, and strategies? Who might be persuaded?

3. STRATEGY UPDATE: What should your strategy be for this round? How can you work toward consensus while advancing your goals?

{memory_context}

Please structure your response as:
SITUATION: [your assessment]
AGENTS: [your analysis of others]  
STRATEGY: [your updated strategy]
"""
        
        # Get private memory update
        memory_result = await Runner.run(agent, memory_prompt)
        memory_text = ItemHelpers.text_message_outputs(memory_result.new_items)
        
        # Parse the memory response (simplified parsing)
        situation = self._extract_section(memory_text, "SITUATION:")
        agents_analysis = self._extract_section(memory_text, "AGENTS:")
        strategy = self._extract_section(memory_text, "STRATEGY:")
        
        # Create memory entry
        memory_entry = MemoryEntry(
            round_number=round_number,
            timestamp=datetime.now(),
            situation_assessment=situation,
            other_agents_analysis=agents_analysis,
            strategy_update=strategy,
            speaking_position=speaking_position
        )
        
        # Add to agent's memory
        agent_memory.add_memory(memory_entry)
        
        return memory_entry
    
    def _build_memory_context(self, agent_id: str, round_number: int) -> str:
        """Build context for memory update including conversation history."""
        context_parts = []
        
        # Add previous rounds summary
        if self.transcript:
            context_parts.append("PREVIOUS CONVERSATION:")
            
            # Get previous rounds (not current round)
            previous_responses = [r for r in self.transcript if r.round_number < round_number]
            for response in previous_responses[-10:]:  # Last 10 messages
                context_parts.append(f"Round {response.round_number} - {response.agent_name}: {response.public_message[:200]}...")
        
        # Add current round so far (speakers before this agent)
        current_round_responses = [r for r in self.transcript if r.round_number == round_number]
        if current_round_responses:
            context_parts.append(f"\nCURRENT ROUND {round_number} SO FAR:")
            for response in current_round_responses:
                context_parts.append(f"{response.agent_name}: {response.public_message[:200]}...")
        
        # Add agent's own memory
        agent_memory = self._get_agent_memory(agent_id)
        if agent_memory.memory_entries:
            context_parts.append(f"\nYOUR PREVIOUS MEMORY:")
            for entry in agent_memory.memory_entries[-3:]:  # Last 3 memory entries
                context_parts.append(f"Round {entry.round_number} Strategy: {entry.strategy_update[:100]}...")
        
        return "\n".join(context_parts)
    
    def _extract_section(self, text: str, section_header: str) -> str:
        """Extract a section from structured text."""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            if line.strip().startswith(section_header):
                in_section = True
                section_lines.append(line.replace(section_header, '').strip())
            elif in_section and line.strip().startswith(('SITUATION:', 'AGENTS:', 'STRATEGY:')):
                break
            elif in_section:
                section_lines.append(line.strip())
        
        return '\n'.join(section_lines).strip() or "No analysis provided"
    
    async def _generate_public_communication(self, agent: DeliberationAgent, round_number: int) -> str:
        """Generate agent's public communication based on their memory."""
        agent_memory = self._get_agent_memory(agent.agent_id)
        latest_memory = agent_memory.get_latest_memory()
        
        # Build context for public communication
        public_context = self._build_public_context(agent.agent_id, round_number)
        
        communication_prompt = f"""Now it's your turn to speak publicly to the other agents in round {round_number}.

Based on your private analysis:
STRATEGY: {latest_memory.strategy_update if latest_memory else 'No strategy defined'}

{public_context}

Please communicate with the other agents. Your goals:
1. Work toward reaching unanimous agreement
2. Present compelling arguments for your position
3. Respond to others' concerns and proposals
4. Be persuasive but respectful

What do you want to say to the group? End with your current principle choice (1, 2, 3, or 4).
"""
        
        # Get public communication
        comm_result = await Runner.run(agent, communication_prompt)
        return ItemHelpers.text_message_outputs(comm_result.new_items)
    
    def _build_public_context(self, agent_id: str, round_number: int) -> str:
        """Build context for public communication."""
        context_parts = []
        
        # Current round speakers so far
        current_round_responses = [r for r in self.transcript if r.round_number == round_number]
        if current_round_responses:
            context_parts.append(f"SPEAKERS IN THIS ROUND SO FAR:")
            for response in current_round_responses:
                context_parts.append(f"{response.agent_name}: {response.public_message[:300]}...")
        
        # Agent's current choice
        agent = self._get_agent_by_id(agent_id)
        if agent.current_choice:
            context_parts.append(f"\nYour current choice: Principle {agent.current_choice.principle_id}")
        
        return "\n".join(context_parts)
    
    async def _collect_feedback(self, consensus_result: ConsensusResult):
        """Collect post-experiment feedback from all agents."""
        print("\n--- Post-Experiment Feedback Collection ---")
        
        if not consensus_result.unanimous:
            print("  No consensus reached - collecting feedback on experience")
        else:
            principle = get_principle_by_id(consensus_result.agreed_principle.principle_id)
            print(f"  Consensus reached on Principle {consensus_result.agreed_principle.principle_id}: {principle['name']}")
        
        # Prepare context for feedback
        experiment_summary = await self._generate_experiment_summary(consensus_result)
        
        # Collect feedback from each agent individually
        feedback_tasks = []
        for agent in self.agents:
            task = self._collect_individual_feedback(agent, experiment_summary, consensus_result)
            feedback_tasks.append(task)
        
        # Run feedback collection in parallel
        with trace("Feedback Collection"):
            feedback_results = await asyncio.gather(*feedback_tasks)
            
            for agent, feedback in zip(self.agents, feedback_results):
                if feedback:
                    self.feedback_responses.append(feedback)
                    print(f"  {agent.name}: Satisfaction {feedback.satisfaction_rating}/10, Fairness {feedback.fairness_rating}/10")
                else:
                    print(f"  {agent.name}: Feedback collection failed")
    
    async def _generate_experiment_summary(self, consensus_result: ConsensusResult) -> str:
        """Generate a summary of the experiment for feedback context."""
        
        if consensus_result.unanimous:
            principle = get_principle_by_id(consensus_result.agreed_principle.principle_id)
            outcome = f"The group reached unanimous agreement on Principle {consensus_result.agreed_principle.principle_id}: {principle['name']}"
        else:
            choices = [agent.current_choice.principle_id for agent in self.agents]
            choice_counts = {}
            for choice in choices:
                choice_counts[choice] = choice_counts.get(choice, 0) + 1
            
            outcome = "The group did not reach unanimous agreement. "
            for principle_id, count in sorted(choice_counts.items()):
                principle = get_principle_by_id(principle_id)
                outcome += f"{count} agents chose Principle {principle_id} ({principle['short_name']}). "
        
        summary = f"""
Experiment Summary:
- Duration: {consensus_result.rounds_to_consensus} rounds
- Total messages: {consensus_result.total_messages}
- Outcome: {outcome}

The four principles that were considered:
{get_all_principles_text()}
"""
        return summary
    
    async def _collect_individual_feedback(self, agent: DeliberationAgent, experiment_summary: str, consensus_result: ConsensusResult) -> Optional[FeedbackResponse]:
        """Collect feedback from a single agent."""
        
        try:
            # Create personalized interview prompt
            interview_prompt = f"""
You are conducting a post-experiment interview with {agent.name}.

{experiment_summary}

{agent.name}'s choice evolution during the experiment:
"""
            
            # Add agent's choice history
            agent_responses = [r for r in self.transcript if r.agent_id == agent.agent_id]
            for response in agent_responses:
                round_name = "Initial evaluation" if response.round_number == 0 else f"Round {response.round_number}"
                principle = get_principle_by_id(response.updated_choice.principle_id)
                interview_prompt += f"- {round_name}: Chose Principle {response.updated_choice.principle_id} ({principle['short_name']})\n"
            
            interview_prompt += f"""

Please conduct an interview with {agent.name} to collect their feedback about the experiment.

Ask them to:
1. Rate their satisfaction with the group's decision (1-10 scale)
2. Rate the fairness of the chosen principle (1-10 scale)  
3. Say whether they would choose the same principle again (yes/no)
4. Mention any alternative principle they might prefer
5. Explain their reasoning for their responses
6. Rate their confidence in their feedback (0-100%)

Please be thorough but concise in your interview.
"""
            
            # Conduct the interview
            interview_result = await Runner.run(self.feedback_collector, interview_prompt)
            interview_text = ItemHelpers.text_message_outputs(interview_result.new_items)
            
            # Extract feedback data from the interview
            feedback = await self._extract_feedback_data(interview_text, agent)
            
            return feedback
            
        except Exception as e:
            print(f"    Error collecting feedback from {agent.name}: {e}")
            return None
    
    async def _extract_feedback_data(self, interview_text: str, agent: DeliberationAgent) -> FeedbackResponse:
        """Extract structured feedback data from interview text."""
        
        extraction_prompt = f"""
Extract structured feedback data from this interview:

{interview_text}

Please extract and provide:
1. Satisfaction rating (1-10): [extract the number]
2. Fairness rating (1-10): [extract the number] 
3. Would choose again (true/false): [extract yes/no and convert to true/false]
4. Alternative preference (1-4 or null): [extract any alternative principle number, or null if none]
5. Reasoning: [extract the reasoning explanation]
6. Confidence (0.0-1.0): [extract confidence percentage and convert to decimal]

Format your response as:
Satisfaction: [number]
Fairness: [number]
Would choose again: [true/false]
Alternative preference: [number or null]
Reasoning: [text]
Confidence: [decimal]
"""
        
        extraction_result = await Runner.run(self.moderator, extraction_prompt)
        extraction_text = ItemHelpers.text_message_outputs(extraction_result.new_items)
        
        # Parse the extracted data (simple parsing)
        satisfaction = 7  # Default values
        fairness = 7
        would_choose_again = True
        alternative_preference = None
        reasoning = interview_text[:500]  # Fallback
        confidence = 0.7
        
        # Extract values from the response
        lines = extraction_text.split('\n')
        for line in lines:
            line = line.strip().lower()
            if line.startswith('satisfaction:'):
                try:
                    satisfaction = int(''.join(c for c in line if c.isdigit())[:2])
                    satisfaction = max(1, min(10, satisfaction))
                except:
                    pass
            elif line.startswith('fairness:'):
                try:
                    fairness = int(''.join(c for c in line if c.isdigit())[:2])
                    fairness = max(1, min(10, fairness))
                except:
                    pass
            elif line.startswith('would choose again:'):
                would_choose_again = 'true' in line or 'yes' in line
            elif line.startswith('alternative preference:'):
                try:
                    if 'null' not in line and 'none' not in line:
                        alt_num = int(''.join(c for c in line if c.isdigit())[:1])
                        if 1 <= alt_num <= 4:
                            alternative_preference = alt_num
                except:
                    pass
            elif line.startswith('confidence:'):
                try:
                    conf_str = ''.join(c for c in line if c.isdigit() or c == '.')
                    confidence = float(conf_str)
                    if confidence > 1.0:  # Assume it's a percentage
                        confidence = confidence / 100.0
                    confidence = max(0.0, min(1.0, confidence))
                except:
                    pass
            elif line.startswith('reasoning:'):
                reasoning = line.replace('reasoning:', '').strip()
        
        return FeedbackResponse(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            satisfaction_rating=satisfaction,
            fairness_rating=fairness,
            would_choose_again=would_choose_again,
            alternative_preference=alternative_preference,
            reasoning=reasoning,
            confidence_in_feedback=confidence,
            timestamp=datetime.now()
        )
    
    async def _finalize_results(self, consensus_result: ConsensusResult) -> ExperimentResults:
        """Finalize and package all experiment results."""
        
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate performance metrics
        self.performance_metrics.total_duration_seconds = total_duration
        self.performance_metrics.average_round_duration = (
            total_duration / max(1, self.current_round)
        )
        
        results = ExperimentResults(
            experiment_id=self.config.experiment_id,
            configuration=self.config,
            deliberation_transcript=self.transcript,
            agent_memories=self.agent_memories,
            speaking_orders=self.speaking_orders,
            consensus_result=consensus_result,
            feedback_responses=self.feedback_responses,
            performance_metrics=self.performance_metrics,
            start_time=self.start_time,
            end_time=end_time
        )
        
        return results


async def run_single_experiment(config: ExperimentConfig) -> ExperimentResults:
    """
    Run a single deliberation experiment with the given configuration.
    
    Args:
        config: Experiment configuration
        
    Returns:
        Complete experiment results
    """
    manager = DeliberationManager(config)
    return await manager.run_experiment()