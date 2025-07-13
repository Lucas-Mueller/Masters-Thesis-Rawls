"""
Enhanced agent classes for the Multi-Agent Distributive Justice Experiment.
These agents have specialized roles and structured outputs.
"""

import os
from typing import Optional, List
from agents import Agent, trace
from agents.extensions.models.litellm_model import LitellmModel
from agents.model_settings import ModelSettings
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
                 personality: str = "You are an agent tasked to design a future society.",
                 model_settings: Optional[ModelSettings] = None):
        
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
            model=model,
            model_settings=model_settings
        )
        self.agent_id = agent_id
        self.current_choice: Optional[PrincipleChoice] = None
        self.round_history: List[str] = []



class DiscussionModerator(Agent):
    """
    Moderator agent for managing deliberation rounds and keeping discussions focused.
    """
    
    def __init__(self, model: str = "gpt-4.1-mini", model_settings: Optional[ModelSettings] = None):
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
            model=model,
            model_settings=model_settings
        )


def create_deliberation_agents(agent_configs: List, defaults, global_temperature: Optional[float] = None) -> List[DeliberationAgent]:
    """
    Create a list of deliberation agents from AgentConfig specifications.
    
    Args:
        agent_configs: List of AgentConfig instances
        defaults: DefaultConfig with fallback values
        global_temperature: Global temperature setting for all agents
    
    Returns:
        List of DeliberationAgent instances
    """
    from ..core.models import AgentConfig, DefaultConfig
    
    agents = []
    
    # Get API keys
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    xai_key = os.environ.get("XAI_API_KEY")
    groqkey = os.environ['GROQ_API_KEY']
    
    for i, agent_config in enumerate(agent_configs):
        agent_id = f"agent_{i+1}"
        agent_name = agent_config.name or f"Agent {i+1}"
        
        # Resolve model (use agent's model or default)
        model_name = agent_config.model or defaults.model
        
        # Create appropriate model wrapper for different providers
        if "claude-sonnet-4" in model_name.lower() or "claude" in model_name.lower():
            if anthropic_key:
                model = LitellmModel(model="anthropic/claude-sonnet-4-20250514", api_key=anthropic_key)
            else:
                model = model_name
        elif "claude-opus-4" in model_name.lower():
            if anthropic_key:
                model = LitellmModel(model="anthropic/claude-opus-4-20250514", api_key=anthropic_key)
                print("You are using Claude 4 Opus, this is super expensive")
            else:
                model = model_name
        elif "deepseek-chat" in model_name.lower():
            if deepseek_key:
                model = LitellmModel(model="deepseek/deepseek-chat", api_key=deepseek_key)
            else:
                model = model_name
        elif "deepseek-reasoner" in model_name.lower():
            if deepseek_key:
                model = LitellmModel(model="deepseek/deepseek-reasoner", api_key=deepseek_key)
            else:
                model = model_name
        elif "gemini-flash" in model_name.lower():
            if gemini_key:
                model = LitellmModel(model="gemini/gemini-2.5-flash-preview-04-17", api_key=gemini_key)
            else:
                model = model_name
        elif "gemini-pro" in model_name.lower():
            if gemini_key:
                model = LitellmModel(model="gemini/gemini-2.5-pro", api_key=gemini_key)
            else:
                model = model_name

        elif "grok-4" in model_name.lower():
            if xai_key:
                model = LitellmModel(model="xai/grok-4-0709", api_key=xai_key)
            else:
                model = model_name
    
        elif "grok-3" in model_name.lower() or "grok-3-mini" in model_name.lower():
            if xai_key:
                model = LitellmModel(model="xai/grok-3-mini", api_key=xai_key)
            else:
                model = model_name

        elif "llama-4" in model_name.lower() or "llama-4-scout" in model_name.lower():
            if groqkey:
                model = LitellmModel(model="groq/meta-llama/llama-4-scout-17b-16e-instruct", api_key=groqkey)
            else:
                model = model_name

        elif "llama-4-maverick" in model_name.lower():
            if groqkey:
                model = LitellmModel(model="groq/meta-llama/llama-4-maverick-17b-128e-instruct", api_key=groqkey)
            else:
                model = model_name
        
        elif "llama-3" in model_name.lower() or "llama-3-70B" in model_name.lower():
            if groqkey:
                model = LitellmModel(model="groq/llama-3.3-70b-versatile", api_key=groqkey)
            else:
                model = model_name
        
        # OpenAI models - explicit handling to ensure they're not caught by other conditions
        elif any(openai_pattern in model_name.lower() for openai_pattern in [
            "gpt-4", "gpt-3.5", "o1", "o3", "o4", "gpt-image", "sora"
        ]):
            # OpenAI models use the model name directly (no LitellmModel wrapper needed)
            model = model_name
        
        else:
            # Default fallback - assume it's an OpenAI model if not explicitly handled
            model = model_name
        
        # Model resolution complete
        
        # Resolve personality (use agent's personality or default)
        personality = agent_config.personality or defaults.personality
        
        # Determine temperature (priority: agent > default > global)
        temperature = (agent_config.temperature or 
                      defaults.temperature or 
                      global_temperature)
        
        # Always create ModelSettings (never None to avoid SDK errors)
        if temperature is not None:
            model_settings = ModelSettings(temperature=temperature)
        else:
            model_settings = ModelSettings()  # Empty but valid ModelSettings
        
        agent = DeliberationAgent(
            agent_id=agent_id,
            name=agent_name,
            model=model,
            personality=personality,
            model_settings=model_settings
        )
        
        agents.append(agent)
    
    return agents






class FeedbackCollector(Agent):
    """
    Specialized agent for collecting post-experiment feedback from participants.
    """
    
    def __init__(self, model: str = "gpt-4.1-mini", model_settings: Optional[ModelSettings] = None):
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
            model=model,
            model_settings=model_settings
        )


def create_discussion_moderator(model_settings: Optional[ModelSettings] = None) -> DiscussionModerator:
    """Create a discussion moderator agent."""
    # Ensure model_settings is never None to avoid SDK errors
    if model_settings is None:
        model_settings = ModelSettings()
    return DiscussionModerator(model_settings=model_settings)


def create_feedback_collector(model_settings: Optional[ModelSettings] = None) -> FeedbackCollector:
    """Create a feedback collector agent."""
    # Ensure model_settings is never None to avoid SDK errors
    if model_settings is None:
        model_settings = ModelSettings()
    return FeedbackCollector(model_settings=model_settings)