"""
Pydantic schemas for structured outputs across the agent system
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class PlanStep(BaseModel):
    """A single step in the research plan"""
    step_number: int
    description: str
    tool_required: Optional[str] = None
    reasoning: str


class ResearchPlan(BaseModel):
    """Complete research plan with steps"""
    question: str
    steps: List[PlanStep]
    estimated_time: str = "2-3 minutes"


class ToolExecution(BaseModel):
    """Record of a tool being executed"""
    tool_name: str
    executed: bool
    output_summary: Optional[str] = None
    error: Optional[str] = None


class ExecutionTrace(BaseModel):
    """Complete trace of execution"""
    plan: ResearchPlan
    tools_executed: List[ToolExecution]
    final_answer: str
    execution_time_seconds: float


class EvaluationResult(BaseModel):
    """Evaluation of an execution"""
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    required_tools_used: bool
    correct_sequence_followed: bool
    answer_supported_by_data: bool
    feedback: str
    issues: List[str] = Field(default_factory=list)


class MistakeType(str):
    """Types of mistakes the agent can make"""
    TOOL_SKIPPED = "TOOL_SKIPPED"
    WRONG_ORDER = "WRONG_ORDER"
    PREMATURE_ANSWER = "PREMATURE_ANSWER"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"


class Mistake(BaseModel):
    """A recorded mistake"""
    mistake_type: str
    description: str
    corrective_rule: str
    frequency: int = 1
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    question: str


class LearningRule(BaseModel):
    """A behavioral constraint learned from mistakes"""
    rule_id: str
    rule_text: str
    applies_to: str  # "planning" or "execution"
    priority: int = Field(ge=1, le=10)


class MemorySnapshot(BaseModel):
    """Snapshot of agent's memory"""
    mistakes: List[Mistake]
    version: str = "1.0"
    total_runs: int = 0
    successful_runs: int = 0


class SearchResult(BaseModel):
    """A single search result"""
    title: str
    snippet: str
    url: str


class SummaryOutput(BaseModel):
    """Summarization output"""
    key_points: List[str]
    main_topic: str
    confidence: Literal["high", "medium", "low"]
