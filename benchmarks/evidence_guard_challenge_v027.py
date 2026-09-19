def _unknown():
    return {
        "raw_value": None,
        "raw_unit": None,
        "source_text": None,
        "state": "unknown",
        "confidence": 0.0,
    }


def _field(value=None, unit=None, text=None, state="confirmed", confidence=1.0):
    if state == "unknown":
        return _unknown()
    return {
        "raw_value": value,
        "raw_unit": unit,
        "source_text": text,
        "state": state,
        "confidence": confidence,
    }


def _intent(**overrides):
    fields = [
        "component",
        "pipe_diameter",
        "nominal_pipe_size",
        "wall_thickness",
        "bracket_width",
        "base_thickness",
        "fastener_designation",
        "fastener_count",
        "associated_fastener_designation",
        "hole_count",
        "hole_diameter",
        "hole_semantics",
        "material",
        "manufacturing_process",
        "load_statement",
    ]
    data = {name: _unknown() for name in fields}
    data["qualitative_requirements"] = []
    data["unmapped_phrases"] = []
    data.update(overrides)
    return data


CHALLENGE = [
    {
        "id": "EG01",
        "prompt": "Steel bracket for a Ø42 pipe; wall 4 mm, width 30 mm, base 6 mm, with two 6.6 mm holes.",
        "guard_targets": ["pipe_diameter"],
        "parsed_intent": _intent(
            component=_field("bracket", text="bracket"),
            pipe_diameter=_field(42, unit=None, text="Ø42 pipe"),
            wall_thickness=_field(4, unit="mm", text="wall 4 mm"),
            bracket_width=_field(30, unit="mm", text="width 30 mm"),
            base_thickness=_field(6, unit="mm", text="base 6 mm"),
            hole_count=_field(2, text="two"),
            hole_diameter=_field(6.6, unit="mm", text="6.6 mm holes"),
            material=_field("steel", text="Steel"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": [],
    },
    {
        "id": "EG02",
        "prompt": "Stahl-Rohrhalter für Ø48; Wand 3 mm, Breite 28 mm, Grundplatte 5 mm und zwei 6 mm Bohrungen.",
        "guard_targets": ["pipe_diameter"],
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="Stahl-Rohrhalter"),
            pipe_diameter=_field(48, unit=None, text="Ø48"),
            wall_thickness=_field(3, unit="mm", text="Wand 3 mm"),
            bracket_width=_field(28, unit="mm", text="Breite 28 mm"),
            base_thickness=_field(5, unit="mm", text="Grundplatte 5 mm"),
            hole_count=_field(2, text="zwei"),
            hole_diameter=_field(6, unit="mm", text="6 mm Bohrungen"),
            material=_field("steel", text="Stahl"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": [],
    },
    {
        "id": "EG03",
        "prompt": "Make a steel pipe bracket for a 50 pipe, with a 4 mm wall, 30 mm width, 6 mm base and two 7 mm holes.",
        "guard_targets": ["pipe_diameter"],
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="pipe bracket"),
            pipe_diameter=_field(50, unit=None, text="50 pipe"),
            wall_thickness=_field(4, unit="mm", text="4 mm wall"),
            bracket_width=_field(30, unit="mm", text="30 mm width"),
            base_thickness=_field(6, unit="mm", text="6 mm base"),
            hole_count=_field(2, text="two"),
            hole_diameter=_field(7, unit="mm", text="7 mm holes"),
            material=_field("steel", text="steel"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": [],
    },
    {
        "id": "EG04",
        "prompt": "Steel bracket for a 50 mm pipe, wall 4 mm, bracket width 30, base 6 mm and two 6.5 mm holes.",
        "guard_targets": ["bracket_width"],
        "parsed_intent": _intent(
            component=_field("bracket", text="bracket"),
            pipe_diameter=_field(50, unit="mm", text="50 mm pipe"),
            wall_thickness=_field(4, unit="mm", text="wall 4 mm"),
            bracket_width=_field(30, unit=None, text="bracket width 30"),
            base_thickness=_field(6, unit="mm", text="base 6 mm"),
            hole_count=_field(2, text="two"),
            hole_diameter=_field(6.5, unit="mm", text="6.5 mm holes"),
            material=_field("steel", text="Steel"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": [],
    },
    {
        "id": "EG05",
        "prompt": "Aluminium pipe bracket: 50 mm pipe, wall 4 mm, width 30 mm, base 6 mm, two holes Ø7.",
        "guard_targets": ["hole_diameter"],
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="pipe bracket"),
            pipe_diameter=_field(50, unit="mm", text="50 mm pipe"),
            wall_thickness=_field(4, unit="mm", text="wall 4 mm"),
            bracket_width=_field(30, unit="mm", text="width 30 mm"),
            base_thickness=_field(6, unit="mm", text="base 6 mm"),
            hole_count=_field(2, text="two"),
            hole_diameter=_field(7, unit=None, text="Ø7"),
            material=_field("aluminium", text="Aluminium"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": [],
    },
    {
        "id": "EG06",
        "prompt": "Polymer pipe bracket for a 0.05 pipe; wall 4 mm, width 32 mm, base 6 mm, two 6 mm holes.",
        "guard_targets": ["pipe_diameter"],
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="pipe bracket"),
            pipe_diameter=_field(0.05, unit=None, text="0.05 pipe"),
            wall_thickness=_field(4, unit="mm", text="wall 4 mm"),
            bracket_width=_field(32, unit="mm", text="width 32 mm"),
            base_thickness=_field(6, unit="mm", text="base 6 mm"),
            hole_count=_field(2, text="two"),
            hole_diameter=_field(6, unit="mm", text="6 mm holes"),
            material=_field("polymer", text="Polymer"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": [],
    },
    {
        "id": "EG07",
        "prompt": "Steel pipe bracket for a 42 mm pipe; wall 4 mm, width 30 mm, base 6 mm, two 6.6 mm holes.",
        "guard_targets": [],
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="pipe bracket"),
            pipe_diameter=_field(42, unit="mm", text="42 mm pipe"),
            wall_thickness=_field(4, unit="mm", text="wall 4 mm"),
            bracket_width=_field(30, unit="mm", text="width 30 mm"),
            base_thickness=_field(6, unit="mm", text="base 6 mm"),
            hole_count=_field(2, text="two"),
            hole_diameter=_field(6.6, unit="mm", text="6.6 mm holes"),
            material=_field("steel", text="Steel"),
        ),
        "expected_status": "ready",
        "expected_stage": "ready",
        "forbidden_inferences": [],
    },
    {
        "id": "EG08",
        "prompt": "Aluminium pipe bracket for a 0.05 m pipe; wall 0.4 cm, width 30 mm, base 0.006 m, two 0.7 cm holes.",
        "guard_targets": [],
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="pipe bracket"),
            pipe_diameter=_field(0.05, unit="m", text="0.05 m pipe"),
            wall_thickness=_field(0.4, unit="cm", text="wall 0.4 cm"),
            bracket_width=_field(30, unit="mm", text="width 30 mm"),
            base_thickness=_field(0.006, unit="m", text="base 0.006 m"),
            hole_count=_field(2, text="two"),
            hole_diameter=_field(0.7, unit="cm", text="0.7 cm holes"),
            material=_field("aluminium", text="Aluminium"),
        ),
        "expected_status": "ready",
        "expected_stage": "ready",
        "forbidden_inferences": [],
    },
]
