"""
Multi-round deliberation engine for the distributive justice experiment.
Manages the conversation flow, consensus detection, and data collection.
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from agents import Runner, ItemHelpers, trace
from models import (
    DeliberationResponse, 
    ConsensusResult, 
    ExperimentConfig, 
    ExperimentResults,
    PerformanceMetrics,
    PrincipleChoice,
    FeedbackResponse,
    get_principle_by_id,
    get_all_principles_text
)
from agents_enhanced import (
    DeliberationAgent, 
    ConsensusJudge, 
    DiscussionModerator,
    FeedbackCollector,
    create_deliberation_agents,
    create_consensus_judge,
    create_discussion_moderator,
    create_feedback_collector
)
from data_export import export_experiment_data


class DeliberationManager:
    """
    Manages the complete deliberation process from initialization to consensus.
    """
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.agents: List[DeliberationAgent] = []
        self.consensus_judge: ConsensusJudge = create_consensus_judge()
        self.moderator: DiscussionModerator = create_discussion_moderator()
        self.feedback_collector: FeedbackCollector = create_feedback_collector()
        self.transcript: List[DeliberationResponse] = []
        self.feedback_responses: List[FeedbackResponse] = []
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
            models=self.config.models
        )
        
        print(f"Created {len(self.agents)} deliberation agents")
        for agent in self.agents:
            print(f"  - {agent.name} ({agent.agent_id})")
    
    async def _initial_evaluation(self):
        """Have each agent individually evaluate the principles."""
        print("\n--- Initial Individual Evaluation ---")
        
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
3. Rate your confidence in this choice (0-100%)

Format your response clearly with your final choice at the end.
"""
        
        # Run all agents in parallel for initial evaluation
        with trace("Initial Individual Evaluation"):
            tasks = []
            for agent in self.agents:
                task = Runner.run(agent, evaluation_prompt)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # Process results and extract choices
            for i, (agent, result) in enumerate(zip(self.agents, results)):
                response_text = ItemHelpers.text_message_outputs(result.new_items)
                choice = await self._extract_principle_choice(response_text, agent.agent_id)
                
                agent.current_choice = choice
                print(f"  {agent.name}: Chose Principle {choice.principle_id} ({choice.confidence:.1%} confidence)")
                
                # Add to transcript
                self.transcript.append(DeliberationResponse(
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    message=response_text,
                    updated_choice=choice,
                    round_number=0,  # Round 0 for initial evaluation
                    timestamp=datetime.now()
                ))
        
        # Check if already unanimous after initial evaluation
        initial_consensus = await self._check_consensus()
        if initial_consensus.unanimous:
            print(f"  ✓ Unanimous agreement reached in initial evaluation!")
            return initial_consensus
        
        print(f"  Initial choices: {[agent.current_choice.principle_id for agent in self.agents]}")
        return None
    
    async def _run_deliberation_rounds(self) -> ConsensusResult:
        """Run multiple rounds of deliberation until consensus or timeout."""
        print("\n--- Starting Multi-Round Deliberation ---")
        
        consensus_result = None
        
        for round_num in range(1, self.config.max_rounds + 1):
            print(f"\n--- Round {round_num} ---")
            self.current_round = round_num
            round_start_time = time.time()
            
            with trace(f"Deliberation Round {round_num}"):
                # Generate discussion prompt
                discussion_prompt = await self._generate_discussion_prompt(round_num)
                
                # Run deliberation round
                await self._run_single_round(discussion_prompt)
                
                # Check for consensus
                consensus_result = await self._check_consensus()
                
                round_duration = time.time() - round_start_time
                print(f"  Round {round_num} completed in {round_duration:.1f}s")
                
                if consensus_result.unanimous:
                    print(f"  ✓ Unanimous agreement reached!")
                    break
                else:
                    print(f"  Current choices: {[agent.current_choice.principle_id for agent in self.agents]}")
                    print(f"  Dissenting agents: {consensus_result.dissenting_agents}")
        
        if not consensus_result.unanimous:
            print(f"\n  ⚠️  No consensus reached after {self.config.max_rounds} rounds")
        
        return consensus_result
    
    async def _run_single_round(self, discussion_prompt: str):
        """Run a single round of deliberation."""
        
        # All agents discuss in parallel
        tasks = []
        for agent in self.agents:
            # Create personalized prompt including conversation history
            personalized_prompt = await self._create_personalized_prompt(agent, discussion_prompt)
            task = Runner.run(agent, personalized_prompt)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Process responses
        for agent, result in zip(self.agents, results):
            response_text = ItemHelpers.text_message_outputs(result.new_items)
            
            # Extract updated choice
            updated_choice = await self._extract_principle_choice(response_text, agent.agent_id)
            agent.current_choice = updated_choice
            
            # Add to transcript
            self.transcript.append(DeliberationResponse(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                message=response_text,
                updated_choice=updated_choice,
                round_number=self.current_round,
                timestamp=datetime.now()
            ))
            
            print(f"  {agent.name}: Chose Principle {updated_choice.principle_id}")
    
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
        
        judge_result = await Runner.run(self.consensus_judge, extraction_prompt)
        choice_text = ItemHelpers.text_message_outputs(judge_result.new_items).strip()
        
        # Extract principle ID
        principle_id = 1  # Default
        for char in choice_text:
            if char.isdigit() and 1 <= int(char) <= 4:
                principle_id = int(char)
                break
        
        principle_info = get_principle_by_id(principle_id)
        
        # Extract confidence (simple heuristic)
        confidence = 0.7  # Default confidence
        if "confident" in response_text.lower():
            confidence = 0.9
        elif "uncertain" in response_text.lower() or "unsure" in response_text.lower():
            confidence = 0.5
        
        return PrincipleChoice(
            principle_id=principle_id,
            principle_name=principle_info["name"],
            reasoning=response_text[:500],  # Truncate for storage
            confidence=confidence
        )
    
    async def _check_consensus(self) -> ConsensusResult:
        """Check if unanimous consensus has been reached."""
        
        if not self.agents or not all(agent.current_choice for agent in self.agents):
            return ConsensusResult(
                unanimous=False,
                dissenting_agents=[agent.agent_id for agent in self.agents if not agent.current_choice],
                rounds_to_consensus=self.current_round,
                total_messages=len(self.transcript)
            )
        
        # Get all choices
        choices = [agent.current_choice.principle_id for agent in self.agents]
        
        # Check if all are the same
        if len(set(choices)) == 1:
            # Unanimous!
            agreed_principle = self.agents[0].current_choice
            return ConsensusResult(
                unanimous=True,
                agreed_principle=agreed_principle,
                dissenting_agents=[],
                rounds_to_consensus=self.current_round,
                total_messages=len(self.transcript)
            )
        else:
            # Find dissenting agents
            most_common_choice = max(set(choices), key=choices.count)
            dissenting_agents = [
                agent.agent_id for agent in self.agents 
                if agent.current_choice.principle_id != most_common_choice
            ]
            
            return ConsensusResult(
                unanimous=False,
                dissenting_agents=dissenting_agents,
                rounds_to_consensus=self.current_round,
                total_messages=len(self.transcript)
            )
    
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
        
        extraction_result = await Runner.run(self.consensus_judge, extraction_prompt)
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