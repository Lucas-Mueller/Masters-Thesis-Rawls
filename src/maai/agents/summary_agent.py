"""
Summary Agent for generating round summaries in multi-agent deliberation experiments.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core.models import DeliberationResponse, DISTRIBUTIVE_JUSTICE_PRINCIPLES
from agents import Agent
from agents.extensions.models.litellm_model import LitellmModel
from agents.model_settings import ModelSettings


class SummaryAgent(Agent):
    """
    Specialized agent for generating structured summaries of deliberation rounds.
    Uses lightweight model (GPT-4.1-mini) for efficient summarization.
    """
    
    def __init__(
        self, 
        model: str = "gpt-4.1-mini",
        temperature: float = 0.1,
        max_tokens: int = 1000
    ):
        """
        Initialize the summary agent.
        
        Args:
            model: LLM model to use for summarization
            temperature: Temperature for generation
            max_tokens: Maximum tokens for summaries
        """
        # Create model settings
        model_settings = ModelSettings(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Initialize the Agent with LitellmModel
        super().__init__(
            agent_id="summary_agent",
            model=LitellmModel(model_settings),
            instructions="You are a summary agent for multi-agent deliberation experiments. Generate concise, structured summaries of discussion rounds."
        )
    
    def _get_summary_prompt(self, round_number: int, round_responses: List[DeliberationResponse]) -> str:
        """
        Generate the prompt for round summarization.
        
        Args:
            round_number: Round number being summarized
            round_responses: All responses from the round
            
        Returns:
            Formatted prompt for summary generation
        """
        # Build the discussion text
        discussion_parts = []
        for response in sorted(round_responses, key=lambda x: x.speaking_position):
            discussion_parts.append(f"{response.agent_name}: {response.public_message}")
        
        discussion_text = "\n".join(discussion_parts)
        
        # Get principle definitions for context
        principles_context = ""
        for pid, principle in DISTRIBUTIVE_JUSTICE_PRINCIPLES.items():
            principles_context += f"Principle {pid}: {principle['name']} - {principle['description']}\n"
        
        prompt = f"""You are a summary agent for a multi-agent deliberation experiment about distributive justice principles.

CONTEXT:
The agents are deliberating on which distributive justice principle to adopt for a future society. They are behind a "veil of ignorance" and don't know their future economic position.

PRINCIPLES:
{principles_context}

ROUND {round_number} SUMMARY TASK:
Review the complete discussion below and create a structured summary focusing on decision-relevant information.

DISCUSSION:
{discussion_text}

REQUIRED OUTPUT FORMAT (respond with valid JSON):
{{
    "summary_text": "## Round {round_number} Summary\\n\\n### Key Arguments Presented:\\n- Agent_X: [main argument/position]\\n- Agent_Y: [main argument/position]\\n\\n### Principle Preferences:\\n- Principle 1: [agents supporting, key reasons]\\n- Principle 2: [agents supporting, key reasons]\\n- Principle 3: [agents supporting, key reasons]\\n- Principle 4: [agents supporting, key reasons]\\n\\n### Consensus Status:\\n- Current agreement level: [none/partial/unanimous]\\n- Main disagreement points: [if any]\\n\\n### Round Outcome:\\n- Principle choices made: [list]\\n- Key shifts in position: [if any]\\n- Next round implications: [strategic considerations]",
    "key_arguments": {{
        "Agent_1": "main argument or position",
        "Agent_2": "main argument or position"
    }},
    "principle_preferences": {{
        "Principle 1": ["Agent_X", "Agent_Y"],
        "Principle 2": ["Agent_Z"]
    }},
    "consensus_status": "Description of current consensus status and main disagreements"
}}

GUIDELINES:
- Keep summary concise but comprehensive
- Focus on decision-relevant information
- Extract key arguments and principle preferences accurately
- Identify consensus status and disagreement points
- Use agent names exactly as they appear in the discussion
- Only include principles that were actually discussed or chosen
- Be objective and neutral in tone"""
        
        return prompt
    
    async def generate_round_summary(
        self, 
        round_number: int, 
        round_responses: List[DeliberationResponse]
    ) -> Dict[str, Any]:
        """
        Generate a structured summary of a deliberation round.
        
        Args:
            round_number: Round number being summarized
            round_responses: All responses from the round
            
        Returns:
            Dictionary containing summary data
        """
        if not round_responses:
            return {
                "summary_text": f"## Round {round_number} Summary\\n\\nNo discussion occurred in this round.",
                "key_arguments": {},
                "principle_preferences": {},
                "consensus_status": "No activity in this round"
            }
        
        # Generate summary prompt
        prompt = self._get_summary_prompt(round_number, round_responses)
        
        # Get summary from LLM
        try:
            response = await self.run(prompt)
            
            # Parse JSON response
            import json
            summary_data = json.loads(response.text)
            
            # Validate required fields
            required_fields = ["summary_text", "key_arguments", "principle_preferences", "consensus_status"]
            for field in required_fields:
                if field not in summary_data:
                    raise ValueError(f"Missing required field: {field}")
            
            return summary_data
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback to basic summary if JSON parsing fails
            return {
                "summary_text": f"## Round {round_number} Summary\\n\\nRound {round_number} involved {len(round_responses)} agents discussing distributive justice principles. Summary generation encountered an error: {str(e)}",
                "key_arguments": {response.agent_name: "Position discussed" for response in round_responses},
                "principle_preferences": {},
                "consensus_status": f"Summary generation failed: {str(e)}"
            }
    
    async def generate_experiment_summary(
        self, 
        all_round_summaries: List[Dict[str, Any]],
        final_consensus: Optional[str] = None
    ) -> str:
        """
        Generate a high-level summary of the entire experiment.
        
        Args:
            all_round_summaries: List of all round summaries
            final_consensus: Final consensus result if any
            
        Returns:
            Formatted experiment summary
        """
        if not all_round_summaries:
            return "No rounds were completed in this experiment."
        
        # Build experiment summary prompt
        summaries_text = "\n\n".join([
            f"Round {i+1}: {summary['summary_text']}" 
            for i, summary in enumerate(all_round_summaries)
        ])
        
        prompt = f"""Generate a concise experiment summary based on these round summaries:

{summaries_text}

Final Consensus: {final_consensus or 'No consensus reached'}

Provide a 2-3 paragraph summary focusing on:
1. Overall deliberation trajectory
2. Key turning points or arguments
3. Final outcome and consensus process"""
        
        try:
            response = await self.run(prompt)
            return response.text
        except Exception as e:
            return f"Experiment involved {len(all_round_summaries)} rounds of deliberation. Final consensus: {final_consensus or 'None reached'}. Summary generation failed: {str(e)}"