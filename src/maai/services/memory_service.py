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


class SelectiveMemoryStrategy(MemoryStrategy):
    """Include only memory from the last N rounds."""
    
    def __init__(self, max_rounds: int = 3):
        """
        Initialize selective memory strategy.
        
        Args:
            max_rounds: Maximum number of recent rounds to remember
        """
        self.max_rounds = max_rounds
    
    def should_include_memory(self, memory_entry: MemoryEntry, current_round: int) -> bool:
        """Include if within recent rounds."""
        return current_round - memory_entry.round_number <= self.max_rounds
    
    def get_memory_context_limit(self) -> int:
        """No specific limit (handled by round filtering)."""
        return 1000


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
        
        # Generate memory update prompt
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