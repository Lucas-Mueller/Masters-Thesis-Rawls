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


def create_deliberation_agents(agent_configs: List, defaults) -> List[DeliberationAgent]:
    """
    Create a list of deliberation agents from AgentConfig specifications.
    
    Args:
        agent_configs: List of AgentConfig instances
        defaults: DefaultConfig with fallback values
    
    Returns:
        List of DeliberationAgent instances
    """
    from ..core.models import AgentConfig, DefaultConfig
    
    agents = []
    
    # Get API keys
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    
    for i, agent_config in enumerate(agent_configs):
        agent_id = f"agent_{i+1}"
        agent_name = agent_config.name or f"Agent {i+1}"
        
        # Resolve model (use agent's model or default)
        model_name = agent_config.model or defaults.model
        
        # Create appropriate model wrapper for different providers
        if "anthropic" in model_name.lower() or "claude" in model_name.lower():
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
        
        # Resolve personality (use agent's personality or default)
        personality = agent_config.personality or defaults.personality
        
        agent = DeliberationAgent(
            agent_id=agent_id,
            name=agent_name,
            model=model,
            personality=personality
        )
        
        agents.append(agent)
    
    return agents






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