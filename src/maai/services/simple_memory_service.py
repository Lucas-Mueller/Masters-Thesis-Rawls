"""
SimpleMemoryService for the simplified single memory mode system.
Supports only short memory mode - no configuration options.
"""

from typing import Dict
from agents import Runner, ItemHelpers
from ..agents.enhanced import DeliberationAgent


class SimpleMemoryService:
    """Simplified memory service - short mode only."""
    
    def __init__(self):
        """Initialize the simple memory service."""
        # Only short memory - no full mode
        self.agent_memory: Dict[str, str] = {}
        self.last_interactions: Dict[str, Dict[str, str]] = {}  # Store last input/output
    
    def initialize_agent_memory(self, agent_id: str) -> None:
        """Initialize memory tracking for a new agent."""
        if agent_id not in self.agent_memory:
            self.agent_memory[agent_id] = ""
            self.last_interactions[agent_id] = {'input': '', 'output': ''}
    
    def get_memory_context(self, agent_id: str) -> str:
        """Get memory context for an agent (short mode only)."""
        self.initialize_agent_memory(agent_id)
        return self.agent_memory[agent_id]
    
    async def update_memory(self, 
                           agent: DeliberationAgent,
                           last_input: str,
                           last_output: str,
                           current_memory: str) -> str:
        """Update agent's memory with simple prompt."""
        
        update_prompt = f"""=== ROLE DESCRIPTION ===
{getattr(agent, 'personality', 'You are a participant in this negotiation.')}

=== NEGOTIATION DESCRIPTION ===
You are participating in a negotiation about distributive justice principles.

=== BANK BALANCE ===
{self.get_current_balance(agent.agent_id)}

=== MEMORY UPDATE TASK ===
You need to update your memory for the next round.

LAST INPUT YOU RECEIVED:
{last_input}

YOUR LAST RESPONSE:
{last_output}

YOUR CURRENT MEMORY:
{current_memory if current_memory.strip() else "No previous memory entries."}

Please create a useful memory entry for the next round. Keep it concise and focus on what will help you make better decisions."""
        
        result = await Runner.run(agent, update_prompt)
        updated_memory = ItemHelpers.text_message_outputs(result.new_items)
        
        # Store the updated memory
        self.agent_memory[agent.agent_id] = updated_memory
        
        return updated_memory
    
    def store_last_interaction(self, agent_id: str, input_msg: str, output_msg: str):
        """Store the last interaction for memory updates."""
        self.initialize_agent_memory(agent_id)
        self.last_interactions[agent_id] = {
            'input': input_msg,
            'output': output_msg
        }
    
    def get_last_interaction(self, agent_id: str) -> Dict[str, str]:
        """Get the last interaction for an agent."""
        return self.last_interactions.get(agent_id, {'input': '', 'output': ''})
    
    def get_current_balance(self, agent_id: str) -> str:
        """Get current balance - placeholder for now."""
        # This should be integrated with earnings service
        return "You have a current bank balance of $0.0000"
    
    def clear_agent_memory(self, agent_id: str) -> None:
        """Clear all memory for an agent."""
        if agent_id in self.agent_memory:
            self.agent_memory[agent_id] = ""
        if agent_id in self.last_interactions:
            self.last_interactions[agent_id] = {'input': '', 'output': ''}
    
    def get_all_agent_ids(self) -> list[str]:
        """Get all agent IDs that have memory tracking."""
        return list(self.agent_memory.keys())