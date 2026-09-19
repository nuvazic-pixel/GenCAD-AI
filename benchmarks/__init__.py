from .cases import BENCHMARK as BENCHMARK_V022
from .cases_v023 import BENCHMARK as BENCHMARK_V023


def get_benchmark(version: str):
    if version == "0.2.2":
        return BENCHMARK_V022
    if version == "0.2.3":
        return BENCHMARK_V023
    raise ValueError(f"Unsupported benchmark version: {version}")


# Current development benchmark. v0.2.2 remains frozen in benchmarks/cases.py.
BENCHMARK = BENCHMARK_V023
