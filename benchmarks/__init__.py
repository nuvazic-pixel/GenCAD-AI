from .cases import BENCHMARK as BENCHMARK_V022
from .cases_v023 import BENCHMARK as BENCHMARK_V023
from .cases_v024 import BENCHMARK as BENCHMARK_V024


def get_benchmark(version: str):
    if version == "0.2.2":
        return BENCHMARK_V022
    if version == "0.2.3":
        return BENCHMARK_V023
    if version == "0.2.4":
        return BENCHMARK_V024
    raise ValueError(f"Unsupported benchmark version: {version}")


# Current development benchmark. Prior benchmark versions remain frozen.
BENCHMARK = BENCHMARK_V024
