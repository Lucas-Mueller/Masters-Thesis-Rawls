"""
MemoryService for centralized agent memory management.
Handles memory strategies, updates, and retrieval for all agents.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
from agents import Runner, ItemHelpers
from ..core.models import AgentMemory, MemoryEntry, DeliberationResponse
from ..agents.enhanced import DeliberationAgent


class MemoryStrategy(ABC):
    """Abstract base class for memory management strategies."""
    
    @abstractmethod
    def should_include_memory(self, memory_entry: MemoryEntry, current_round: int) -> bool:
        """
        Determine if a memory entry should be included in context.
        
        Args:
            memory_entry: Memory entry to evaluate
            current_round: Current round number
            
        Returns:
            True if memory should be included, False otherwise
        """
        pass
    
    @abstractmethod
    def get_memory_context_limit(self) -> int:
        """Get the maximum number of memory entries to include."""
        pass
    
    async def generate_memory_entry(self, agent: DeliberationAgent, round_number: int, 
                                   speaking_position: int, transcript: List[DeliberationResponse],
                                   memory_context: str) -> MemoryEntry:
        """
        Generate a memory entry for the agent. Default implementation uses the original single-prompt approach.
        Subclasses can override this to implement different memory generation strategies.
        
        Args:
            agent: Agent to generate memory for
            round_number: Current round number
            speaking_position: Position in speaking order
            transcript: Current conversation transcript
            memory_context: Pre-built memory context string
            
        Returns:
            Generated memory entry
        """
        # Default single-prompt implementation (existing behavior)
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
        
        # Parse the memory response
        situation = self._extract_section(memory_text, "SITUATION:")
        agents_analysis = self._extract_section(memory_text, "AGENTS:")
        strategy = self._extract_section(memory_text, "STRATEGY:")
        
        # Create memory entry
        return MemoryEntry(
            round_number=round_number,
            timestamp=datetime.now(),
            situation_assessment=situation,
            other_agents_analysis=agents_analysis,
            strategy_update=strategy,
            speaking_position=speaking_position
        )
    
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


class FullMemoryStrategy(MemoryStrategy):
    """Include all previous memory entries (current behavior)."""
    
    def should_include_memory(self, memory_entry: MemoryEntry, current_round: int) -> bool:
        """Include all memory entries."""
        return True
    
    def get_memory_context_limit(self) -> int:
        """No limit on memory entries."""
        return 1000  # Effectively unlimited


class RecentMemoryStrategy(MemoryStrategy):
    """Include only the most recent N memory entries."""
    
    def __init__(self, max_entries: int = 3):
        """
        Initialize recent memory strategy.
        
        Args:
            max_entries: Maximum number of recent entries to include
        """
        self.max_entries = max_entries
    
    def should_include_memory(self, memory_entry: MemoryEntry, current_round: int) -> bool:
        """Include if within recent limit (handled by get_memory_context_limit)."""
        return True
    
    def get_memory_context_limit(self) -> int:
        """Return maximum recent entries."""
        return self.max_entries




class MemoryService:
    """Centralized service for managing agent memory."""
    
    def __init__(self, memory_strategy: MemoryStrategy = None):
        """
        Initialize memory service.
        
        Args:
            memory_strategy: Strategy for memory management. 
                           Defaults to FullMemoryStrategy for compatibility.
        """
        self.memory_strategy = memory_strategy or FullMemoryStrategy()
        self.agent_memories: Dict[str, AgentMemory] = {}
    
    def initialize_agent_memory(self, agent_id: str):
        """Initialize memory for an agent."""
        if agent_id not in self.agent_memories:
            self.agent_memories[agent_id] = AgentMemory(agent_id=agent_id)
    
    def get_agent_memory(self, agent_id: str) -> AgentMemory:
        """Get agent memory, creating if necessary."""
        if agent_id not in self.agent_memories:
            self.initialize_agent_memory(agent_id)
        return self.agent_memories[agent_id]
    
    async def update_agent_memory(self, agent: DeliberationAgent, round_number: int, 
                                speaking_position: int, transcript: List[DeliberationResponse]) -> MemoryEntry:
        """
        Update an agent's private memory before they speak.
        
        Args:
            agent: Agent to update memory for
            round_number: Current round number
            speaking_position: Position in speaking order
            transcript: Current conversation transcript
            
        Returns:
            New memory entry created
        """
        agent_memory = self.get_agent_memory(agent.agent_id)
        
        # Build memory context
        memory_context = self._build_memory_context(agent.agent_id, round_number, transcript)
        
        # Use strategy to generate memory entry
        memory_entry = await self.memory_strategy.generate_memory_entry(
            agent, round_number, speaking_position, transcript, memory_context
        )
        
        # Add to agent's memory
        agent_memory.add_memory(memory_entry)
        
        return memory_entry
    
    def _build_memory_context(self, agent_id: str, round_number: int, 
                             transcript: List[DeliberationResponse]) -> str:
        """Build context for memory update including conversation history."""
        context_parts = []
        
        # Add previous rounds summary
        if transcript:
            context_parts.append("PREVIOUS CONVERSATION:")
            
            # Get previous rounds (not current round)
            previous_responses = [r for r in transcript if r.round_number < round_number]
            for response in previous_responses[-10:]:  # Last 10 messages
                context_parts.append(f"Round {response.round_number} - {response.agent_name}: {response.public_message[:200]}...")
        
        # Add current round so far (speakers before this agent)
        current_round_responses = [r for r in transcript if r.round_number == round_number]
        if current_round_responses:
            context_parts.append(f"\nCURRENT ROUND {round_number} SO FAR:")
            for response in current_round_responses:
                context_parts.append(f"{response.agent_name}: {response.public_message[:200]}...")
        
        # Add agent's own memory (filtered by strategy)
        agent_memory = self.get_agent_memory(agent_id)
        if agent_memory.memory_entries:
            context_parts.append(f"\nYOUR PREVIOUS MEMORY:")
            
            # Filter memories based on strategy
            relevant_memories = []
            for entry in agent_memory.memory_entries:
                if self.memory_strategy.should_include_memory(entry, round_number):
                    relevant_memories.append(entry)
            
            # Apply limit
            max_entries = self.memory_strategy.get_memory_context_limit()
            relevant_memories = relevant_memories[-max_entries:]
            
            for entry in relevant_memories:
                context_parts.append(f"Round {entry.round_number} Strategy: {entry.strategy_update[:100]}...")
        
        return "\n".join(context_parts)
    
    def get_all_agent_memories(self) -> List[AgentMemory]:
        """Get all agent memories for export."""
        return list(self.agent_memories.values())
    
    def get_agent_memory_summary(self, agent_id: str) -> Dict[str, any]:
        """Get summary of agent's memory for analysis."""
        agent_memory = self.get_agent_memory(agent_id)
        
        if not agent_memory.memory_entries:
            return {
                "agent_id": agent_id,
                "total_memories": 0,
                "strategy_evolution": [],
                "memory_timeline": []
            }
        
        return {
            "agent_id": agent_id,
            "total_memories": len(agent_memory.memory_entries),
            "strategy_evolution": agent_memory.get_strategy_evolution(),
            "memory_timeline": [
                {
                    "round": entry.round_number,
                    "timestamp": entry.timestamp,
                    "situation_length": len(entry.situation_assessment),
                    "strategy_length": len(entry.strategy_update)
                }
                for entry in agent_memory.memory_entries
            ]
        }
    
    def clear_agent_memory(self, agent_id: str):
        """Clear all memory for an agent."""
        if agent_id in self.agent_memories:
            del self.agent_memories[agent_id]
    
    def clear_all_memories(self):
        """Clear all agent memories."""
        self.agent_memories.clear()
    
    def set_memory_strategy(self, strategy: MemoryStrategy):
        """Change the memory management strategy."""
        self.memory_strategy = strategy


class DecomposedMemoryStrategy(MemoryStrategy):
    """Memory strategy using focused, sequential prompts to improve memory quality."""
    
    def __init__(self, max_entries: int = 5):
        """
        Initialize decomposed memory strategy.
        
        Args:
            max_entries: Maximum number of recent memory entries to include in context
        """
        self.max_entries = max_entries
    
    def should_include_memory(self, memory_entry: MemoryEntry, current_round: int) -> bool:
        """Include memory entries for context building (handled by limit)."""
        return True
    
    def get_memory_context_limit(self) -> int:
        """Return maximum recent entries."""
        return self.max_entries
    
    async def generate_memory_entry(self, agent: DeliberationAgent, round_number: int,
                                   speaking_position: int, transcript: List[DeliberationResponse],
                                   memory_context: str) -> MemoryEntry:
        """
        Generate memory using three focused sequential steps.
        
        Args:
            agent: Agent to generate memory for
            round_number: Current round number
            speaking_position: Position in speaking order
            transcript: Current conversation transcript
            memory_context: Pre-built memory context string
            
        Returns:
            Generated memory entry
        """
        # Step 1: Generate factual recap
        factual_recap = await self._generate_factual_recap(agent, round_number, transcript)
        
        # Step 2: Generate focused agent analysis
        agent_analysis = await self._generate_agent_analysis(agent, round_number, transcript, factual_recap)
        
        # Step 3: Generate specific strategic action
        strategic_action = await self._generate_strategic_action(agent, round_number, factual_recap, agent_analysis)
        
        # Create memory entry
        return MemoryEntry(
            round_number=round_number,
            timestamp=datetime.now(),
            situation_assessment=factual_recap,
            other_agents_analysis=agent_analysis,
            strategy_update=strategic_action,
            speaking_position=speaking_position
        )
    
    async def _generate_factual_recap(self, agent: DeliberationAgent, round_number: int,
                                     transcript: List[DeliberationResponse]) -> str:
        """Step 1: Generate simple factual recap of recent events."""
        
        # Get recent conversation (last 5 messages to keep focused)
        recent_responses = [r for r in transcript if r.round_number >= max(1, round_number - 1)][-5:]
        
        if not recent_responses:
            return "No recent conversation to summarize."
        
        recent_transcript = "\n".join([
            f"Round {r.round_number} - {r.agent_name}: {r.public_message[:300]}..."
            for r in recent_responses
        ])
        
        prompt = f"""Briefly summarize what just happened in the deliberation:

RECENT CONVERSATION:
{recent_transcript}

Focus on FACTS only:
- Who spoke and in what order?
- What principle did each agent choose?
- What key topics or concerns were mentioned?

Keep it factual and concise (2-3 sentences max).
Avoid interpretations or motivations."""

        result = await Runner.run(agent, prompt)
        return ItemHelpers.text_message_outputs(result.new_items).strip()
    
    async def _generate_agent_analysis(self, agent: DeliberationAgent, round_number: int,
                                      transcript: List[DeliberationResponse], factual_recap: str) -> str:
        """Step 2: Generate focused analysis of one specific agent's behavior."""
        
        # Select target agent for analysis (most recent speaker who isn't this agent)
        target_agent = self._select_analysis_target(agent, transcript, round_number)
        
        if not target_agent:
            return "No other agents to analyze in recent conversation."
        
        prompt = f"""Based on these facts: {factual_recap}

Focus ONLY on {target_agent}'s behavior and statements:

1. What specific statements did they make?
2. What principle did they choose and what reasoning did they give?
3. Are they showing flexibility, consistency, or change in position?
4. What specific concerns or priorities do they keep mentioning?

Give concrete examples from their actual words.
Avoid assumptions about hidden motivations - focus on observable behavior."""

        result = await Runner.run(agent, prompt)
        return ItemHelpers.text_message_outputs(result.new_items).strip()
    
    async def _generate_strategic_action(self, agent: DeliberationAgent, round_number: int,
                                        factual_recap: str, agent_analysis: str) -> str:
        """Step 3: Generate one specific, actionable strategy for next round."""
        
        prompt = f"""Given this situation:

FACTS: {factual_recap}
AGENT ANALYSIS: {agent_analysis}

What is ONE specific thing you could do in the next round to move toward consensus?

Be concrete and actionable:
- What exact argument or point could you make?
- Which specific agent would you focus on persuading?
- What particular concern would you address?
- How would you frame your message?

Give ONE focused strategy, not multiple general ideas."""

        result = await Runner.run(agent, prompt)
        return ItemHelpers.text_message_outputs(result.new_items).strip()
    
    def _select_analysis_target(self, agent: DeliberationAgent, transcript: List[DeliberationResponse],
                               round_number: int) -> Optional[str]:
        """Select which agent to focus analysis on."""
        
        # Get recent responses (last 3 rounds)
        recent_responses = [r for r in transcript if r.round_number >= max(1, round_number - 2)]
        
        # Find agents who spoke recently (excluding this agent)
        recent_speakers = []
        for response in reversed(recent_responses):  # Most recent first
            if response.agent_name != agent.name and response.agent_name not in recent_speakers:
                recent_speakers.append(response.agent_name)
        
        # Return most recent speaker who isn't this agent
        return recent_speakers[0] if recent_speakers else None


def create_memory_strategy(strategy_name: str) -> MemoryStrategy:
    """
    Factory function to create memory strategies based on configuration.
    
    Args:
        strategy_name: Strategy name (full|recent|decomposed)
        
    Returns:
        Configured memory strategy instance
    """
    strategy_map = {
        "full": FullMemoryStrategy,
        "recent": RecentMemoryStrategy,
        "decomposed": DecomposedMemoryStrategy
    }
    
    if strategy_name not in strategy_map:
        raise ValueError(f"Unknown memory strategy: {strategy_name}. Available: {list(strategy_map.keys())}")
    
    return strategy_map[strategy_name]()