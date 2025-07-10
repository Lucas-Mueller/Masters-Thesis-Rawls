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
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0-1)")


class DeliberationResponse(BaseModel):
    """Represents a single agent's response during deliberation."""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_name: str = Field(..., description="Human-readable agent name")
    message: str = Field(..., description="Agent's deliberation message")
    updated_choice: PrincipleChoice = Field(..., description="Agent's current principle choice")
    round_number: int = Field(..., ge=0, description="Current deliberation round (0 for initial evaluation)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


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


class PerformanceMetrics(BaseModel):
    """Performance metrics for an experiment."""
    total_duration_seconds: float = Field(..., description="Total experiment duration")
    average_round_duration: float = Field(..., description="Average time per round")
    total_tokens_used: int = Field(default=0, description="Total tokens consumed")
    api_calls_made: int = Field(default=0, description="Total API calls made")
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
    confidence_in_feedback: float = Field(..., ge=0.0, le=1.0, description="Confidence in feedback responses")
    timestamp: datetime = Field(default_factory=datetime.now, description="Feedback timestamp")


class ExperimentResults(BaseModel):
    """Complete results of an experiment."""
    experiment_id: str = Field(..., description="Unique experiment identifier")
    configuration: ExperimentConfig = Field(..., description="Experiment configuration")
    deliberation_transcript: List[DeliberationResponse] = Field(default_factory=list, description="Full conversation transcript")
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
        "short_name": "Rawlsian"
    },
    2: {
        "name": "Maximize the Average Income", 
        "description": "The principle that ensures the greatest possible total income for the group, without regard for its distribution.",
        "short_name": "Utilitarian"
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