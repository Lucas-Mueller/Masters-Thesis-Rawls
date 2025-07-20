"""
Data models for the Multi-Agent Distributive Justice Experiment.
All models use Pydantic for validation and structure.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LikertScale(str, Enum):
    """4-point Likert scale for principle evaluation."""
    STRONGLY_DISAGREE = "strongly_disagree"
    DISAGREE = "disagree"
    AGREE = "agree"
    STRONGLY_AGREE = "strongly_agree"
    
    def to_numeric(self) -> int:
        """Convert to numeric scale for analysis (1-4)."""
        mapping = {
            "strongly_disagree": 1,
            "disagree": 2,
            "agree": 3,
            "strongly_agree": 4
        }
        return mapping[self.value]
    
    def to_display(self) -> str:
        """Convert to human-readable display format."""
        mapping = {
            "strongly_disagree": "Strongly Disagree",
            "disagree": "Disagree",
            "agree": "Agree",
            "strongly_agree": "Strongly Agree"
        }
        return mapping[self.value]


class PublicHistoryMode(str, Enum):
    """Public history mode for experiments."""
    FULL = "full"
    SUMMARIZED = "summarized"


class IncomeClass(str, Enum):
    """Income classes for economic simulation."""
    HIGH = "High"
    MEDIUM_HIGH = "Medium high"
    MEDIUM = "Medium"
    MEDIUM_LOW = "Medium low"
    LOW = "Low"


class CertaintyLevel(str, Enum):
    """5-point certainty scale for preference rankings."""
    VERY_UNSURE = "very_unsure"
    UNSURE = "unsure"
    NO_OPINION = "no_opinion"
    SURE = "sure"
    VERY_SURE = "very_sure"
    
    def to_display(self) -> str:
        """Convert to human-readable display format."""
        mapping = {
            "very_unsure": "Very Unsure",
            "unsure": "Unsure",
            "no_opinion": "No Opinion",
            "sure": "Sure",
            "very_sure": "Very Sure"
        }
        return mapping[self.value]


class SummaryAgentConfig(BaseModel):
    """Configuration for the summary agent."""
    model: str = Field(default="gpt-4.1-mini", description="Model to use for summary generation")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Temperature for summary generation")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="Maximum tokens for summaries")


class RoundSummary(BaseModel):
    """Summary of a completed deliberation round."""
    round_number: int = Field(..., ge=1, description="Round number")
    summary_text: str = Field(..., description="Generated summary text")
    key_arguments: Dict[str, str] = Field(default_factory=dict, description="agent_name -> main_argument")
    principle_preferences: Dict[str, List[str]] = Field(default_factory=dict, description="principle -> supporting_agents")
    consensus_status: str = Field(..., description="Consensus status description")
    timestamp: datetime = Field(default_factory=datetime.now, description="Summary generation timestamp")
    summary_agent_model: str = Field(..., description="Model used for summary generation")


class AgentConfig(BaseModel):
    """Configuration for a single agent."""
    name: Optional[str] = Field(None, description="Human-readable name for the agent")
    personality: Optional[str] = Field(None, description="Agent's personality/role description")
    model: Optional[str] = Field(None, description="LLM model to use for this agent")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature setting for this agent (0.0-2.0)")


class DefaultConfig(BaseModel):
    """Default values for agent properties when not specified."""
    personality: str = Field(
        default="You are an agent tasked to design a future society.",
        description="Default personality for agents"
    )
    model: str = Field(
        default="gpt-4.1-nano",
        description="Default LLM model for agents"
    )
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Default temperature for agents (0.0-2.0)")


class LoggingConfig(BaseModel):
    """Configuration for experiment logging."""
    enabled: bool = Field(default=True, description="Enable comprehensive logging")
    capture_raw_inputs: bool = Field(default=True, description="Log full prompts sent to agents")
    capture_raw_outputs: bool = Field(default=True, description="Log complete LLM responses")
    capture_memory_context: bool = Field(default=True, description="Log memory contexts provided to agents")
    capture_memory_steps: bool = Field(default=True, description="Log decomposed memory steps (if using decomposed strategy)")
    include_processing_times: bool = Field(default=True, description="Include timing information for all operations")


class OutputConfig(BaseModel):
    """Configuration for experiment output."""
    directory: str = Field(default="experiment_results", description="Output directory for experiment files")
    formats: List[str] = Field(default=["json", "csv", "txt"], description="Export formats")
    include_feedback: bool = Field(default=True, description="Include feedback in export")
    include_transcript: bool = Field(default=True, description="Include transcript in export")


class PrincipleChoice(BaseModel):
    """Represents an agent's choice of distributive justice principle."""
    principle_id: int = Field(..., ge=1, le=4, description="Principle ID (1-4)")
    principle_name: str = Field(..., description="Name of the chosen principle")
    reasoning: str = Field(..., description="Agent's reasoning for this choice")
    floor_constraint: Optional[int] = Field(None, description="Floor constraint amount for principle 3")
    range_constraint: Optional[int] = Field(None, description="Range constraint amount for principle 4")


class IncomeDistribution(BaseModel):
    """Represents a single income distribution scenario."""
    distribution_id: int = Field(..., description="Unique identifier for this distribution")
    name: str = Field(..., description="Human-readable name for this distribution")
    income_by_class: Dict[IncomeClass, int] = Field(..., description="Mapping of income classes to dollar amounts")


class EconomicOutcome(BaseModel):
    """Tracks economic outcome for an agent in a single round."""
    agent_id: str = Field(..., description="Agent identifier")
    round_number: int = Field(..., ge=1, description="Round number (1-4 for individual rounds)")
    chosen_principle: int = Field(..., ge=1, le=4, description="Principle chosen by agent")
    assigned_income_class: IncomeClass = Field(..., description="Randomly assigned income class")
    actual_income: int = Field(..., description="Actual income earned based on distribution")
    payout_amount: float = Field(..., description="Payout amount (actual_income * payout_ratio)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Outcome timestamp")


class PreferenceRanking(BaseModel):
    """Agent's preference ranking of principles with certainty level."""
    agent_id: str = Field(..., description="Agent identifier")
    rankings: List[int] = Field(..., description="Principle rankings [1,2,3,4] where 1=best, 4=worst", min_length=4, max_length=4)
    certainty_level: CertaintyLevel = Field(..., description="Agent's certainty about their ranking")
    reasoning: str = Field(..., description="Agent's reasoning for their ranking")
    phase: str = Field(..., description="Phase when ranking was collected (initial, post_individual, post_group)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Ranking timestamp")


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
    max_rounds: int = Field(default=10, ge=1, description="Maximum deliberation rounds")
    decision_rule: str = Field(default="unanimity", description="Decision rule (unanimity/majority)")
    timeout_seconds: int = Field(default=300, ge=30, description="Timeout per round in seconds")
    agents: List[AgentConfig] = Field(..., description="List of agent configurations")
    defaults: DefaultConfig = Field(default_factory=DefaultConfig, description="Default values for agent properties")
    global_temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Global temperature setting for all agents (0.0-2.0)")
    memory_strategy: str = Field(default="decomposed", description="Memory strategy: recent|decomposed")
    public_history_mode: PublicHistoryMode = Field(default=PublicHistoryMode.FULL, description="Public history mode: full|summarized")
    summary_agent: SummaryAgentConfig = Field(default_factory=SummaryAgentConfig, description="Summary agent configuration")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")
    output: OutputConfig = Field(default_factory=OutputConfig, description="Output configuration")
    
    # New game logic configuration
    income_distributions: List[IncomeDistribution] = Field(default_factory=list, description="Available income distribution scenarios")
    payout_ratio: float = Field(default=0.0001, description="Payout ratio: dollars earned per $1 of income (default: $1 per $10,000)")
    individual_rounds: int = Field(default=4, ge=1, description="Number of individual application rounds in Phase 1")
    enable_detailed_examples: bool = Field(default=True, description="Enable detailed income distribution examples")
    enable_secret_ballot: bool = Field(default=True, description="Enable secret ballot voting in Phase 2")
    
    @property
    def num_agents(self) -> int:
        """Number of participating agents (derived from agents list)."""
        return len(self.agents)


class PerformanceMetrics(BaseModel):
    """Performance metrics for an experiment."""
    total_duration_seconds: float = Field(..., description="Total experiment duration")
    average_round_duration: float = Field(..., description="Average time per round")
    errors_encountered: int = Field(default=0, description="Number of errors encountered")


class PrincipleEvaluation(BaseModel):
    """Evaluation of a single principle using Likert scale."""
    principle_id: int = Field(..., ge=1, le=4, description="Principle ID (1-4)")
    principle_name: str = Field(..., description="Name of the principle")
    satisfaction_rating: LikertScale = Field(..., description="Satisfaction rating on 4-point Likert scale")
    reasoning: str = Field(..., description="Agent's reasoning for this rating")
    timestamp: datetime = Field(default_factory=datetime.now, description="Evaluation timestamp")


class AgentEvaluationResponse(BaseModel):
    """Complete evaluation response from an agent for all principles."""
    agent_id: str = Field(..., description="Agent identifier")
    agent_name: str = Field(..., description="Agent name")
    principle_evaluations: List[PrincipleEvaluation] = Field(..., description="Evaluations for all 4 principles")
    overall_reasoning: str = Field(..., description="Agent's overall reasoning for their ratings")
    evaluation_duration: Optional[float] = Field(None, description="Time taken for evaluation in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class FeedbackResponse(BaseModel):
    """Individual agent feedback after experiment completion."""
    agent_id: str = Field(..., description="Agent identifier")
    agent_name: str = Field(..., description="Agent name")
    satisfaction_rating: int = Field(..., ge=1, le=10, description="Satisfaction with group choice (1-10)")
    fairness_rating: int = Field(..., ge=1, le=10, description="Perceived fairness of chosen principle (1-10)")
    would_choose_again: bool = Field(..., description="Whether agent would make same choice again")
    alternative_preference: Optional[int] = Field(None, ge=1, le=4, description="Alternative principle preference if any")
    reasoning: str = Field(..., description="Agent's reasoning for their feedback")
    timestamp: datetime = Field(default_factory=datetime.now, description="Feedback timestamp")


class ExperimentResults(BaseModel):
    """Complete results of an experiment."""
    experiment_id: str = Field(..., description="Unique experiment identifier")
    configuration: ExperimentConfig = Field(..., description="Experiment configuration")
    deliberation_transcript: List[DeliberationResponse] = Field(default_factory=list, description="Full conversation transcript")
    agent_memories: List[AgentMemory] = Field(default_factory=list, description="Private agent memories")
    speaking_orders: List[List[str]] = Field(default_factory=list, description="Speaking order for each round")
    round_summaries: List[RoundSummary] = Field(default_factory=list, description="AI-generated summaries of each round")
    consensus_result: ConsensusResult = Field(..., description="Consensus outcome")
    initial_evaluation_responses: List[AgentEvaluationResponse] = Field(default_factory=list, description="Initial Likert scale assessments (before deliberation)")
    evaluation_responses: List[AgentEvaluationResponse] = Field(default_factory=list, description="Post-consensus principle evaluations")
    feedback_responses: List[FeedbackResponse] = Field(default_factory=list, description="Post-experiment feedback (legacy)")
    performance_metrics: PerformanceMetrics = Field(..., description="Performance data")
    start_time: datetime = Field(default_factory=datetime.now, description="Experiment start time")
    end_time: Optional[datetime] = Field(None, description="Experiment end time")


# Principle definitions for easy reference
DISTRIBUTIVE_JUSTICE_PRINCIPLES = {
    1: {
        "name": "MAXIMIZING THE FLOOR INCOME",
        "description": "The most just distribution of income is that which maximizes the floor (or lowest) income in the society. This principle considers only the welfare of the worst-off individual in society. In judging among income distributions, the distribution which ensures the poorest person the highest income is the most just. No person's income can go up unless it increases the income of the people at the very bottom.",
        "short_name": "Floor Income",
        "requires_parameter": False
    },
    2: {
        "name": "MAXIMIZING THE AVERAGE INCOME", 
        "description": "The most just distribution of income is that which maximizes the average income in the society. For any society maximizing the average income maximizes the total income in the society.",
        "short_name": "Average Income",
        "requires_parameter": False
    },
    3: {
        "name": "MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT",
        "description": "The most just distribution of income is that which maximizes the average income only after a certain specified minimum income is guaranteed to everyone. Such a principle ensures that the attempt to maximize the average is constrained so as to ensure that individuals \"at the bottom\" receive a specified minimum. To choose this principle one must specify the value of the floor (lowest income).",
        "short_name": "Floor Constraint",
        "requires_parameter": True,
        "parameter_type": "floor_amount"
    },
    4: {
        "name": "MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT",
        "description": "The most just distribution of income is that which attempts to maximize the average income only after guaranteeing that the difference between the poorest and the richest individuals (i.e., the range of income) in the society is not greater than a specified amount. Such a principle ensures that the attempt to maximize the average does not allow income differences between rich and poor to exceed a specified amount. To choose this principle one must specify the dollar difference between the high and low incomes.",
        "short_name": "Range Constraint",
        "requires_parameter": True,
        "parameter_type": "range_amount"
    }
}


def get_principle_by_id(principle_id: int) -> dict:
    """Get principle information by ID."""
    return DISTRIBUTIVE_JUSTICE_PRINCIPLES.get(principle_id, {})


def get_principle_name(principle_id: int) -> str:
    """Get principle name by ID."""
    principle = get_principle_by_id(principle_id)
    return principle.get("name", f"Unknown Principle {principle_id}")


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


def is_openai_model(model_name: str) -> bool:
    """
    Check if a model name corresponds to an OpenAI model.
    
    Args:
        model_name: The model name to check
        
    Returns:
        True if the model is from OpenAI, False otherwise
    """
    if not model_name:
        return False
    
    model_name = model_name.lower().strip()
    
    # Official OpenAI model patterns
    openai_models = {
        "gpt-4", "gpt-4-32k", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
        "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.5",
        "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-instruct",
        "o1", "o1-mini", "o1-preview", "o3", "o3-mini", "o4-mini",
        "gpt-image-1", "sora"
    }
    
    return model_name in openai_models


def all_models_are_openai(config: 'ExperimentConfig') -> bool:
    """
    Check if all models in an experiment configuration are OpenAI models.
    
    Args:
        config: The experiment configuration to check
        
    Returns:
        True if all models are OpenAI models, False otherwise
    """
    # Check all agent models
    for agent in config.agents:
        model_name = agent.model or config.defaults.model
        if not is_openai_model(model_name):
            return False
    
    return True