from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import platform
from typing import Any

from pydantic import BaseModel


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def _hash(value: Any) -> str:
    payload = value if isinstance(value, str) else _canonical_json(value)
    return sha256(payload.encode("utf-8")).hexdigest()


class ExperimentFingerprint(BaseModel):
    run_id: str
    provider: str
    model: str
    prompt_version: str
    benchmark_version: str
    schema_version: str
    git_commit: str | None = None
    prompt_hash: str
    benchmark_hash: str
    schema_hash: str
    fingerprint_id: str
    python_version: str
    created_at_utc: str


def create_fingerprint(
    *,
    run_id: str,
    provider: str,
    model: str,
    prompt_version: str,
    benchmark_version: str,
    schema_version: str,
    prompt: str,
    benchmark: Any,
    schema: Any,
    git_commit: str | None = None,
) -> ExperimentFingerprint:
    identity = {
        "run_id": run_id,
        "provider": provider,
        "model": model,
        "prompt_version": prompt_version,
        "benchmark_version": benchmark_version,
        "schema_version": schema_version,
        "git_commit": git_commit,
        "prompt_hash": _hash(prompt),
        "benchmark_hash": _hash(benchmark),
        "schema_hash": _hash(schema),
    }

    return ExperimentFingerprint(
        **identity,
        fingerprint_id=_hash(identity),
        python_version=platform.python_version(),
        created_at_utc=datetime.now(timezone.utc).isoformat(),
    )
