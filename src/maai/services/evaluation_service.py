"""
EvaluationService for conducting post-consensus principle evaluations.
Implements parallel evaluation using Likert scale ratings.
"""

import asyncio
import json
import time
import logging
from typing import List, Dict, Optional
from agents import Runner, ItemHelpers
from ..core.models import (
    AgentEvaluationResponse, 
    PrincipleEvaluation, 
    ConsensusResult, 
    DeliberationResponse, 
    LikertScale,
    get_all_principles_text,
    get_principle_name
)

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for conducting post-consensus principle evaluations."""
    
    def __init__(self, max_concurrent_evaluations: int = 10):
        """
        Initialize the evaluation service.
        
        Args:
            max_concurrent_evaluations: Maximum number of concurrent evaluations
        """
        self.max_concurrent_evaluations = max_concurrent_evaluations
        self.semaphore = asyncio.Semaphore(max_concurrent_evaluations)
    
    async def conduct_parallel_evaluation(
        self, 
        agents: List,  # List[DeliberationAgent] - avoiding circular import
        consensus_result: ConsensusResult,
        moderator_agent  # DeliberationAgent - for parsing responses
    ) -> List[AgentEvaluationResponse]:
        """
        Conduct parallel evaluation of all principles by all agents.
        
        Args:
            agents: List of agents to evaluate
            consensus_result: Result of the consensus process
            moderator_agent: Agent to use for parsing responses
            
        Returns:
            List of evaluation responses from all agents
        """
        logger.info(f"Starting parallel evaluation stage with {len(agents)} agents")
        
        # Create evaluation tasks for all agents
        evaluation_tasks = [
            self._evaluate_agent_principles(agent, consensus_result, moderator_agent)
            for agent in agents
        ]
        
        # Execute evaluations in parallel with proper error handling
        evaluation_responses = []
        results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Evaluation failed for agent {agents[i].agent_id}: {result}")
                # Create a fallback response
                evaluation_responses.append(self._create_fallback_response(agents[i]))
            else:
                evaluation_responses.append(result)
        
        logger.info(f"Completed evaluation stage - collected {len(evaluation_responses)} responses")
        return evaluation_responses
    
    async def conduct_initial_assessment(
        self,
        agents: List,  # List[DeliberationAgent]
        dummy_consensus: ConsensusResult,  # Not used, just for method signature compatibility
        moderator_agent  # DeliberationAgent
    ) -> List[AgentEvaluationResponse]:
        """
        Conduct initial Likert scale assessment (parallel).
        This is purely for data collection before any deliberation.
        
        Args:
            agents: List of agents to assess
            dummy_consensus: Unused (for signature compatibility)
            moderator_agent: Agent for parsing responses
            
        Returns:
            List of initial assessment responses
        """
        logger.info(f"Starting initial Likert assessment with {len(agents)} agents")
        
        # Create evaluation tasks for all agents
        assessment_tasks = [
            self._conduct_initial_agent_assessment(agent, moderator_agent)
            for agent in agents
        ]
        
        # Execute assessments in parallel with error handling
        assessment_responses = []
        results = await asyncio.gather(*assessment_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Initial assessment failed for agent {agents[i].agent_id}: {result}")
                # Create a fallback response
                assessment_responses.append(self._create_fallback_response(agents[i]))
            else:
                assessment_responses.append(result)
        
        logger.info(f"Completed initial assessment - collected {len(assessment_responses)} responses")
        return assessment_responses
    
    async def _conduct_initial_agent_assessment(
        self,
        agent,  # DeliberationAgent
        moderator_agent  # DeliberationAgent
    ) -> AgentEvaluationResponse:
        """
        Conduct initial assessment for a single agent.
        
        Args:
            agent: Agent to assess
            moderator_agent: Agent for parsing responses
            
        Returns:
            Initial assessment response
        """
        async with self.semaphore:  # Limit concurrent assessments
            try:
                assessment_prompt = self._create_initial_assessment_prompt()
                
                # Get agent's assessment response
                start_time = time.time()
                result = await Runner.run(agent, assessment_prompt)
                response_text = ItemHelpers.text_message_outputs(result.new_items)
                assessment_duration = time.time() - start_time
                
                # Parse response into structured format
                principle_evaluations = await self._parse_evaluation_response(
                    response_text, moderator_agent
                )
                
                return AgentEvaluationResponse(
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    principle_evaluations=principle_evaluations,
                    overall_reasoning=response_text,
                    evaluation_duration=assessment_duration
                )
                
            except Exception as e:
                logger.error(f"Error in initial assessment for agent {agent.agent_id}: {e}")
                return self._create_fallback_response(agent)
    
    def _create_initial_assessment_prompt(self) -> str:
        """
        Create prompt for initial Likert scale assessment.
        
        Returns:
            Formatted assessment prompt
        """
        prompt = f"""
Before any discussion begins, please evaluate each of the four distributive justice principles based on your initial thoughts and preferences.

{get_all_principles_text()}

For each principle, please provide your satisfaction rating using this 4-point scale:
- Strongly Disagree (1)
- Disagree (2) 
- Agree (3)
- Strongly Agree (4)

Please also provide your reasoning for each rating.

This is purely to understand your initial perspective before any group discussion.

Format your response EXACTLY as follows:

PRINCIPLE 1: [Strongly Disagree/Disagree/Agree/Strongly Agree]
REASONING 1: [Your reasoning]

PRINCIPLE 2: [Strongly Disagree/Disagree/Agree/Strongly Agree]
REASONING 2: [Your reasoning]

PRINCIPLE 3: [Strongly Disagree/Disagree/Agree/Strongly Agree]
REASONING 3: [Your reasoning]

PRINCIPLE 4: [Strongly Disagree/Disagree/Agree/Strongly Agree]
REASONING 4: [Your reasoning]

OVERALL REASONING: [Your overall thoughts on these principles]
"""
        return prompt
    
    async def _evaluate_agent_principles(
        self, 
        agent,  # DeliberationAgent
        consensus_result: ConsensusResult,
        moderator_agent  # DeliberationAgent
    ) -> AgentEvaluationResponse:
        """
        Evaluate all 4 principles for a single agent.
        
        Args:
            agent: Agent to conduct evaluation
            consensus_result: Result of the consensus process
            moderator_agent: Agent to use for parsing responses
            
        Returns:
            Complete evaluation response from the agent
        """
        async with self.semaphore:  # Limit concurrent evaluations
            try:
                evaluation_prompt = self._create_evaluation_prompt(consensus_result)
                
                # Get agent's evaluation response using OpenAI Agents SDK pattern
                start_time = time.time()
                result = await Runner.run(agent, evaluation_prompt)
                response_text = ItemHelpers.text_message_outputs(result.new_items)
                evaluation_duration = time.time() - start_time
                
                # Parse response into structured format
                principle_evaluations = await self._parse_evaluation_response(
                    response_text, moderator_agent
                )
                
                return AgentEvaluationResponse(
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    principle_evaluations=principle_evaluations,
                    overall_reasoning=response_text,
                    evaluation_duration=evaluation_duration
                )
                
            except Exception as e:
                logger.error(f"Error evaluating principles for agent {agent.agent_id}: {e}")
                return self._create_fallback_response(agent)
    
    def _create_evaluation_prompt(self, consensus_result: ConsensusResult) -> str:
        """
        Create evaluation prompt for post-consensus principle assessment.
        
        Args:
            consensus_result: Result of the consensus process
            
        Returns:
            Formatted evaluation prompt
        """
        agreed_principle = consensus_result.agreed_principle if consensus_result.unanimous else None
        
        consensus_text = (
            f"The group reached consensus on: {agreed_principle.principle_name}"
            if agreed_principle
            else "The group did not reach consensus"
        )
        
        prompt = f"""
{consensus_text}

Now, please evaluate each of the four distributive justice principles based on your experience in this experiment.

{get_all_principles_text()}

For each principle, please provide your satisfaction rating using this 4-point scale:
- Strongly Disagree (1)
- Disagree (2) 
- Agree (3)
- Strongly Agree (4)

Please also provide your reasoning for each rating.

Format your response EXACTLY as follows:

PRINCIPLE 1: [Strongly Disagree/Disagree/Agree/Strongly Agree]
REASONING 1: [Your reasoning]

PRINCIPLE 2: [Strongly Disagree/Disagree/Agree/Strongly Agree]
REASONING 2: [Your reasoning]

PRINCIPLE 3: [Strongly Disagree/Disagree/Agree/Strongly Agree]
REASONING 3: [Your reasoning]

PRINCIPLE 4: [Strongly Disagree/Disagree/Agree/Strongly Agree]
REASONING 4: [Your reasoning]

OVERALL REASONING: [Your overall thoughts on the evaluation process]
"""
        return prompt
    
    async def _parse_evaluation_response(
        self, 
        response_text: str, 
        moderator_agent  # DeliberationAgent
    ) -> List[PrincipleEvaluation]:
        """
        Parse agent response into structured principle evaluations.
        
        Args:
            response_text: Agent's response text to parse
            moderator_agent: Agent to use for parsing
            
        Returns:
            List of principle evaluations
        """
        try:
            # Use moderator agent to extract structured data
            parse_prompt = f"""
Please extract the principle evaluations from this agent response:

{response_text}

Extract the rating (Strongly Disagree, Disagree, Agree, or Strongly Agree) and reasoning for each of the 4 principles.

Format your response as valid JSON:
{{
    "principle_1": {{"rating": "agree", "reasoning": "..."}},
    "principle_2": {{"rating": "disagree", "reasoning": "..."}},
    "principle_3": {{"rating": "strongly_agree", "reasoning": "..."}},
    "principle_4": {{"rating": "strongly_disagree", "reasoning": "..."}}
}}

Use only these rating values: "strongly_disagree", "disagree", "agree", "strongly_agree"
"""
            
            # Use moderator agent to parse response
            result = await Runner.run(moderator_agent, parse_prompt)
            moderator_response_text = ItemHelpers.text_message_outputs(result.new_items)
            
            # Clean the response and validate before JSON parsing
            moderator_response_text = moderator_response_text.strip()
            if not moderator_response_text:
                logger.warning("Empty response from moderator, falling back to simple parsing")
                return self._fallback_parse_evaluation(response_text)
            
            # Try to extract JSON from the response if it's wrapped in other text
            json_start = moderator_response_text.find('{')
            json_end = moderator_response_text.rfind('}')
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_text = moderator_response_text[json_start:json_end + 1]
            else:
                logger.warning("No JSON found in moderator response, falling back to simple parsing")
                return self._fallback_parse_evaluation(response_text)
            
            # Parse JSON response and create PrincipleEvaluation objects
            parsed_data = json.loads(json_text)
            evaluations = []
            
            for i in range(1, 5):
                principle_key = f"principle_{i}"
                if principle_key in parsed_data:
                    rating_str = parsed_data[principle_key]["rating"].lower()
                    reasoning = parsed_data[principle_key]["reasoning"]
                    
                    # Map to LikertScale enum
                    rating = LikertScale(rating_str)
                    
                    evaluation = PrincipleEvaluation(
                        principle_id=i,
                        principle_name=get_principle_name(i),
                        satisfaction_rating=rating,
                        reasoning=reasoning
                    )
                    evaluations.append(evaluation)
            
            return evaluations
            
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.warning(f"JSON parsing failed, falling back to simple parsing: {e}")
            return self._fallback_parse_evaluation(response_text)
    
    def _fallback_parse_evaluation(self, response_text: str) -> List[PrincipleEvaluation]:
        """
        Fallback parsing when JSON parsing fails.
        
        Args:
            response_text: Raw response text to parse
            
        Returns:
            List of principle evaluations with default values
        """
        evaluations = []
        
        # Simple text parsing as fallback
        for i in range(1, 5):
            # Look for pattern: "PRINCIPLE {i}: [rating]"
            rating = LikertScale.AGREE  # Default to agree
            reasoning = "Parsed from agent response using fallback method"
            
            # Try to find the rating in the text
            principle_patterns = [
                f"PRINCIPLE {i}:",
                f"principle {i}:",
                f"Principle {i}:",
                f"{i}.",  # Sometimes agents just use numbers
            ]
            
            for pattern in principle_patterns:
                if pattern in response_text:
                    # Extract text after the pattern
                    start_idx = response_text.find(pattern)
                    if start_idx != -1:
                        # Get the next 200 characters or to next principle
                        next_principle_idx = response_text.find(f"PRINCIPLE {i+1}:", start_idx)
                        if next_principle_idx == -1:
                            next_principle_idx = start_idx + 200
                        
                        section_text = response_text[start_idx:next_principle_idx].lower()
                        
                        # Map text to rating with more specific patterns
                        if "strongly disagree" in section_text:
                            rating = LikertScale.STRONGLY_DISAGREE
                        elif "strongly agree" in section_text:
                            rating = LikertScale.STRONGLY_AGREE
                        elif "disagree" in section_text:
                            rating = LikertScale.DISAGREE
                        elif "agree" in section_text:
                            rating = LikertScale.AGREE
                        
                        # Try to extract reasoning from the section
                        reasoning_patterns = [
                            f"REASONING {i}:",
                            f"reasoning {i}:",
                            f"Reasoning {i}:",
                            "reasoning:",
                            "because",
                            "since"
                        ]
                        
                        for reasoning_pattern in reasoning_patterns:
                            if reasoning_pattern in section_text:
                                reasoning_start = section_text.find(reasoning_pattern)
                                if reasoning_start != -1:
                                    reasoning_text = section_text[reasoning_start + len(reasoning_pattern):].strip()
                                    # Get first sentence or up to 200 chars
                                    if reasoning_text:
                                        reasoning = reasoning_text[:200].strip()
                                        if reasoning.endswith('.'):
                                            reasoning = reasoning[:-1]
                                    break
                        
                        break
            
            evaluation = PrincipleEvaluation(
                principle_id=i,
                principle_name=get_principle_name(i),
                satisfaction_rating=rating,
                reasoning=reasoning if reasoning != "Parsed from agent response using fallback method" else f"Agent response indicated {rating.to_display().lower()} for principle {i}"
            )
            evaluations.append(evaluation)
        
        return evaluations
    
    def _create_fallback_response(self, agent) -> AgentEvaluationResponse:
        """
        Create a fallback response when evaluation fails.
        
        Args:
            agent: Agent that failed evaluation
            
        Returns:
            Fallback evaluation response
        """
        # Create neutral evaluations for all principles
        evaluations = []
        for i in range(1, 5):
            evaluation = PrincipleEvaluation(
                principle_id=i,
                principle_name=get_principle_name(i),
                satisfaction_rating=LikertScale.AGREE,  # Neutral default
                reasoning="Evaluation failed - using default neutral rating"
            )
            evaluations.append(evaluation)
        
        return AgentEvaluationResponse(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            principle_evaluations=evaluations,
            overall_reasoning="Evaluation process failed - using fallback response",
            evaluation_duration=0.0
        )