from pydantic import BaseModel, Field


class CaseMetrics(BaseModel):
    case_id: str
    expected_status: str
    actual_status: str
    explicit_fact_total: int = 0
    explicit_fact_correct: int = 0
    hallucinated_fields: int = 0
    hallucination_opportunities: int = 0
    uncertainty_total: int = 0
    uncertainty_preserved: int = 0
    semantic_traps: int = 0
    semantic_confusions: int = 0
    unsafe_proceed: bool = False
    correct_ready: bool = False
    notes: list[str] = Field(default_factory=list)


class BenchmarkSummary(BaseModel):
    model: str
    case_count: int

    explicit_fact_recall: float
    hallucinated_field_rate: float
    uncertainty_preservation: float
    semantic_confusion_rate: float
    unsafe_proceed_rate: float

    expected_ready_cases: int
    correct_ready_cases: int
    correct_ready_rate: float

    release_gate_passed: bool
