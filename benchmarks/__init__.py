from .cases import BENCHMARK as BENCHMARK_V022
from .cases_v023 import BENCHMARK as BENCHMARK_V023
from .cases_v024 import BENCHMARK as BENCHMARK_V024
from .holdout_v025 import HOLDOUT as HOLDOUT_V025
from .holdout_v026 import HOLDOUT as HOLDOUT_V026
from .evidence_guard_challenge_v027 import CHALLENGE as EVIDENCE_GUARD_CHALLENGE_V027


def get_benchmark(version: str):
    if version == "0.2.2":
        return BENCHMARK_V022
    if version == "0.2.3":
        return BENCHMARK_V023
    if version == "0.2.4":
        return BENCHMARK_V024
    if version == "0.2.5-holdout":
        return HOLDOUT_V025
    if version == "0.2.6-holdout2":
        return HOLDOUT_V026
    if version == "0.2.7-evidence-guard":
        return EVIDENCE_GUARD_CHALLENGE_V027
    raise ValueError(f"Unsupported benchmark version: {version}")


# Current development benchmark. Prior benchmark versions remain frozen.
BENCHMARK = BENCHMARK_V024
