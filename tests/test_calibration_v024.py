from hashlib import sha256

from app.domain.evidence import EvidenceState
from app.domain.intent import ParsedEngineeringIntent
from app.pipeline.builder import build_engineering_spec
from app.pipeline.validation import validate_spec
from app.providers.prompt import SYSTEM_PROMPT
from benchmarks import BENCHMARK_V023, BENCHMARK_V024


PROMPT_V1_HASH = "ca2dab42a10ad69812dcc30ac565f2830d76fc55fb4ba5e2c66faad9119a3e4d"


def _case(case_id):
    return next(case for case in BENCHMARK_V024 if case["id"] == case_id)


def test_prompt_v1_remains_frozen_for_v024():
    assert sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest() == PROMPT_V1_HASH


def test_v023_and_v024_keep_identical_case_ids_and_prompts():
    assert [c["id"] for c in BENCHMARK_V023] == [c["id"] for c in BENCHMARK_V024]
    assert [c["prompt"] for c in BENCHMARK_V023] == [c["prompt"] for c in BENCHMARK_V024]


def test_m6_hole_designation_does_not_assert_physical_fastener():
    case = _case("B02")
    intent = ParsedEngineeringIntent.model_validate(case["parsed_intent"])

    assert intent.associated_fastener_designation.raw_value == "M6"
    assert intent.fastener_designation.state == "unknown"
    assert intent.hole_count.raw_value == 2


def test_explicit_screws_remain_physical_fastener_fields():
    case = _case("B10")
    intent = ParsedEngineeringIntent.model_validate(case["parsed_intent"])

    assert intent.fastener_designation.raw_value == "M6"
    assert intent.fastener_designation.state == "hypothesis"
    assert intent.fastener_count.raw_value == 2
    assert intent.fastener_count.state == "hypothesis"
    assert intent.associated_fastener_designation.state == "unknown"


def test_positive_control_ready_without_physical_fastener_specification():
    case = _case("P04")
    intent = ParsedEngineeringIntent.model_validate(case["parsed_intent"])
    spec = build_engineering_spec(case["prompt"], intent)
    report = validate_spec(spec)

    assert spec.fastener_designation.state == EvidenceState.UNKNOWN
    assert spec.fastener_count.state == EvidenceState.UNKNOWN
    assert spec.associated_fastener_designation.value == "M6"
    assert spec.hole_count.value == 2
    assert spec.hole_diameter.value is not None
    assert spec.hole_diameter.value.value_mm == 6.6
    assert report.status.value == "ready"


def test_b17_bracket_component_is_explicit_in_bracket_width_phrase():
    case = _case("B17")
    intent = ParsedEngineeringIntent.model_validate(case["parsed_intent"])

    assert intent.component.state == "confirmed"
    assert intent.component.raw_value == "bracket"
