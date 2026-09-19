FIELDS = [
    "component", "pipe_diameter", "nominal_pipe_size", "wall_thickness",
    "bracket_width", "base_thickness", "fastener_designation", "fastener_count",
    "hole_diameter", "hole_semantics", "material", "manufacturing_process",
    "load_statement",
]

UNKNOWN = {
    "raw_value": None, "raw_unit": None, "source_text": None,
    "state": "unknown", "confidence": 0.0,
}

def field(value=None, unit=None, text=None, state="confirmed", confidence=1.0):
    if state == "unknown":
        return dict(UNKNOWN)
    return {
        "raw_value": value, "raw_unit": unit, "source_text": text,
        "state": state, "confidence": confidence,
    }

def intent(**overrides):
    data = {name: dict(UNKNOWN) for name in FIELDS}
    data.update(overrides)
    return data

BENCHMARK = [
    {
        'id': 'B01',
        'prompt': 'Create a bracket for a 50 mm pipe.',
        'parsed_intent': intent(
            component=field('bracket', text='bracket'),
            pipe_diameter=field(50, unit='mm', text='50 mm pipe'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['material', 'wall_thickness', 'fastener_designation'],
    },
    {
        'id': 'B02',
        'prompt': 'Create a bracket for a Ø50 pipe with two M6 holes.',
        'parsed_intent': intent(
            component=field('bracket', text='bracket'),
            pipe_diameter=field(50, unit='mm', text='Ø50 pipe'),
            fastener_designation=field('M6', text='M6'),
            fastener_count=field(2, text='two'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['clearance_hole_diameter', 'material'],
    },
    {
        'id': 'B03',
        'prompt': 'Create a bracket for a 5 cm pipe.',
        'parsed_intent': intent(
            component=field('bracket', text='bracket'),
            pipe_diameter=field(5, unit='cm', text='5 cm pipe'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'expected_normalized': {'pipe_diameter_mm': 50.0},
        'forbidden_inferences': ['material'],
    },
    {
        'id': 'B04',
        'prompt': 'Create a bracket for a 0.05 m pipe.',
        'parsed_intent': intent(
            component=field('bracket', text='bracket'),
            pipe_diameter=field(0.05, unit='m', text='0.05 m pipe'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'expected_normalized': {'pipe_diameter_mm': 50.0},
        'forbidden_inferences': ['material'],
    },
    {
        'id': 'B05',
        'prompt': 'Bracket für ein 50 mm Rohr mit zwei M6 Bohrungen.',
        'parsed_intent': intent(
            component=field('bracket', text='Bracket'),
            pipe_diameter=field(50, unit='mm', text='50 mm Rohr'),
            fastener_designation=field('M6', text='M6'),
            fastener_count=field(2, text='zwei'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['clearance_hole_diameter'],
    },
    {
        'id': 'B06',
        'prompt': 'Create a bracket for DN50.',
        'parsed_intent': intent(
            component=field('bracket', text='bracket'),
            nominal_pipe_size=field('DN50', text='DN50'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'terminology_resolution',
        'forbidden_inferences': ['pipe_diameter'],
    },
    {
        'id': 'B07',
        'prompt': 'Strong bracket for a pipe.',
        'parsed_intent': intent(
            component=field('bracket', text='bracket'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['pipe_diameter', 'material', 'load_statement'],
    },
    {
        'id': 'B08',
        'prompt': 'Aluminium bracket for a 50 mm pipe.',
        'parsed_intent': intent(
            component=field('bracket', text='bracket'),
            pipe_diameter=field(50, unit='mm', text='50 mm pipe'),
            material=field('aluminium', text='Aluminium'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['wall_thickness', 'manufacturing_process'],
    },
    {
        'id': 'B09',
        'prompt': '50 mm pipe, probably aluminium.',
        'parsed_intent': intent(
            pipe_diameter=field(50, unit='mm', text='50 mm pipe'),
            material=field('aluminium', text='probably aluminium', state='hypothesis', confidence=0.55),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['confirmed_material'],
    },
    {
        'id': 'B10',
        'prompt': '50 mm pipe with maybe two M6 screws.',
        'parsed_intent': intent(
            pipe_diameter=field(50, unit='mm', text='50 mm pipe'),
            fastener_designation=field('M6', text='maybe two M6 screws', state='hypothesis', confidence=0.55),
            fastener_count=field(2, text='maybe two', state='hypothesis', confidence=0.55),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['confirmed_fastener'],
    },
    {
        'id': 'B11',
        'prompt': '50 mm pipe, 4 mm wall, two M6 holes.',
        'parsed_intent': intent(
            pipe_diameter=field(50, unit='mm', text='50 mm pipe'),
            wall_thickness=field(4, unit='mm', text='4 mm wall'),
            fastener_designation=field('M6', text='M6'),
            fastener_count=field(2, text='two'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['bracket_width', 'base_thickness', 'material'],
    },
    {
        'id': 'B12',
        'prompt': '50 mm pipe, wall thickness 40 mm.',
        'parsed_intent': intent(
            pipe_diameter=field(50, unit='mm', text='50 mm pipe'),
            wall_thickness=field(40, unit='mm', text='wall thickness 40 mm'),
        ),
        'expected_status': 'rejected',
        'expected_stage': 'engineering_validation',
        'forbidden_inferences': [],
    },
    {
        'id': 'B13',
        'prompt': 'Pipe diameter fifty millimetres.',
        'parsed_intent': intent(
            pipe_diameter=field(50, unit='mm', text='fifty millimetres'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['material', 'fastener_designation'],
    },
    {
        'id': 'B14',
        'prompt': 'Use M6 clearance holes.',
        'parsed_intent': intent(
            fastener_designation=field('M6', text='M6'),
            hole_semantics=field('clearance', text='clearance holes'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['clearance_hole_diameter'],
    },
    {
        'id': 'B15',
        'prompt': 'Use two 6.6 mm holes.',
        'parsed_intent': intent(
            fastener_count=field(2, text='two'),
            hole_diameter=field(6.6, unit='mm', text='6.6 mm holes'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['fastener_designation'],
    },
    {
        'id': 'B16',
        'prompt': 'Two M6 threaded holes.',
        'parsed_intent': intent(
            fastener_designation=field('M6', text='M6'),
            fastener_count=field(2, text='Two'),
            hole_semantics=field('threaded', text='threaded holes'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['clearance_hole_diameter'],
    },
    {
        'id': 'B17',
        'prompt': '50mm pipe, 30mm bracket width, 6mm base.',
        'parsed_intent': intent(
            pipe_diameter=field(50, unit='mm', text='50mm pipe'),
            bracket_width=field(30, unit='mm', text='30mm bracket width'),
            base_thickness=field(6, unit='mm', text='6mm base'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['wall_thickness'],
    },
    {
        'id': 'B18',
        'prompt': 'Steel bracket.',
        'parsed_intent': intent(
            component=field('bracket', text='bracket'),
            material=field('steel', text='Steel'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['steel_grade'],
    },
    {
        'id': 'B19',
        'prompt': 'Make it suitable for 100 kg.',
        'parsed_intent': intent(
            load_statement=field('100 kg', text='100 kg'),
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['force_newton', 'safety_factor'],
    },
    {
        'id': 'B20',
        'prompt': 'Use something lightweight and strong.',
        'parsed_intent': intent(
        ),
        'expected_status': 'needs_clarification',
        'expected_stage': 'readiness_validation',
        'forbidden_inferences': ['material', 'alloy', 'geometry'],
    },
    {
        'id': 'P01',
        'prompt': 'Create an aluminium pipe bracket for a 50 mm pipe, 4 mm wall thickness, 30 mm bracket width, 6 mm base thickness and two M6 mounting holes. Use 6.6 mm clearance holes.',
        'parsed_intent': intent(
            component=field('pipe_bracket', text='pipe bracket'),
            pipe_diameter=field(50, unit='mm', text='50 mm pipe'),
            wall_thickness=field(4, unit='mm', text='4 mm wall thickness'),
            bracket_width=field(30, unit='mm', text='30 mm bracket width'),
            base_thickness=field(6, unit='mm', text='6 mm base thickness'),
            fastener_designation=field('M6', text='M6'),
            fastener_count=field(2, text='two'),
            hole_diameter=field(6.6, unit='mm', text='6.6 mm clearance holes'),
            hole_semantics=field('clearance', text='clearance holes'),
            material=field('aluminium', text='aluminium'),
        ),
        'expected_status': 'ready',
        'expected_stage': 'ready',
        'forbidden_inferences': [],
    },
    {
        'id': 'P02',
        'prompt': 'Steel pipe bracket: pipe diameter 80 mm, wall thickness 5 mm, bracket width 40 mm, base thickness 8 mm, two M8 mounting holes, 9 mm clearance-hole diameter.',
        'parsed_intent': intent(
            component=field('pipe_bracket', text='pipe bracket'),
            pipe_diameter=field(80, unit='mm', text='pipe diameter 80 mm'),
            wall_thickness=field(5, unit='mm', text='wall thickness 5 mm'),
            bracket_width=field(40, unit='mm', text='bracket width 40 mm'),
            base_thickness=field(8, unit='mm', text='base thickness 8 mm'),
            fastener_designation=field('M8', text='M8'),
            fastener_count=field(2, text='two'),
            hole_diameter=field(9, unit='mm', text='9 mm clearance-hole diameter'),
            hole_semantics=field('clearance', text='clearance-hole'),
            material=field('steel', text='Steel'),
        ),
        'expected_status': 'ready',
        'expected_stage': 'ready',
        'forbidden_inferences': [],
    },
    {
        'id': 'P03',
        'prompt': 'Create a polymer pipe bracket for a 4 cm pipe. Wall thickness 3 mm, bracket width 35 mm, base thickness 7 mm, two M6 holes, hole diameter 6.6 mm.',
        'parsed_intent': intent(
            component=field('pipe_bracket', text='pipe bracket'),
            pipe_diameter=field(4, unit='cm', text='4 cm pipe'),
            wall_thickness=field(3, unit='mm', text='Wall thickness 3 mm'),
            bracket_width=field(35, unit='mm', text='bracket width 35 mm'),
            base_thickness=field(7, unit='mm', text='base thickness 7 mm'),
            fastener_designation=field('M6', text='M6'),
            fastener_count=field(2, text='two'),
            hole_diameter=field(6.6, unit='mm', text='hole diameter 6.6 mm'),
            material=field('polymer', text='polymer'),
        ),
        'expected_status': 'ready',
        'expected_stage': 'ready',
        'forbidden_inferences': [],
    },
    {
        'id': 'P04',
        'prompt': 'Aluminium wall bracket for a 0.06 m pipe: wall thickness 4 mm, width 32 mm, base thickness 6 mm, two M6 mounting holes, 6.6 mm hole diameter.',
        'parsed_intent': intent(
            component=field('wall bracket', text='wall bracket'),
            pipe_diameter=field(0.06, unit='m', text='0.06 m pipe'),
            wall_thickness=field(4, unit='mm', text='wall thickness 4 mm'),
            bracket_width=field(32, unit='mm', text='width 32 mm'),
            base_thickness=field(6, unit='mm', text='base thickness 6 mm'),
            fastener_designation=field('M6', text='M6'),
            fastener_count=field(2, text='two'),
            hole_diameter=field(6.6, unit='mm', text='6.6 mm hole diameter'),
            material=field('aluminium', text='Aluminium'),
        ),
        'expected_status': 'ready',
        'expected_stage': 'ready',
        'forbidden_inferences': [],
    },
    {
        'id': 'P05',
        'prompt': 'Bracket für ein 50 mm Rohr: Aluminium, Wandstärke 4 mm, Breite 30 mm, Grundplatte 6 mm, zwei M6 Befestigungsbohrungen mit 6,6 mm Durchmesser.',
        'parsed_intent': intent(
            component=field('bracket', text='Bracket'),
            pipe_diameter=field(50, unit='mm', text='50 mm Rohr'),
            wall_thickness=field(4, unit='mm', text='Wandstärke 4 mm'),
            bracket_width=field(30, unit='mm', text='Breite 30 mm'),
            base_thickness=field(6, unit='mm', text='Grundplatte 6 mm'),
            fastener_designation=field('M6', text='M6'),
            fastener_count=field(2, text='zwei'),
            hole_diameter=field(6.6, unit='mm', text='6,6 mm Durchmesser'),
            material=field('aluminium', text='Aluminium'),
        ),
        'expected_status': 'ready',
        'expected_stage': 'ready',
        'forbidden_inferences': [],
    },
]
