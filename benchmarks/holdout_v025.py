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


HOLDOUT = [
    {
        "id": "H01",
        "prompt": "Design a steel pipe bracket for a 63 mm pipe: 5 mm wall, 36 mm bracket width, 8 mm base, three 7 mm mounting holes.",
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="pipe bracket"),
            pipe_diameter=_field(63, unit="mm", text="63 mm pipe"),
            wall_thickness=_field(5, unit="mm", text="5 mm wall"),
            bracket_width=_field(36, unit="mm", text="36 mm bracket width"),
            base_thickness=_field(8, unit="mm", text="8 mm base"),
            hole_count=_field(3, text="three"),
            hole_diameter=_field(7, unit="mm", text="7 mm mounting holes"),
            material=_field("steel", text="steel"),
        ),
        "expected_status": "ready",
        "expected_stage": "ready",
        "forbidden_inferences": [],
    },
    {
        "id": "H02",
        "prompt": "Aluminiumhalter für ein Rohr Ø 4 cm; Wand 3 mm, Halterbreite 28 mm, Grundplatte 5 mm, zwei Bohrungen Ø 6,5 mm.",
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="Aluminiumhalter"),
            pipe_diameter=_field(4, unit="cm", text="Ø 4 cm"),
            wall_thickness=_field(3, unit="mm", text="Wand 3 mm"),
            bracket_width=_field(28, unit="mm", text="Halterbreite 28 mm"),
            base_thickness=_field(5, unit="mm", text="Grundplatte 5 mm"),
            hole_count=_field(2, text="zwei"),
            hole_diameter=_field("6,5", unit="mm", text="Ø 6,5 mm"),
            material=_field("aluminium", text="Aluminiumhalter"),
        ),
        "expected_status": "ready",
        "expected_stage": "ready",
        "forbidden_inferences": [],
    },
    {
        "id": "H03",
        "prompt": "Need a bracket around a DN40 line, with two M8 clearance holes.",
        "parsed_intent": _intent(
            component=_field("bracket", text="bracket"),
            nominal_pipe_size=_field("DN40", text="DN40"),
            associated_fastener_designation=_field("M8", text="M8 clearance holes"),
            hole_count=_field(2, text="two"),
            hole_semantics=_field("clearance", text="clearance holes"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "terminology_resolution",
        "forbidden_inferences": [
            "pipe_diameter",
            "clearance_hole_diameter",
            "fastener_designation",
        ],
    },
    {
        "id": "H04",
        "prompt": "Create a bracket for a Ø42 pipe with 4 mm wall thickness.",
        "parsed_intent": _intent(
            component=_field("bracket", text="bracket"),
            pipe_diameter=_field(42, unit=None, text="Ø42 pipe"),
            wall_thickness=_field(4, unit="mm", text="4 mm wall thickness"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": [],
    },
    {
        "id": "H05",
        "prompt": "Use three M5 bolts to mount a bracket for a 50 mm pipe.",
        "parsed_intent": _intent(
            component=_field("bracket", text="bracket"),
            pipe_diameter=_field(50, unit="mm", text="50 mm pipe"),
            fastener_designation=_field("M5", text="M5 bolts"),
            fastener_count=_field(3, text="three"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": ["hole_count", "clearance_hole_diameter"],
    },
    {
        "id": "H06",
        "prompt": "Pipe clamp bracket for a 75 mm pipe, with four M8 threaded holes.",
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="Pipe clamp bracket"),
            pipe_diameter=_field(75, unit="mm", text="75 mm pipe"),
            associated_fastener_designation=_field("M8", text="M8 threaded holes"),
            hole_count=_field(4, text="four"),
            hole_semantics=_field("threaded", text="threaded holes"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": ["fastener_designation", "clearance_hole_diameter"],
    },
    {
        "id": "H07",
        "prompt": "Make a 60 mm pipe bracket, probably aluminium, with a 4 mm wall.",
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="pipe bracket"),
            pipe_diameter=_field(60, unit="mm", text="60 mm"),
            wall_thickness=_field(4, unit="mm", text="4 mm wall"),
            material=_field(
                "aluminium",
                text="probably aluminium",
                state="hypothesis",
                confidence=0.7,
            ),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": ["confirmed_material"],
    },
    {
        "id": "H08",
        "prompt": "Design a compact, lightweight bracket for a 45 mm pipe.",
        "parsed_intent": _intent(
            component=_field("bracket", text="bracket"),
            pipe_diameter=_field(45, unit="mm", text="45 mm pipe"),
            qualitative_requirements=[
                {
                    "text": "compact",
                    "category": "size",
                    "source_text": "compact",
                    "confidence": 1.0,
                },
                {
                    "text": "lightweight",
                    "category": "weight",
                    "source_text": "lightweight",
                    "confidence": 1.0,
                },
            ],
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": ["load_statement", "material"],
    },
    {
        "id": "H09",
        "prompt": "Bracket for a 50 mm pipe, rated for 1.2 kN.",
        "parsed_intent": _intent(
            component=_field("bracket", text="Bracket"),
            pipe_diameter=_field(50, unit="mm", text="50 mm pipe"),
            load_statement=_field(1.2, unit="kN", text="rated for 1.2 kN"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": ["force_newton", "safety_factor"],
    },
    {
        "id": "H10",
        "prompt": "Aluminium pipe bracket: 50 mm pipe, 4 mm wall, 30 mm wide, 6 mm base, two M6 clearance holes, each 6.6 mm diameter.",
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="pipe bracket"),
            pipe_diameter=_field(50, unit="mm", text="50 mm pipe"),
            wall_thickness=_field(4, unit="mm", text="4 mm wall"),
            bracket_width=_field(30, unit="mm", text="30 mm wide"),
            base_thickness=_field(6, unit="mm", text="6 mm base"),
            associated_fastener_designation=_field("M6", text="M6 clearance holes"),
            hole_count=_field(2, text="two"),
            hole_diameter=_field(6.6, unit="mm", text="6.6 mm diameter"),
            hole_semantics=_field("clearance", text="clearance holes"),
            material=_field("aluminium", text="Aluminium"),
        ),
        "expected_status": "ready",
        "expected_stage": "ready",
        "forbidden_inferences": ["fastener_designation"],
    },
    {
        "id": "H11",
        "prompt": "Stahl-Rohrhalter: Rohrdurchmesser 80 mm, Wandstärke 5 mm, Breite 42 mm, Grundplatte 8 mm, drei Bohrungen mit 9 mm Durchmesser.",
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="Stahl-Rohrhalter"),
            pipe_diameter=_field(80, unit="mm", text="Rohrdurchmesser 80 mm"),
            wall_thickness=_field(5, unit="mm", text="Wandstärke 5 mm"),
            bracket_width=_field(42, unit="mm", text="Breite 42 mm"),
            base_thickness=_field(8, unit="mm", text="Grundplatte 8 mm"),
            hole_count=_field(3, text="drei"),
            hole_diameter=_field(9, unit="mm", text="9 mm Durchmesser"),
            material=_field("steel", text="Stahl"),
        ),
        "expected_status": "ready",
        "expected_stage": "ready",
        "forbidden_inferences": [],
    },
    {
        "id": "H12",
        "prompt": "Polymer pipe bracket for a 30 mm pipe, wall thickness 16 mm, width 25 mm, base 5 mm, two 5 mm holes.",
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="pipe bracket"),
            pipe_diameter=_field(30, unit="mm", text="30 mm pipe"),
            wall_thickness=_field(16, unit="mm", text="wall thickness 16 mm"),
            bracket_width=_field(25, unit="mm", text="width 25 mm"),
            base_thickness=_field(5, unit="mm", text="base 5 mm"),
            hole_count=_field(2, text="two"),
            hole_diameter=_field(5, unit="mm", text="5 mm holes"),
            material=_field("polymer", text="Polymer"),
        ),
        "expected_status": "rejected",
        "expected_stage": "engineering_validation",
        "forbidden_inferences": [],
    },
    {
        "id": "H13",
        "prompt": "Create a bracket for a 50 mm pipe. Do not assume the material or hole sizes.",
        "parsed_intent": _intent(
            component=_field("bracket", text="bracket"),
            pipe_diameter=_field(50, unit="mm", text="50 mm pipe"),
        ),
        "expected_status": "needs_clarification",
        "expected_stage": "readiness_validation",
        "forbidden_inferences": ["material", "clearance_hole_diameter"],
    },
    {
        "id": "H14",
        "prompt": "Steel pipe bracket for a 0.05 m pipe, 0.4 cm wall, 32 mm width, 6 mm base, two 0.7 cm mounting holes.",
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="pipe bracket"),
            pipe_diameter=_field(0.05, unit="m", text="0.05 m pipe"),
            wall_thickness=_field(0.4, unit="cm", text="0.4 cm wall"),
            bracket_width=_field(32, unit="mm", text="32 mm width"),
            base_thickness=_field(6, unit="mm", text="6 mm base"),
            hole_count=_field(2, text="two"),
            hole_diameter=_field(0.7, unit="cm", text="0.7 cm mounting holes"),
            material=_field("steel", text="Steel"),
        ),
        "expected_status": "ready",
        "expected_stage": "ready",
        "forbidden_inferences": [],
    },
    {
        "id": "H15",
        "prompt": "For a 50 mm aluminium pipe bracket: wall 4 mm, width 30 mm, base 6 mm. Mount it with two M6 screws through two 6.6 mm clearance holes.",
        "parsed_intent": _intent(
            component=_field("pipe_bracket", text="pipe bracket"),
            pipe_diameter=_field(50, unit="mm", text="50 mm"),
            wall_thickness=_field(4, unit="mm", text="wall 4 mm"),
            bracket_width=_field(30, unit="mm", text="width 30 mm"),
            base_thickness=_field(6, unit="mm", text="base 6 mm"),
            fastener_designation=_field("M6", text="M6 screws"),
            fastener_count=_field(2, text="two M6 screws"),
            hole_count=_field(2, text="two 6.6 mm clearance holes"),
            hole_diameter=_field(6.6, unit="mm", text="6.6 mm clearance holes"),
            hole_semantics=_field("clearance", text="clearance holes"),
            material=_field("aluminium", text="aluminium"),
        ),
        "expected_status": "ready",
        "expected_stage": "ready",
        "forbidden_inferences": [],
    },
]
