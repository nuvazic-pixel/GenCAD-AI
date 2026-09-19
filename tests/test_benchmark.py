import pytest
from app.domain.intent import ParsedEngineeringIntent
from app.domain.evidence import EvidenceState
from app.parsers.mock import MockParser
from app.pipeline.builder import build_engineering_spec
from app.pipeline.validation import validate_spec
from benchmarks import BENCHMARK


@pytest.mark.parametrize("case",BENCHMARK,ids=[c["id"] for c in BENCHMARK])
def test_benchmark_case(case):
    parsed=ParsedEngineeringIntent.model_validate(case["parsed_intent"])
    spec=build_engineering_spec(case["prompt"],MockParser(parsed).parse(case["prompt"]))
    report=validate_spec(spec)
    assert report.status.value==case["expected_status"]
    assert report.expected_stage==case["expected_stage"]
    if "expected_normalized" in case and "pipe_diameter_mm" in case["expected_normalized"]:
        assert spec.pipe_diameter.value is not None
        assert spec.pipe_diameter.value.value_mm==case["expected_normalized"]["pipe_diameter_mm"]
    for _,value in spec:
        if hasattr(value,"state"):
            assert value.state!=EvidenceState.DERIVED


def test_dn50_is_not_silently_converted_to_50mm():
    c=next(c for c in BENCHMARK if c["id"]=="B06")
    spec=build_engineering_spec(c["prompt"],ParsedEngineeringIntent.model_validate(c["parsed_intent"]))
    assert spec.nominal_pipe_size.value=="DN50"
    assert spec.pipe_diameter.state==EvidenceState.UNKNOWN


def test_probably_aluminium_remains_hypothesis():
    c=next(c for c in BENCHMARK if c["id"]=="B09")
    spec=build_engineering_spec(c["prompt"],ParsedEngineeringIntent.model_validate(c["parsed_intent"]))
    assert spec.material.state==EvidenceState.HYPOTHESIS


def test_m6_clearance_is_not_derived_by_builder():
    c=next(c for c in BENCHMARK if c["id"]=="B14")
    spec=build_engineering_spec(c["prompt"],ParsedEngineeringIntent.model_validate(c["parsed_intent"]))
    assert spec.fastener_designation.value=="M6"
    assert spec.hole_semantics.value=="clearance"
    assert spec.clearance_hole_diameter.state==EvidenceState.UNKNOWN
