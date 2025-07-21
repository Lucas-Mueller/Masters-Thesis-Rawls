"""
MemoryService for centralized agent memory management.
Handles memory strategies, updates, and retrieval for all agents.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
from agents import Runner, ItemHelpers
from ..core.models import (
    AgentMemory, MemoryEntry, DeliberationResponse,
    EnhancedAgentMemory, IndividualMemoryEntry, IndividualMemoryType,
    IndividualMemoryContent, IndividualReflectionContext, LearningContext,
    Phase1ExperienceData, ConsolidatedMemory, PrincipleChoice, EconomicOutcome
)
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
    
    def __init__(self, memory_strategy: MemoryStrategy = None, logger=None, enable_phase1_memory: bool = True):
        """
        Initialize memory service.
        
        Args:
            memory_strategy: Strategy for memory management. 
                           Defaults to RecentMemoryStrategy for compatibility.
            logger: ExperimentLogger instance for logging memory operations
            enable_phase1_memory: Whether to enable Phase 1 memory functionality
        """
        self.memory_strategy = memory_strategy or RecentMemoryStrategy()
        self.agent_memories: Dict[str, EnhancedAgentMemory] = {}
        self.logger = logger
        self.enable_phase1_memory = enable_phase1_memory
    
    def initialize_agent_memory(self, agent_id: str):
        """Initialize memory for an agent."""
        if agent_id not in self.agent_memories:
            self.agent_memories[agent_id] = EnhancedAgentMemory(agent_id=agent_id)
    
    def get_agent_memory(self, agent_id: str) -> EnhancedAgentMemory:
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
        
        # Log memory context
        if self.logger:
            self.logger.log_memory_generation(
                agent_id=agent.name,
                round_num=round_number,
                memory_content=memory_context,
                strategy=type(self.memory_strategy).__name__
            )
        
        # Use strategy to generate memory entry
        if isinstance(self.memory_strategy, DecomposedMemoryStrategy):
            # For decomposed strategy, we want to log each step
            memory_entry = await self._generate_decomposed_memory_with_logging(
                agent, round_number, speaking_position, transcript, memory_context
            )
        else:
            memory_entry = await self.memory_strategy.generate_memory_entry(
                agent, round_number, speaking_position, transcript, memory_context
            )
        
        # Log final memory entry
        if self.logger:
            memory_content = f"SITUATION: {memory_entry.situation_assessment}\nAGENTS: {memory_entry.other_agents_analysis}\nSTRATEGY: {memory_entry.strategy_update}"
            self.logger.log_memory_generation(
                agent_id=agent.name,
                round_num=round_number,
                memory_content=memory_content,
                strategy=memory_entry.strategy_update
            )
        
        # Add to agent's memory
        agent_memory.add_memory(memory_entry)
        
        return memory_entry
    
    def _build_memory_context(self, agent_id: str, round_number: int, 
                             transcript: List[DeliberationResponse]) -> str:
        """Build context for memory update including conversation history and Phase 1 memories."""
        context_parts = []
        
        # Add Phase 1 context if enabled (only for Phase 2 rounds)
        if self.enable_phase1_memory and round_number >= 1:
            phase1_context = self.get_phase1_context_for_phase2(agent_id)
            if phase1_context:
                context_parts.append(phase1_context)
        
        # Add previous rounds summary
        if transcript:
            context_parts.append("PREVIOUS CONVERSATION:")
            
            # Get previous rounds (not current round)
            previous_responses = [r for r in transcript if r.round_number < round_number]
            for response in previous_responses[-10:]:  # Last 10 messages
                context_parts.append(f"Round {response.round_number} - {response.agent_name}: {response.public_message}")
        
        # Add current round so far (speakers before this agent)
        current_round_responses = [r for r in transcript if r.round_number == round_number]
        if current_round_responses:
            context_parts.append(f"\nCURRENT ROUND {round_number} SO FAR:")
            for response in current_round_responses:
                context_parts.append(f"{response.agent_name}: {response.public_message}")
        
        # Add agent's own Phase 2 memory (filtered by strategy)
        agent_memory = self.get_agent_memory(agent_id)
        if agent_memory.memory_entries:
            context_parts.append(f"\nYOUR PREVIOUS DELIBERATION MEMORY:")
            
            # Filter memories based on strategy
            relevant_memories = []
            for entry in agent_memory.memory_entries:
                if self.memory_strategy.should_include_memory(entry, round_number):
                    relevant_memories.append(entry)
            
            # Apply limit
            max_entries = self.memory_strategy.get_memory_context_limit()
            relevant_memories = relevant_memories[-max_entries:]
            
            for entry in relevant_memories:
                context_parts.append(f"Round {entry.round_number} Strategy: {entry.strategy_update}")
        
        return "\n".join(context_parts)
    
    def get_all_agent_memories(self) -> List[EnhancedAgentMemory]:
        """Get all agent memories for export."""
        return list(self.agent_memories.values())
    
    # Phase 1 Memory Methods
    async def generate_individual_reflection(self, agent: DeliberationAgent, 
                                           reflection_context: IndividualReflectionContext) -> IndividualMemoryEntry:
        """
        Generate an individual reflection memory for Phase 1 activities.
        
        Args:
            agent: Agent to generate reflection for
            reflection_context: Context for reflection generation
            
        Returns:
            Generated individual memory entry
        """
        if not self.enable_phase1_memory:
            return None
        
        memory_prompt = f"""You are reflecting on your individual experience in this distributive justice experiment.

CURRENT ACTIVITY: {reflection_context.activity}

{reflection_context.reasoning_prompt}

Based on your experience so far, please provide:

1. SITUATION ASSESSMENT: What is happening in your individual learning process?

2. REASONING PROCESS: What thoughts and considerations are going through your mind?

3. INSIGHTS GAINED: What new insights or understanding have you developed?

4. CONFIDENCE LEVEL: How confident do you feel about your current understanding? (0.0 = very unsure, 1.0 = very confident)

5. PREFERENCE EVOLUTION: How have your preferences or views changed, if at all?

Please structure your response as:
SITUATION: [your assessment]
REASONING: [your thought process]
INSIGHTS: [what you learned]
CONFIDENCE: [0.0-1.0 number]
PREFERENCES: [how your views evolved]
"""
        
        result = await Runner.run(agent, memory_prompt)
        response_text = ItemHelpers.text_message_outputs(result.new_items)
        
        # Parse the response
        situation = self._extract_section(response_text, "SITUATION:")
        reasoning = self._extract_section(response_text, "REASONING:")
        insights = self._extract_section(response_text, "INSIGHTS:")
        confidence_text = self._extract_section(response_text, "CONFIDENCE:")
        preferences = self._extract_section(response_text, "PREFERENCES:")
        
        # Parse confidence level
        try:
            confidence_level = float(confidence_text.split()[0])
            confidence_level = max(0.0, min(1.0, confidence_level))  # Clamp to 0-1 range
        except (ValueError, IndexError):
            confidence_level = 0.5  # Default middle value
        
        # Create memory content
        content = IndividualMemoryContent(
            situation_assessment=situation,
            reasoning_process=reasoning,
            insights_gained=insights,
            confidence_level=confidence_level,
            preference_evolution=preferences
        )
        
        # Create memory entry
        memory_entry = IndividualMemoryEntry(
            memory_id=str(uuid4()),
            agent_id=agent.agent_id,
            memory_type=IndividualMemoryType.REFLECTION,
            content=content,
            activity_context=reflection_context.activity
        )
        
        # Add to agent memory
        agent_memory = self.get_agent_memory(agent.agent_id)
        agent_memory.add_individual_memory(memory_entry)
        
        # Log if logger available
        if self.logger:
            self.logger.log_memory_generation(
                agent_id=agent.name,
                round_num=0,  # Phase 1
                memory_content=f"Phase 1 Reflection - {reflection_context.activity}: {insights}",
                strategy="individual_reflection"
            )
        
        return memory_entry
    
    async def update_individual_learning(self, agent: DeliberationAgent, 
                                       learning_context: LearningContext) -> IndividualMemoryEntry:
        """
        Update an agent's individual learning memory.
        
        Args:
            agent: Agent to update learning for
            learning_context: Context for learning update
            
        Returns:
            Generated learning memory entry
        """
        if not self.enable_phase1_memory:
            return None
        
        # Build learning prompt
        previous_context = ""
        if learning_context.previous_understanding:
            previous_context = f"\nYOUR PREVIOUS UNDERSTANDING: {learning_context.previous_understanding}"
        
        memory_prompt = f"""You are building your understanding of distributive justice principles through examples and practice.

LEARNING STAGE: {learning_context.learning_stage}
NEW INFORMATION: {learning_context.new_information}{previous_context}

Based on this new information, please reflect on:

1. SITUATION ASSESSMENT: What are you learning about in this stage?

2. REASONING PROCESS: How are you processing and integrating this new information?

3. INSIGHTS GAINED: What patterns, connections, or insights are emerging?

4. CONFIDENCE LEVEL: How confident are you becoming in your understanding? (0.0-1.0)

5. STRATEGIC IMPLICATIONS: How might this learning affect your approach in group discussions?

Please structure your response as:
SITUATION: [learning context]
REASONING: [integration process]
INSIGHTS: [emerging understanding]
CONFIDENCE: [0.0-1.0 number]
STRATEGY: [implications for group phase]
"""
        
        result = await Runner.run(agent, memory_prompt)
        response_text = ItemHelpers.text_message_outputs(result.new_items)
        
        # Parse the response
        situation = self._extract_section(response_text, "SITUATION:")
        reasoning = self._extract_section(response_text, "REASONING:")
        insights = self._extract_section(response_text, "INSIGHTS:")
        confidence_text = self._extract_section(response_text, "CONFIDENCE:")
        strategy = self._extract_section(response_text, "STRATEGY:")
        
        # Parse confidence level
        try:
            confidence_level = float(confidence_text.split()[0])
            confidence_level = max(0.0, min(1.0, confidence_level))
        except (ValueError, IndexError):
            confidence_level = 0.5
        
        # Create memory content
        content = IndividualMemoryContent(
            situation_assessment=situation,
            reasoning_process=reasoning,
            insights_gained=insights,
            confidence_level=confidence_level,
            strategic_implications=strategy
        )
        
        # Create memory entry
        memory_entry = IndividualMemoryEntry(
            memory_id=str(uuid4()),
            agent_id=agent.agent_id,
            memory_type=IndividualMemoryType.LEARNING,
            content=content,
            activity_context=learning_context.learning_stage
        )
        
        # Add to agent memory
        agent_memory = self.get_agent_memory(agent.agent_id)
        agent_memory.add_individual_memory(memory_entry)
        
        # Log if logger available
        if self.logger:
            self.logger.log_memory_generation(
                agent_id=agent.name,
                round_num=0,  # Phase 1
                memory_content=f"Phase 1 Learning - {learning_context.learning_stage}: {insights}",
                strategy="individual_learning"
            )
        
        return memory_entry
    
    async def integrate_phase1_experience(self, agent: DeliberationAgent, 
                                        experience_data: Phase1ExperienceData) -> IndividualMemoryEntry:
        """
        Integrate a Phase 1 experience into memory.
        
        Args:
            agent: Agent to generate integration memory for
            experience_data: Experience data to integrate
            
        Returns:
            Generated integration memory entry
        """
        if not self.enable_phase1_memory:
            return None
        
        # Build experience context
        experience_context = []
        if experience_data.principle_choice:
            experience_context.append(f"PRINCIPLE CHOSEN: {experience_data.principle_choice.principle_name}")
            experience_context.append(f"REASONING: {experience_data.principle_choice.reasoning}")
        
        if experience_data.economic_outcome:
            experience_context.append(f"ECONOMIC OUTCOME: Assigned {experience_data.economic_outcome.assigned_income_class.value} income class")
            experience_context.append(f"ACTUAL INCOME: ${experience_data.economic_outcome.actual_income:,}")
            experience_context.append(f"PAYOUT: ${experience_data.economic_outcome.payout_amount:.4f}")
        
        if experience_data.examples_shown:
            experience_context.append(f"EXAMPLES SHOWN: {len(experience_data.examples_shown)} distribution examples")
        
        context_text = "\n".join(experience_context)
        
        memory_prompt = f"""You have just completed an individual experience in the distributive justice experiment.

EXPERIENCE DETAILS:
{context_text}

REFLECTION QUESTION: {experience_data.reflection_prompt}

Please reflect on this experience:

1. SITUATION ASSESSMENT: What just happened and what was significant about it?

2. REASONING PROCESS: What went through your mind during this experience?

3. INSIGHTS GAINED: What did you learn from this specific experience?

4. CONFIDENCE LEVEL: How has this experience affected your confidence? (0.0-1.0)

5. STRATEGIC IMPLICATIONS: How might this experience influence your group strategy?

Please structure your response as:
SITUATION: [what happened]
REASONING: [your thought process]
INSIGHTS: [specific learnings]
CONFIDENCE: [0.0-1.0 number]
STRATEGY: [group phase implications]
"""
        
        result = await Runner.run(agent, memory_prompt)
        response_text = ItemHelpers.text_message_outputs(result.new_items)
        
        # Parse the response
        situation = self._extract_section(response_text, "SITUATION:")
        reasoning = self._extract_section(response_text, "REASONING:")
        insights = self._extract_section(response_text, "INSIGHTS:")
        confidence_text = self._extract_section(response_text, "CONFIDENCE:")
        strategy = self._extract_section(response_text, "STRATEGY:")
        
        # Parse confidence level
        try:
            confidence_level = float(confidence_text.split()[0])
            confidence_level = max(0.0, min(1.0, confidence_level))
        except (ValueError, IndexError):
            confidence_level = 0.5
        
        # Create memory content
        content = IndividualMemoryContent(
            situation_assessment=situation,
            reasoning_process=reasoning,
            insights_gained=insights,
            confidence_level=confidence_level,
            strategic_implications=strategy
        )
        
        # Determine activity context
        activity_context = f"individual_round_{experience_data.round_number}" if experience_data.round_number else "experience_integration"
        
        # Create memory entry
        memory_entry = IndividualMemoryEntry(
            memory_id=str(uuid4()),
            agent_id=agent.agent_id,
            memory_type=IndividualMemoryType.INTEGRATION,
            content=content,
            activity_context=activity_context,
            round_context=experience_data.round_number
        )
        
        # Add to agent memory
        agent_memory = self.get_agent_memory(agent.agent_id)
        agent_memory.add_individual_memory(memory_entry)
        
        # Log if logger available
        if self.logger:
            self.logger.log_memory_generation(
                agent_id=agent.name,
                round_num=experience_data.round_number or 0,
                memory_content=f"Phase 1 Integration - {activity_context}: {insights}",
                strategy="experience_integration"
            )
        
        return memory_entry
    
    async def consolidate_phase1_memories(self, agent_id: str) -> ConsolidatedMemory:
        """
        Consolidate Phase 1 memories into a summary for Phase 2 context.
        
        Args:
            agent_id: Agent to consolidate memories for
            
        Returns:
            Consolidated memory summary
        """
        if not self.enable_phase1_memory:
            return None
        
        agent_memory = self.get_agent_memory(agent_id)
        
        if not agent_memory.has_individual_memories():
            # No individual memories to consolidate
            return ConsolidatedMemory(
                agent_id=agent_id,
                consolidated_insights="No individual experiences to consolidate.",
                strategic_preferences="No strategic preferences developed.",
                economic_learnings="No economic learnings accumulated.",
                confidence_summary="No confidence evolution tracked.",
                principle_understanding="No principle understanding developed."
            )
        
        # Prepare memory context for consolidation
        memory_summaries = []
        for memory in agent_memory.individual_memories:
            summary = f"Activity: {memory.activity_context}\n"
            summary += f"Insights: {memory.content.insights_gained}\n"
            summary += f"Confidence: {memory.content.confidence_level}\n"
            if memory.content.strategic_implications:
                summary += f"Strategic Implications: {memory.content.strategic_implications}\n"
            if memory.content.preference_evolution:
                summary += f"Preference Evolution: {memory.content.preference_evolution}\n"
            memory_summaries.append(summary)
        
        memories_text = "\n---\n".join(memory_summaries)
        
        consolidation_prompt = f"""You are consolidating your individual learning experiences before entering group deliberation.

YOUR INDIVIDUAL PHASE 1 EXPERIENCES:
{memories_text}

Please create a consolidated summary that will help you in group discussions:

1. CONSOLIDATED INSIGHTS: What are the key insights you gained across all individual experiences?

2. STRATEGIC PREFERENCES: What strategic preferences or approaches have you developed?

3. ECONOMIC LEARNINGS: What did you learn about economic outcomes and their impact?

4. CONFIDENCE SUMMARY: How has your confidence evolved throughout these experiences?

5. PRINCIPLE UNDERSTANDING: How has your understanding of the four distributive justice principles evolved?

Please structure your response as:
INSIGHTS: [key consolidated insights]
PREFERENCES: [strategic approaches developed]
ECONOMICS: [economic learnings]
CONFIDENCE: [confidence evolution]
PRINCIPLES: [principle understanding evolution]
"""
        
        # Get agent for LLM call
        from ..agents.enhanced import DeliberationAgent
        # We need to create a temporary agent or find the agent object
        # For now, let's assume we can access it through the memory system
        # This is a design issue that might need refinement
        
        # Create temporary agent for consolidation (this might need to be refactored)
        from agents.model_settings import ModelSettings
        model_settings = ModelSettings(temperature=0.1)
        
        temp_agent = DeliberationAgent(
            agent_id=f"temp_{agent_id}",
            name=f"temp_{agent_id}",
            model="gpt-4.1-mini",
            personality="Consolidation agent",
            model_settings=model_settings
        )
        
        result = await Runner.run(temp_agent, consolidation_prompt)
        response_text = ItemHelpers.text_message_outputs(result.new_items)
        
        # Parse the consolidated response
        insights = self._extract_section(response_text, "INSIGHTS:")
        preferences = self._extract_section(response_text, "PREFERENCES:")
        economics = self._extract_section(response_text, "ECONOMICS:")
        confidence = self._extract_section(response_text, "CONFIDENCE:")
        principles = self._extract_section(response_text, "PRINCIPLES:")
        
        # Create consolidated memory
        consolidated = ConsolidatedMemory(
            agent_id=agent_id,
            consolidated_insights=insights,
            strategic_preferences=preferences,
            economic_learnings=economics,
            confidence_summary=confidence,
            principle_understanding=principles
        )
        
        # Store in agent memory
        agent_memory.consolidated_memory = consolidated
        
        # Log if logger available
        if self.logger:
            self.logger.log_memory_generation(
                agent_id=agent_id,
                round_num=0,
                memory_content=f"Phase 1 Consolidation: {insights}",
                strategy="memory_consolidation"
            )
        
        return consolidated
    
    def get_phase1_context_for_phase2(self, agent_id: str) -> str:
        """
        Get Phase 1 memory context to include in Phase 2 deliberation.
        
        Args:
            agent_id: Agent to get context for
            
        Returns:
            Formatted context string for Phase 2 use
        """
        if not self.enable_phase1_memory:
            return ""
        
        agent_memory = self.get_agent_memory(agent_id)
        context_parts = []
        
        # Add consolidated memory if available
        if agent_memory.consolidated_memory:
            context_parts.append("YOUR INDIVIDUAL PHASE INSIGHTS:")
            context_parts.append(f"Key Insights: {agent_memory.consolidated_memory.consolidated_insights}")
            context_parts.append(f"Strategic Preferences: {agent_memory.consolidated_memory.strategic_preferences}")
            context_parts.append(f"Economic Learnings: {agent_memory.consolidated_memory.economic_learnings}")
            context_parts.append("")
        
        # Add recent individual memories if no consolidation available
        elif agent_memory.has_individual_memories():
            context_parts.append("YOUR INDIVIDUAL PHASE INSIGHTS:")
            recent_memories = agent_memory.individual_memories[-3:]  # Last 3 memories
            for memory in recent_memories:
                context_parts.append(f"{memory.activity_context}: {memory.content.insights_gained}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_agent_memory_summary(self, agent_id: str) -> Dict[str, any]:
        """Get summary of agent's memory for analysis."""
        agent_memory = self.get_agent_memory(agent_id)
        
        # Phase 2 memory summary
        phase2_summary = {
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
        
        # Phase 1 memory summary
        phase1_summary = {
            "total_individual_memories": len(agent_memory.individual_memories),
            "memory_types": [memory.memory_type.value for memory in agent_memory.individual_memories],
            "activities": [memory.activity_context for memory in agent_memory.individual_memories],
            "insights": agent_memory.get_individual_insights(),
            "has_consolidation": agent_memory.consolidated_memory is not None
        }
        
        return {
            "agent_id": agent_id,
            "phase1": phase1_summary,
            "phase2": phase2_summary,
            "consolidated_memory": {
                "available": agent_memory.consolidated_memory is not None,
                "insights": agent_memory.consolidated_memory.consolidated_insights if agent_memory.consolidated_memory else None,
                "confidence": agent_memory.consolidated_memory.confidence_summary if agent_memory.consolidated_memory else None
            }
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
    
    def _extract_section(self, text: str, section_header: str) -> str:
        """Extract a section from structured text."""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            if line.strip().startswith(section_header):
                in_section = True
                section_lines.append(line.replace(section_header, '').strip())
            elif in_section and line.strip().startswith(('SITUATION:', 'REASONING:', 'INSIGHTS:', 'CONFIDENCE:', 'PREFERENCES:', 'STRATEGY:', 'ECONOMICS:', 'PRINCIPLES:')):
                break
            elif in_section:
                section_lines.append(line.strip())
        
        return '\n'.join(section_lines).strip() or "No analysis provided"
    
    async def _generate_decomposed_memory_with_logging(self, agent: DeliberationAgent, 
                                                     round_number: int, speaking_position: int,
                                                     transcript: List[DeliberationResponse], 
                                                     memory_context: str) -> MemoryEntry:
        """Generate decomposed memory with step-by-step logging."""
        import time
        decomposed_steps = []
        
        # Step 1: Generate factual recap
        start_time = time.time()
        factual_recap = await self.memory_strategy._generate_factual_recap(agent, round_number, transcript)
        processing_time_ms = (time.time() - start_time) * 1000
        
        step_1 = {
            "step": "factual_recap",
            "prompt": "Briefly summarize what just happened in the deliberation",
            "response": factual_recap,
            "processing_time_ms": processing_time_ms
        }
        decomposed_steps.append(step_1)
        
        # Step 2: Generate focused agent analysis
        start_time = time.time()
        agent_analysis = await self.memory_strategy._generate_agent_analysis(agent, round_number, transcript, factual_recap)
        processing_time_ms = (time.time() - start_time) * 1000
        
        step_2 = {
            "step": "agent_analysis",
            "prompt": "Focus on specific agent behavior and statements",
            "response": agent_analysis,
            "processing_time_ms": processing_time_ms
        }
        decomposed_steps.append(step_2)
        
        # Step 3: Generate specific strategic action
        start_time = time.time()
        strategic_action = await self.memory_strategy._generate_strategic_action(agent, round_number, factual_recap, agent_analysis)
        processing_time_ms = (time.time() - start_time) * 1000
        
        step_3 = {
            "step": "strategic_action",
            "prompt": "What specific action or actions you could take next round?",
            "response": strategic_action,
            "processing_time_ms": processing_time_ms
        }
        decomposed_steps.append(step_3)
        
        # Log decomposed memory generation
        if self.logger:
            memory_content = f"DECOMPOSED MEMORY:\n1. RECAP: {factual_recap}\n2. ANALYSIS: {agent_analysis}\n3. STRATEGY: {strategic_action}"
            self.logger.log_memory_generation(
                agent_id=agent.name,
                round_num=round_number,
                memory_content=memory_content,
                strategy="decomposed"
            )
        
        # Create memory entry
        return MemoryEntry(
            round_number=round_number,
            timestamp=datetime.now(),
            situation_assessment=factual_recap,
            other_agents_analysis=agent_analysis,
            strategy_update=strategic_action,
            speaking_position=speaking_position
        )


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
            f"Round {r.round_number} - {r.agent_name}: {r.public_message}"
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


class Phase1AwareDecomposedStrategy(DecomposedMemoryStrategy):
    """
    Enhanced decomposed memory strategy that's aware of Phase 1 experiences.
    Provides more nuanced memory generation by considering individual phase learning.
    """
    
    def __init__(self, max_entries: int = 5, phase1_weight: float = 0.3):
        """
        Initialize Phase 1 aware decomposed memory strategy.
        
        Args:
            max_entries: Maximum number of recent memory entries to include in context
            phase1_weight: Weight given to Phase 1 insights in memory generation (0.0-1.0)
        """
        super().__init__(max_entries)
        self.phase1_weight = phase1_weight
    
    async def generate_memory_entry(self, agent: DeliberationAgent, round_number: int,
                                   speaking_position: int, transcript: List[DeliberationResponse],
                                   memory_context: str) -> MemoryEntry:
        """
        Generate memory using three focused sequential steps with Phase 1 awareness.
        """
        # Check if Phase 1 context is available in memory_context
        has_phase1_context = "YOUR INDIVIDUAL PHASE INSIGHTS:" in memory_context
        
        # Step 1: Generate factual recap (same as parent)
        factual_recap = await self._generate_factual_recap(agent, round_number, transcript)
        
        # Step 2: Generate Phase 1 aware agent analysis
        if has_phase1_context:
            agent_analysis = await self._generate_phase1_aware_agent_analysis(
                agent, round_number, transcript, factual_recap, memory_context
            )
        else:
            agent_analysis = await self._generate_agent_analysis(
                agent, round_number, transcript, factual_recap
            )
        
        # Step 3: Generate Phase 1 informed strategic action
        if has_phase1_context:
            strategic_action = await self._generate_phase1_informed_strategy(
                agent, round_number, factual_recap, agent_analysis, memory_context
            )
        else:
            strategic_action = await self._generate_strategic_action(
                agent, round_number, factual_recap, agent_analysis
            )
        
        # Create memory entry
        return MemoryEntry(
            round_number=round_number,
            timestamp=datetime.now(),
            situation_assessment=factual_recap,
            other_agents_analysis=agent_analysis,
            strategy_update=strategic_action,
            speaking_position=speaking_position
        )
    
    async def _generate_phase1_aware_agent_analysis(self, agent: DeliberationAgent, round_number: int,
                                                   transcript: List[DeliberationResponse], factual_recap: str,
                                                   memory_context: str) -> str:
        """Generate agent analysis that considers Phase 1 experiences."""
        
        # Extract Phase 1 insights from context
        phase1_insights = ""
        if "YOUR INDIVIDUAL PHASE INSIGHTS:" in memory_context:
            lines = memory_context.split('\n')
            phase1_lines = []
            in_phase1_section = False
            for line in lines:
                if "YOUR INDIVIDUAL PHASE INSIGHTS:" in line:
                    in_phase1_section = True
                    continue
                elif in_phase1_section and line.strip() == "":
                    break
                elif in_phase1_section:
                    phase1_lines.append(line)
            phase1_insights = "\n".join(phase1_lines)
        
        # Select target agent for analysis
        target_agent = self._select_analysis_target(agent, transcript, round_number)
        
        if not target_agent:
            return "No other agents to analyze in recent conversation."
        
        prompt = f"""Based on these facts: {factual_recap}

YOUR INDIVIDUAL PHASE INSIGHTS:
{phase1_insights}

Focus ONLY on {target_agent}'s behavior and statements, considering your individual learning:

1. What specific statements did they make?
2. What principle did they choose and what reasoning did they give?
3. How does their approach compare to insights you gained in individual practice?
4. Are they showing flexibility, consistency, or change in position?
5. Based on your individual experience, what concerns might they have?

Give concrete examples from their actual words.
Consider how your individual learning helps you understand their perspective."""

        result = await Runner.run(agent, prompt)
        return ItemHelpers.text_message_outputs(result.new_items).strip()
    
    async def _generate_phase1_informed_strategy(self, agent: DeliberationAgent, round_number: int,
                                               factual_recap: str, agent_analysis: str,
                                               memory_context: str) -> str:
        """Generate strategy informed by Phase 1 experiences."""
        
        # Extract Phase 1 strategic preferences from context
        phase1_strategy = ""
        if "Strategic Preferences:" in memory_context:
            lines = memory_context.split('\n')
            for line in lines:
                if "Strategic Preferences:" in line:
                    phase1_strategy = line.replace("Strategic Preferences:", "").strip()
                    break
        
        prompt = f"""Given this situation:

FACTS: {factual_recap}
AGENT ANALYSIS: {agent_analysis}
YOUR INDIVIDUAL STRATEGIC PREFERENCES: {phase1_strategy}

What is ONE specific thing you could do in the next round to move toward consensus while staying true to your individual learning?

Be concrete and actionable:
- What exact argument could you make based on your individual experience?
- How can your individual insights help persuade others?
- Which specific agent would you focus on and why?
- How would you bridge your individual learning with group consensus?

Give ONE focused strategy that leverages your individual phase experience."""

        result = await Runner.run(agent, prompt)
        return ItemHelpers.text_message_outputs(result.new_items).strip()


def create_memory_strategy(strategy_name: str) -> MemoryStrategy:
    """
    Factory function to create memory strategies based on configuration.
    
    Args:
        strategy_name: Strategy name (recent|decomposed|phase_aware_decomposed)
        
    Returns:
        Configured memory strategy instance
    """
    strategy_map = {
        "recent": RecentMemoryStrategy,
        "decomposed": DecomposedMemoryStrategy,
        "phase_aware_decomposed": Phase1AwareDecomposedStrategy
    }
    
    if strategy_name not in strategy_map:
        raise ValueError(f"Unknown memory strategy: {strategy_name}. Available: {list(strategy_map.keys())}")
    
    return strategy_map[strategy_name]()