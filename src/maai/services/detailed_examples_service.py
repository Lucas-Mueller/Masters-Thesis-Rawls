"""
DetailedExamplesService for providing detailed examples of principle outcomes.
Implements the missing "Detailed Examples" step from new_logic.md.
"""

from typing import List
from agents import Runner
from ..agents.enhanced import DeliberationAgent
from .economics_service import EconomicsService


class DetailedExamplesService:
    """Service for providing detailed examples of principle outcomes."""
    
    def __init__(self, economics_service: EconomicsService):
        """
        Initialize the detailed examples service.
        
        Args:
            economics_service: Service for economic calculations and analysis
        """
        self.economics_service = economics_service
    
    async def present_detailed_examples(self, agents: List[DeliberationAgent]) -> None:
        """
        Present detailed examples to all agents showing principle outcome mappings.
        
        Args:
            agents: List of agents to present examples to
        """
        # 1. Generate complete analysis
        analysis = self.economics_service.analyze_all_principle_outcomes()
        
        # 2. Format for agent consumption
        examples_text = self._format_detailed_examples(analysis)
        
        # 3. Present to each agent
        for agent in agents:
            await self._present_examples_to_agent(agent, examples_text)
    
    def _format_detailed_examples(self, analysis: dict) -> str:
        """
        Format the analysis into human-readable examples text.
        Matches the exact format from new_logic.md.
        
        Args:
            analysis: Results from economics_service.analyze_all_principle_outcomes()
            
        Returns:
            Formatted examples text for agents
        """
        lines = []
        lines.append("Now you will see detailed examples of how each principle applies to the income distributions.")
        lines.append("")
        lines.append("For the current set of distributions, here are the outcome mappings:")
        lines.append("")
        
        # Principle 1
        p1_result = analysis["principle_1"] 
        lines.append(f"Maximizing the floor → {p1_result['selected_distribution'].name}")
        lines.append("")
        
        # Principle 2  
        p2_result = analysis["principle_2"]
        lines.append(f"Maximizing average → {p2_result['selected_distribution'].name}")
        lines.append("")
        
        # Principle 3 variations
        lines.append("Maximizing average with a floor constraint of:")
        for constraint, result in analysis["principle_3"].items():
            if result["selected_distribution"]:
                lines.append(f"  {constraint} → {result['selected_distribution'].name}")
            else:
                lines.append(f"  {constraint} → No valid distribution")
        lines.append("")
        
        # Principle 4 variations
        lines.append("Maximizing average with a range constraint of:")
        for constraint, result in analysis["principle_4"].items():
            if result["selected_distribution"]:
                lines.append(f"  {constraint} → {result['selected_distribution'].name}")
            else:
                lines.append(f"  {constraint} → No valid distribution")
        
        return "\n".join(lines)
    
    async def _present_examples_to_agent(self, agent: DeliberationAgent, examples_text: str) -> None:
        """
        Present examples to a single agent.
        
        Args:
            agent: Agent to present examples to
            examples_text: Formatted examples text
        """
        prompt = f"""You have now learned about the four distributive justice principles. 
Before you begin making choices, here are detailed examples showing how each principle would be applied:

{examples_text}

Please take time to understand these mappings. This shows you exactly which income distribution each principle would select from the available options, and how constraint values affect the outcomes for principles 3 and 4.

These examples will help you make informed decisions in the upcoming individual application rounds.

Please acknowledge that you understand these examples by briefly summarizing what you learned."""

        response = await Runner.run(agent, prompt)
        print(f"  {agent.name}: {response.data if hasattr(response, 'data') else str(response)}")