from hashlib import sha256

from app.domain.evidence import EvidenceState
from app.domain.intent import ParsedEngineeringIntent, ParsedField
from app.pipeline.builder import build_engineering_spec
from app.pipeline.normalizer import canonical_field, normalize_length
from app.providers.prompt import SYSTEM_PROMPT
from benchmarks import BENCHMARK_V022, BENCHMARK_V023


BASELINE_001_PROMPT_HASH = "ca2dab42a10ad69812dcc30ac565f2830d76fc55fb4ba5e2c66faad9119a3e4d"


def _intent(**overrides):
    unknown = {
        "raw_value": None,
        "raw_unit": None,
        "source_text": None,
        "state": "unknown",
        "confidence": 0.0,
    }
    payload = {
        name: dict(unknown)
        for name in [
            "component",
            "pipe_diameter",
            "nominal_pipe_size",
            "wall_thickness",
            "bracket_width",
            "base_thickness",
            "fastener_designation",
            "fastener_count",
            "hole_count",
            "hole_diameter",
            "hole_semantics",
            "material",
            "manufacturing_process",
            "load_statement",
        ]
    }
    payload["qualitative_requirements"] = []
    payload["unmapped_phrases"] = []
    payload.update(overrides)
    return ParsedEngineeringIntent.model_validate(payload)


def test_prompt_v1_is_byte_for_byte_frozen_from_baseline_001():
    digest = sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest()
    assert digest == BASELINE_001_PROMPT_HASH


def test_frozen_v022_and_calibrated_v023_keep_same_case_ids_and_prompts():
    assert [c["id"] for c in BENCHMARK_V022] == [c["id"] for c in BENCHMARK_V023]
    assert [c["prompt"] for c in BENCHMARK_V022] == [c["prompt"] for c in BENCHMARK_V023]


def test_unknown_invariant_removes_value_unit_and_confidence():
    field = ParsedField.model_validate(
        {
            "raw_value": "lightweight and strong",
            "raw_unit": "mm",
            "source_text": "lightweight and strong",
            "state": "unknown",
            "confidence": 0.9,
        }
    )
    assert field.raw_value is None
    assert field.raw_unit is None
    assert field.confidence == 0.0


def test_missing_length_unit_is_not_assumed_to_be_mm():
    intent = _intent(
        component={
            "raw_value": "bracket",
            "raw_unit": None,
            "source_text": "bracket",
            "state": "confirmed",
            "confidence": 1.0,
        },
        pipe_diameter={
            "raw_value": 50,
            "raw_unit": None,
            "source_text": "Ø50",
            "state": "confirmed",
            "confidence": 1.0,
        },
    )
    spec = build_engineering_spec("Create a bracket for Ø50.", intent)
    assert spec.pipe_diameter.state == EvidenceState.UNKNOWN
    assert any("no explicit unit" in warning for warning in spec.warnings)


def test_textual_number_and_unit_alias_normalize_deterministically():
    field = ParsedField(
        raw_value="fifty",
        raw_unit="millimetres",
        source_text="fifty millimetres",
        state="confirmed",
        confidence=1.0,
    )
    assert normalize_length(field) == (50.0, "mm")


def test_decimal_comma_normalizes_deterministically():
    field = ParsedField(
        raw_value="6,6",
        raw_unit="mm",
        source_text="6,6 mm",
        state="confirmed",
        confidence=1.0,
    )
    assert normalize_length(field) == (6.6, "mm")


def test_component_aliases_are_semantically_equal():
    expected = ParsedField(raw_value="pipe_bracket", state="confirmed", confidence=1.0)
    actual = ParsedField(raw_value="pipe bracket", state="confirmed", confidence=1.0)
    assert canonical_field("component", expected) == canonical_field("component", actual)


def test_hole_count_does_not_create_fastener_count():
    case = next(c for c in BENCHMARK_V023 if c["id"] == "B15")
    intent = ParsedEngineeringIntent.model_validate(case["parsed_intent"])
    spec = build_engineering_spec(case["prompt"], intent)
    assert spec.hole_count.value == 2
    assert spec.fastener_count.state == EvidenceState.UNKNOWN
