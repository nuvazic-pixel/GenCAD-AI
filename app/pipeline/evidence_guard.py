from __future__ import annotations

import re
from typing import Iterable

from pydantic import BaseModel, Field

from app.domain.intent import ParsedEngineeringIntent, ParsedField
from app.pipeline.normalizer import normalize_text, normalize_unit


LENGTH_FIELDS = (
    "pipe_diameter",
    "wall_thickness",
    "bracket_width",
    "base_thickness",
    "hole_diameter",
)

UNIT_EVIDENCE = {
    "mm": ("mm", "millimeter", "millimeters", "millimetre", "millimetres"),
    "cm": ("cm", "centimeter", "centimeters", "centimetre", "centimetres"),
    "m": ("m", "meter", "meters", "metre", "metres"),
}


class EvidenceGuardFinding(BaseModel):
    field: str
    action: str
    reason: str
    raw_value: str | int | float | None = None
    raw_unit: str | None = None
    source_text: str | None = None


class EvidenceGuardReport(BaseModel):
    findings: list[EvidenceGuardFinding] = Field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.findings)


def _contains_token(text: str, token: str) -> bool:
    escaped = re.escape(token)
    return re.search(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", text, re.IGNORECASE) is not None


def unit_supported_by_source(field: ParsedField) -> bool:
    if field.raw_unit is None:
        return True

    unit = normalize_unit(field.raw_unit)
    if unit not in UNIT_EVIDENCE:
        # Unknown units are outside this length guard's authority.
        return True

    # Safety rule: a model-provided unit must be visible in the field-level
    # source phrase. We deliberately do not search the full prompt because an
    # unrelated "mm" elsewhere must not justify "Ø42 -> 42 mm".
    source = normalize_text(field.source_text)
    if not source:
        return False

    return any(_contains_token(source, token) for token in UNIT_EVIDENCE[unit])


def apply_source_evidence_guard(
    prompt: str,
    intent: ParsedEngineeringIntent,
) -> tuple[ParsedEngineeringIntent, EvidenceGuardReport]:
    del prompt  # reserved for future evidence checks; field-level evidence is stricter for units.

    payload = intent.model_dump(mode="python")
    findings: list[EvidenceGuardFinding] = []

    for field_name in LENGTH_FIELDS:
        field = getattr(intent, field_name)
        if field.state == "unknown" or field.raw_unit is None:
            continue

        if not unit_supported_by_source(field):
            findings.append(
                EvidenceGuardFinding(
                    field=field_name,
                    action="strip_unsupported_unit",
                    reason="raw_unit is not supported by the field-level source_text",
                    raw_value=field.raw_value,
                    raw_unit=str(field.raw_unit),
                    source_text=field.source_text,
                )
            )
            payload[field_name]["raw_unit"] = None

    guarded = ParsedEngineeringIntent.model_validate(payload)
    return guarded, EvidenceGuardReport(findings=findings)


def relation_supports_hole_association(
    prompt: str,
    designation: str | None,
) -> bool:
    if not designation:
        return False

    text = normalize_text(prompt)
    d = re.escape(normalize_text(designation))

    # Split on sentence punctuation, but do not split decimal numbers such as 6.6.
    segments = [
        segment.strip()
        for segment in re.split(r"(?<!\\d)[.!?](?!\\d)", text)
        if segment.strip()
    ]

    direct_pattern = re.compile(
        rf"\\b{d}\\b\\s+"
        rf"(?:(?:clearance|threaded|mounting|befestigungs|gewinde|durchgangs)\\s+)?"
        rf"\\b(?:hole|holes|bohrung|bohrungen)\\b",
        re.IGNORECASE,
    )
    relation_pattern = re.compile(
        rf"\\b{d}\\b.{{0,40}}"
        rf"\\b(?:screw|screws|bolt|bolts|schraube|schrauben)\\b"
        rf".{{0,60}}\\b(?:through|into|durch|in)\\b"
        rf".{{0,80}}\\b(?:hole|holes|bohrung|bohrungen)\\b",
        re.IGNORECASE,
    )

    return any(
        direct_pattern.search(segment) or relation_pattern.search(segment)
        for segment in segments
    )


def unexpected_association_is_supported(
    prompt: str,
    intent: ParsedEngineeringIntent,
) -> bool:
    actual = intent.associated_fastener_designation
    if actual.state == "unknown" or actual.raw_value is None:
        return False

    physical = intent.fastener_designation
    if physical.state == "unknown" or physical.raw_value is None:
        # Direct M6-hole wording may legitimately populate only the associated field.
        return relation_supports_hole_association(prompt, str(actual.raw_value))

    same_designation = (
        normalize_text(actual.raw_value) == normalize_text(physical.raw_value)
    )
    return same_designation and relation_supports_hole_association(
        prompt,
        str(actual.raw_value),
    )
