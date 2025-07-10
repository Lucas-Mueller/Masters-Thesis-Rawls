"""
Enhanced agent classes for the Multi-Agent Distributive Justice Experiment.
These agents have specialized roles and structured outputs.
"""

import os
from typing import Optional, List
from agents import Agent
from agents.extensions.models.litellm_model import LitellmModel
from ..core.models import PrincipleChoice, DeliberationResponse, ConsensusResult, FeedbackResponse, get_all_principles_text, get_default_personality
from datetime import datetime


class DeliberationAgent(Agent):
    """
    Enhanced agent for distributive justice deliberation.
    Includes structured output and specialized instructions.
    """
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 model: str = "gpt-4.1-mini",
                 personality: str = "You are an agent tasked to design a future society."):
        
        base_instructions = f"""
{personality}

You are participating in a deliberation about distributive justice principles.

{get_all_principles_text()}

Your task is to:
1. Carefully consider each principle and its implications
2. Engage in thoughtful discussion with other agents
3. Provide clear reasoning for your choices
4. Be open to changing your mind based on compelling arguments
5. Work toward reaching unanimous agreement with the group

Important context:
- You are behind a "veil of ignorance" - you don't know what economic position you'll have
- Your position (rich, middle class, poor) will be randomly assigned AFTER the group decides
- If the group cannot reach unanimous agreement, everyone gets a poor outcome
- Focus on what would be fair and just for society as a whole

Communication guidelines:
- Be respectful and constructive in your discussions
- Present logical arguments with clear reasoning
- Listen to others' perspectives carefully
- Be willing to compromise when appropriate
- Keep responses focused and concise
"""
        
        super().__init__(
            name=name,
            instructions=base_instructions,
            model=model
        )
        self.agent_id = agent_id
        self.current_choice: Optional[PrincipleChoice] = None
        self.round_history: List[str] = []


class ConsensusJudge(Agent):
    """
    Specialized agent for detecting unanimous agreement and analyzing consensus.
    """
    
    def __init__(self, model: str = "gpt-4.1"):
        instructions = f"""
You are a neutral judge analyzing whether a group of agents has reached unanimous agreement on a distributive justice principle.

{get_all_principles_text()}

Your task is to:
1. Review all agent responses from the current round
2. Determine if ALL agents have chosen the SAME principle
3. Identify any agents who have different choices
4. Provide a clear assessment of the consensus status

Rules for consensus:
- Unanimous agreement means ALL agents chose the exact same principle (1, 2, 3, or 4)
- Even if agents have similar reasoning, they must choose the same numbered principle
- If any agent is uncertain or mentions multiple principles, consensus is NOT reached
- Focus on the final principle choice, not just the reasoning

Output format:
- Clearly state whether unanimous agreement was reached (YES/NO)
- If YES, state which principle was unanimously chosen
- If NO, list which agents chose different principles
- Provide brief reasoning for your assessment
"""
        
        super().__init__(
            name="Consensus Judge",
            instructions=instructions,
            model=model
        )


class DiscussionModerator(Agent):
    """
    Moderator agent for managing deliberation rounds and keeping discussions focused.
    """
    
    def __init__(self, model: str = "gpt-4.1-mini"):
        instructions = f"""
You are a discussion moderator for a distributive justice deliberation.

{get_all_principles_text()}

Your role is to:
1. Summarize the current state of the discussion
2. Identify key points of agreement and disagreement
3. Guide the conversation toward consensus
4. Ensure all agents have had a chance to express their views
5. Keep discussions focused and productive

Guidelines:
- Remain neutral and don't advocate for any particular principle
- Encourage agents to address each other's specific concerns
- Help clarify misunderstandings about the principles
- Suggest areas where compromise might be possible
- Keep the discussion moving toward resolution

Communication style:
- Be clear and concise
- Ask focused questions to clarify positions
- Summarize complex discussions in simple terms
- Encourage respectful dialogue
- Remind agents of their shared goal of reaching agreement
"""
        
        super().__init__(
            name="Discussion Moderator",
            instructions=instructions,
            model=model
        )


def create_deliberation_agents(num_agents: int, models: Optional[List[str]] = None, personalities: Optional[List[str]] = None) -> List[DeliberationAgent]:
    """
    Create a list of deliberation agents with diverse model configurations.
    
    Args:
        num_agents: Number of agents to create
        models: Optional list of model names to use
    
    Returns:
        List of DeliberationAgent instances
    """
    
    # Default models if none provided
    if not models:
        models = ["gpt-4.1-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1"]
    
    agents = []
    
    # Get API keys
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    
    for i in range(num_agents):
        agent_id = f"agent_{i+1}"
        agent_name = f"Agent {i+1}"
        
        # Cycle through available models
        model_name = models[i % len(models)]
        
        # Create agent with appropriate model
        if "anthropic" in model_name.lower() or "claude" or "claude-sonnet-4" in model_name.lower():
            if anthropic_key:
                model = LitellmModel(model="anthropic/claude-sonnet-4-20250514", api_key=anthropic_key)
            else:
                model = "gpt-4.1-mini"  # Fallback
        elif "deepseek" in model_name.lower():
            if deepseek_key:
                model = LitellmModel(model="deepseek/deepseek-chat", api_key=deepseek_key)
            else:
                model = "gpt-4.1-mini"  # Fallback
        else:
            model = model_name
        
        # Use provided personality or default
        if personalities and i < len(personalities):
            personality = personalities[i]
        else:
            from ..core.models import get_default_personality
            personality = get_default_personality()
        
        agent = DeliberationAgent(
            agent_id=agent_id,
            name=agent_name,
            model=model,
            personality=personality
        )
        
        agents.append(agent)
    
    return agents


def create_consensus_judge() -> ConsensusJudge:
    """Create a consensus judge agent."""
    return ConsensusJudge()


class FeedbackCollector(Agent):
    """
    Specialized agent for collecting post-experiment feedback from participants.
    """
    
    def __init__(self, model: str = "gpt-4.1-mini"):
        instructions = f"""
You are a neutral interviewer collecting feedback from agents who just completed a distributive justice deliberation.

{get_all_principles_text()}

Your task is to conduct individual interviews with each agent to understand:
1. Their satisfaction with the group's final decision
2. Their assessment of the fairness of the chosen principle  
3. Whether they would make the same choice if they could do it again
4. Any alternative preferences they might have
5. Their reasoning for their feedback

Guidelines for feedback collection:
- Ask specific, clear questions
- Encourage honest and detailed responses
- Remain neutral and non-judgmental
- Probe for deeper reasoning when appropriate
- Help agents reflect on their experience

Interview structure:
1. Ask about satisfaction with the group decision (rate 1-10)
2. Ask about perceived fairness of the chosen principle (rate 1-10)
3. Ask if they would choose the same principle again (yes/no)
4. Ask about any alternative preferences
5. Ask for detailed reasoning about their responses

Be empathetic and professional in your approach.
"""
        
        super().__init__(
            name="Feedback Collector",
            instructions=instructions,
            model=model
        )


def create_discussion_moderator() -> DiscussionModerator:
    """Create a discussion moderator agent."""
    return DiscussionModerator()


def create_feedback_collector() -> FeedbackCollector:
    """Create a feedback collector agent."""
    return FeedbackCollector()