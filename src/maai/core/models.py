"""
Data models for the Multi-Agent Distributive Justice Experiment.
All models use Pydantic for validation and structure.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PrincipleChoice(BaseModel):
    """Represents an agent's choice of distributive justice principle."""
    principle_id: int = Field(..., ge=1, le=4, description="Principle ID (1-4)")
    principle_name: str = Field(..., description="Name of the chosen principle")
    reasoning: str = Field(..., description="Agent's reasoning for this choice")


class MemoryEntry(BaseModel):
    """Represents a private memory entry for an agent."""
    round_number: int = Field(..., ge=0, description="Round when this memory was created")
    timestamp: datetime = Field(default_factory=datetime.now, description="Memory creation timestamp")
    situation_assessment: str = Field(..., description="Agent's assessment of the current situation")
    other_agents_analysis: str = Field(..., description="Analysis of other agents' positions and motivations")
    strategy_update: str = Field(..., description="Agent's updated strategy based on analysis")
    speaking_position: int = Field(..., description="Position in speaking order for this round (1=first, etc.)")


class AgentMemory(BaseModel):
    """Complete memory system for an agent."""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    memory_entries: List[MemoryEntry] = Field(default_factory=list, description="Chronological memory entries")
    
    def add_memory(self, entry: MemoryEntry):
        """Add a new memory entry."""
        self.memory_entries.append(entry)
    
    def get_latest_memory(self) -> Optional[MemoryEntry]:
        """Get the most recent memory entry."""
        return self.memory_entries[-1] if self.memory_entries else None
    
    def get_strategy_evolution(self) -> List[str]:
        """Get the evolution of strategies over time."""
        return [entry.strategy_update for entry in self.memory_entries]


class DeliberationResponse(BaseModel):
    """Represents a single agent's response during deliberation."""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_name: str = Field(..., description="Human-readable agent name")
    public_message: str = Field(..., description="Agent's public communication to other agents")
    private_memory_entry: Optional[MemoryEntry] = Field(None, description="Agent's private memory update (if any)")
    updated_choice: PrincipleChoice = Field(..., description="Agent's current principle choice")
    round_number: int = Field(..., ge=0, description="Current deliberation round (0 for initial evaluation)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    speaking_position: int = Field(default=0, description="Position in speaking order (0 for initial eval, 1+ for rounds)")


class ConsensusResult(BaseModel):
    """Represents the result of consensus detection."""
    unanimous: bool = Field(..., description="Whether unanimous agreement was reached")
    agreed_principle: Optional[PrincipleChoice] = Field(None, description="Agreed principle if unanimous")
    dissenting_agents: List[str] = Field(default_factory=list, description="List of dissenting agent IDs")
    rounds_to_consensus: int = Field(..., ge=0, description="Number of rounds to reach consensus (0 if reached in initial evaluation)")
    total_messages: int = Field(..., ge=0, description="Total messages exchanged")


class ExperimentConfig(BaseModel):
    """Configuration for a single experiment run."""
    experiment_id: str = Field(..., description="Unique experiment identifier")
    num_agents: int = Field(..., ge=3, le=50, description="Number of participating agents")
    max_rounds: int = Field(default=10, ge=1, description="Maximum deliberation rounds")
    decision_rule: str = Field(default="unanimity", description="Decision rule (unanimity/majority)")
    timeout_seconds: int = Field(default=300, ge=30, description="Timeout per round in seconds")
    models: List[str] = Field(default_factory=list, description="LLM models to use for agents")
    personalities: List[str] = Field(default_factory=list, description="Agent personalities (custom text or references)")


class PerformanceMetrics(BaseModel):
    """Performance metrics for an experiment."""
    total_duration_seconds: float = Field(..., description="Total experiment duration")
    average_round_duration: float = Field(..., description="Average time per round")
    errors_encountered: int = Field(default=0, description="Number of errors encountered")


class FeedbackResponse(BaseModel):
    """Individual agent feedback after experiment completion."""
    agent_id: str = Field(..., description="Agent identifier")
    agent_name: str = Field(..., description="Agent name")
    satisfaction_rating: int = Field(..., ge=1, le=10, description="Satisfaction with group choice (1-10)")
    fairness_rating: int = Field(..., ge=1, le=10, description="Perceived fairness of chosen principle (1-10)")
    would_choose_again: bool = Field(..., description="Whether agent would make same choice again")
    alternative_preference: Optional[int] = Field(None, ge=1, le=4, description="Alternative principle preference if any")
    reasoning: str = Field(..., description="Agent's reasoning for their feedback")
    confidence_in_feedback: float = Field(default=0.7, description="Agent's confidence in their feedback (0.0-1.0)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Feedback timestamp")


class ExperimentResults(BaseModel):
    """Complete results of an experiment."""
    experiment_id: str = Field(..., description="Unique experiment identifier")
    configuration: ExperimentConfig = Field(..., description="Experiment configuration")
    deliberation_transcript: List[DeliberationResponse] = Field(default_factory=list, description="Full conversation transcript")
    agent_memories: List[AgentMemory] = Field(default_factory=list, description="Private agent memories")
    speaking_orders: List[List[str]] = Field(default_factory=list, description="Speaking order for each round")
    consensus_result: ConsensusResult = Field(..., description="Consensus outcome")
    feedback_responses: List[FeedbackResponse] = Field(default_factory=list, description="Post-experiment feedback")
    performance_metrics: PerformanceMetrics = Field(..., description="Performance data")
    start_time: datetime = Field(default_factory=datetime.now, description="Experiment start time")
    end_time: Optional[datetime] = Field(None, description="Experiment end time")


# Principle definitions for easy reference
DISTRIBUTIVE_JUSTICE_PRINCIPLES = {
    1: {
        "name": "Maximize the Minimum Income",
        "description": "The principle that ensures the worst-off member of society is as well-off as possible.",
        "short_name": "Minimum Focus"
    },
    2: {
        "name": "Maximize the Average Income", 
        "description": "The principle that ensures the greatest possible total income for the group, without regard for its distribution.",
        "short_name": "Average Focus"
    },
    3: {
        "name": "Maximize the Average Income with a Floor Constraint",
        "description": "A hybrid principle that establishes a minimum guaranteed income (a 'safety net') for everyone, and then maximizes the average income.",
        "short_name": "Floor Constraint"
    },
    4: {
        "name": "Maximize the Average Income with a Range Constraint",
        "description": "A hybrid principle that limits the gap between the richest and poorest members, and then maximizes the average income.",
        "short_name": "Range Constraint"
    }
}


def get_principle_by_id(principle_id: int) -> dict:
    """Get principle information by ID."""
    return DISTRIBUTIVE_JUSTICE_PRINCIPLES.get(principle_id, {})


def get_all_principles_text() -> str:
    """Get formatted text of all principles for agent instructions."""
    principles_text = "There are 4 principles of distributive justice:\n\n"
    for pid, principle in DISTRIBUTIVE_JUSTICE_PRINCIPLES.items():
        principles_text += f"{pid}. {principle['name']}: {principle['description']}\n\n"
    return principles_text


def detect_consensus(deliberation_responses: List[DeliberationResponse]) -> ConsensusResult:
    """
    Detect consensus by checking if all agents have the same principle_id.
    This is a simple code-based approach that doesn't rely on LLM assessment.
    
    Args:
        deliberation_responses: List of agent responses to analyze
        
    Returns:
        ConsensusResult indicating whether consensus was reached
    """
    if not deliberation_responses:
        return ConsensusResult(
            unanimous=False,
            agreed_principle=None,
            dissenting_agents=[],
            rounds_to_consensus=0,
            total_messages=0
        )
    
    # Get the latest response from each agent
    latest_responses = {}
    for response in deliberation_responses:
        latest_responses[response.agent_id] = response
    
    if not latest_responses:
        return ConsensusResult(
            unanimous=False,
            agreed_principle=None,
            dissenting_agents=[],
            rounds_to_consensus=0,
            total_messages=len(deliberation_responses)
        )
    
    # Check if all agents have the same principle_id
    principle_ids = [resp.updated_choice.principle_id for resp in latest_responses.values()]
    
    if len(set(principle_ids)) == 1:
        # Consensus reached - all agents chose the same principle
        consensus_principle_id = principle_ids[0]
        # Get the principle choice from any agent (they're all the same)
        sample_response = next(iter(latest_responses.values()))
        agreed_principle = sample_response.updated_choice
        
        # Calculate rounds to consensus
        max_round = max(resp.round_number for resp in latest_responses.values())
        
        return ConsensusResult(
            unanimous=True,
            agreed_principle=agreed_principle,
            dissenting_agents=[],
            rounds_to_consensus=max_round,
            total_messages=len(deliberation_responses)
        )
    else:
        # No consensus - find dissenting agents
        most_common_principle = max(set(principle_ids), key=principle_ids.count)
        dissenting_agents = [
            agent_id for agent_id, resp in latest_responses.items()
            if resp.updated_choice.principle_id != most_common_principle
        ]
        
        return ConsensusResult(
            unanimous=False,
            agreed_principle=None,
            dissenting_agents=dissenting_agents,
            rounds_to_consensus=0,
            total_messages=len(deliberation_responses)
        )


def get_default_personality() -> str:
    """Get the default personality for agents."""
    return "You are an agent tasked to design a future society."